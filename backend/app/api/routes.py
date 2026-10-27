from __future__ import annotations
import logging
import uuid
from typing import Optional, List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
import io

from app.schemas.schemas import (
    AnalyzeRequest, AnalyzeResponse, HealthResponse, CompareRequest,
    CompareResultItem, AskRequest, AskResponse,
)
from app.services.pipeline_service import analyze_review
from app.services.sentiment_service import get_sentiment_service
from app.services.cxscore_service import compute_cx_score
from app.services import dashboard_service, gemini_service, insight_service, ask_service, repository
from app.utils.file_utils import load_dataframe, detect_review_column, FileParsingError
from app.config import settings
from app.db import db_available
from app.auth import get_current_user_optional, require_user

logger = logging.getLogger("cxiq")
router = APIRouter()


def _assert_dataset_access(dataset_id: str, current_user: Optional[dict]) -> None:
    """Ownership guard shared by every endpoint that reads back a
    previously-analyzed dataset (dashboard, preview, CSV download, Ask
    CXIQ). SECURITY: never trust a user_id from the frontend/request body —
    the only identity used here is whatever `get_current_user_optional`
    resolved from the verified Clerk session token on THIS request.

    - If the database isn't configured, or the dataset has no owner
      (guest upload, or the shared bundled "sample" dataset), access is
      unrestricted — this preserves the app's existing guest-mode behavior
      exactly as it worked before this feature.
    - If the dataset DOES have an owner, the requester must be signed in
      as that exact owner, or this raises 404 (not 403) so a dataset's
      existence/ownership can't be probed by an unauthenticated or
      wrong-account request.
    """
    if not db_available():
        return
    meta = repository.get_dataset_meta(dataset_id)
    if not meta or meta.get("user_id") is None:
        return
    if not current_user:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    requester_id = repository.get_or_create_user(current_user["clerk_user_id"], current_user.get("email"))
    if requester_id != meta["user_id"]:
        raise HTTPException(status_code=404, detail="Dataset not found.")


@router.get("/health", response_model=HealthResponse)
def health():
    sentiment_ready = get_sentiment_service().is_ready()
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        models_loaded={
            "sentiment_tfidf_logreg": sentiment_ready,
            "gemini_configured": gemini_service.is_configured(),
            "database_connected": db_available(),
            "auth_configured": settings.AUTH_ENABLED,
        },
    )


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest):
    if len(payload.text) > settings.MAX_TEXT_LENGTH:
        raise HTTPException(status_code=422, detail=f"Feedback text exceeds the {settings.MAX_TEXT_LENGTH} character limit.")
    try:
        result = analyze_review(payload.text, domain=payload.domain, rating=payload.rating)
    except Exception as exc:
        logger.exception("Analysis failed")
        raise HTTPException(status_code=500, detail="Something went wrong while analyzing this feedback. Please try again.")

    # optional Gemini enrichment (falls back to rule-based insight automatically)
    structured_input = {
        "overall_sentiment": result["overall_sentiment"]["label"],
        "confidence": result["overall_sentiment"]["confidence"],
        "aspects": [{"aspect": a["aspect"], "sentiment": a["sentiment"]} for a in result["aspects"]],
        "emotion": result["emotion"]["label"],
        "priority": result["priority"]["label"],
    }
    gemini_out = gemini_service.generate_business_summary(
        structured_input,
        fallback={"business_insight": result["business_insight"], "recommendations": result["recommendations"]},
    )

    return AnalyzeResponse(
        text=result["text"],
        original_text=result["original_text"],
        detected_language=result["detected_language"],
        language_code=result["language_code"],
        is_code_mixed=result["is_code_mixed"],
        translated_text=result["translated_text"],
        translation_status=result["translation_status"],
        reliable=result["reliable"],
        domain=result["domain"],
        overall_sentiment=result["overall_sentiment"],
        aspects=result["aspects"],
        emotion=result["emotion"],
        priority=result["priority"],
        explanation=result["explanation"],
        business_insight=gemini_out.get("business_insight", result["business_insight"]),
        recommendations=gemini_out.get("recommendations", result["recommendations"]),
        customer_experience_score=None,
    )


@router.post("/analyze/compare", response_model=List[CompareResultItem])
def analyze_compare(payload: CompareRequest):
    """Cross-Language Analysis: analyze the same (or similar) feedback
    entered in different languages side by side, so a manager can see that
    CXIQ understands customer experience consistently across markets."""
    results = []
    for entry in payload.entries:
        try:
            r = analyze_review(entry.text, domain=payload.domain)
        except Exception:
            logger.exception("Compare-languages analysis failed for one entry")
            raise HTTPException(status_code=500, detail="Something went wrong analyzing one of the entries.")

        main_aspect = r["aspects"][0]["aspect"] if r["aspects"] else None
        # A lightweight, indicative CX score for this single entry, used only
        # to make the comparison table meaningful — not the same as the
        # dataset-level CX Score shown on the Dashboard.
        cx = compute_cx_score(
            sentiment_counts={r["overall_sentiment"]["label"]: 1},
            aspect_sentiment_counts={a["sentiment"]: 1 for a in r["aspects"]} if r["aspects"] else {},
            priority_counts={r["priority"]["label"]: 1},
        )
        results.append(CompareResultItem(
            label=entry.label,
            original_text=r["original_text"],
            detected_language=r["detected_language"],
            translated_text=r["translated_text"],
            translation_status=r["translation_status"],
            overall_sentiment=r["overall_sentiment"]["label"],
            confidence=r["overall_sentiment"]["confidence"],
            emotion=r["emotion"]["label"],
            priority=r["priority"]["label"],
            main_aspect=main_aspect,
            cx_score=cx["score"],
        ))
    return results


@router.post("/analyze/batch")
async def analyze_batch(
    file: UploadFile = File(...),
    domain: str = Form("other"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=422, detail="The uploaded file is empty.")
    try:
        df = load_dataframe(file.filename, content)
    except FileParsingError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    review_column = detect_review_column(df)
    if not review_column:
        raise HTTPException(
            status_code=422,
            detail="Could not detect a review/feedback text column. Please include a column named "
                   "'review', 'text', 'review_text', 'feedback', or 'comment'.",
        )

    if len(df) > settings.MAX_BATCH_ROWS:
        raise HTTPException(status_code=422, detail=f"Dataset exceeds the maximum of {settings.MAX_BATCH_ROWS} rows.")

    # Tie this upload to a signed-in user when a valid Clerk session was
    # provided and a database is available; guests (or no database) still
    # get full functionality, they just won't see it in a personal list.
    user_id = None
    if current_user and db_available():
        user_id = repository.get_or_create_user(current_user["clerk_user_id"], current_user.get("email"))

    try:
        summary = dashboard_service.process_batch(
            df, review_column, domain=domain, filename=file.filename, user_id=user_id,
        )
    except Exception:
        logger.exception("Batch analysis failed")
        raise HTTPException(status_code=500, detail="Something went wrong while analyzing the dataset.")

    return summary


@router.get("/datasets")
def list_my_datasets(current_user: dict = Depends(require_user)):
    """Returns the signed-in user's previously uploaded datasets. Requires
    both a signed-in Clerk session AND a configured database — if either is
    missing, this endpoint simply isn't useful (nothing would be tied to an
    account), so it returns a clear message rather than a confusing 401."""
    if not db_available():
        raise HTTPException(status_code=503, detail="Dataset history requires a configured database.")
    user_id = repository.get_or_create_user(current_user["clerk_user_id"], current_user.get("email"))
    return {"datasets": repository.list_datasets_for_user(user_id)}


@router.get("/datasets/my")
def list_my_datasets_v2(current_user: dict = Depends(require_user)):
    """"My Datasets" page — identical to GET /api/datasets, kept as its own
    path to match the feature's documented API surface. The authenticated
    user's identity comes ONLY from the verified Clerk session token (see
    app/auth.py); nothing from the request body/query is trusted for this."""
    return list_my_datasets(current_user)


@router.get("/datasets/{dataset_id}")
def get_dataset_detail(dataset_id: str, current_user: dict = Depends(require_user)):
    """Metadata for a single previously-analyzed dataset — used by "My
    Datasets" cards. Returns 404 (not 403) for a dataset that exists but
    belongs to someone else, so ownership can't be probed."""
    if not db_available():
        raise HTTPException(status_code=503, detail="Dataset history requires a configured database.")
    meta = repository.get_dataset_meta(dataset_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    user_id = repository.get_or_create_user(current_user["clerk_user_id"], current_user.get("email"))
    if meta.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return meta


@router.post("/datasets/sample")
def load_sample_dataset(current_user: dict = Depends(require_user)):
    """"Try Sample Dataset": gives the signed-in user their own private copy
    of the bundled sample dataset, so it shows up in their My Datasets
    history and is isolated from every other account. Idempotent — clicking
    it again reuses the existing copy instead of creating a duplicate."""
    user_id = repository.get_or_create_user(current_user["clerk_user_id"], current_user.get("email"))

    if db_available():
        existing_id = repository.get_user_sample_dataset_id(user_id)
        if existing_id:
            return {"dataset_id": existing_id, "reused": True}

        new_dataset_id = str(uuid.uuid4())
        # Prefer cloning the already-analyzed shared "sample" dataset
        # (preloaded at startup — see main.py) rather than re-running the
        # ML/translation pipeline over ~650 rows again for every account.
        cloned = repository.clone_dataset_for_user(
            source_dataset_id=dashboard_service.DEFAULT_DATASET_ID,
            new_dataset_id=new_dataset_id,
            user_id=user_id,
            filename="sample_customer_reviews.csv",
            is_sample=True,
        )
        if cloned:
            return {"dataset_id": new_dataset_id, "reused": False}

        # The shared sample dataset hasn't been preloaded (e.g. very first
        # startup ran before the CSV existed) — analyze it fresh instead.
        df, review_col = dashboard_service.load_sample_dataframe()
        if df is None or not review_col:
            raise HTTPException(status_code=503, detail="The sample dataset is not available on this server.")
        summary = dashboard_service.process_batch(
            df, review_col, domain="other", dataset_id=new_dataset_id,
            filename="sample_customer_reviews.csv", user_id=user_id, is_sample=True,
        )
        return {"dataset_id": summary["dataset_id"], "reused": False}

    # No database configured: nothing to persist/isolate per account, so
    # just hand back the same guest-mode sample dataset id CXIQ has always
    # used (unchanged behavior for a no-database deployment).
    return {"dataset_id": dashboard_service.DEFAULT_DATASET_ID, "reused": True}


@router.get("/analyze/batch/{dataset_id}/preview")
def batch_preview(
    dataset_id: str, rows: int = Query(10, le=100),
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    _assert_dataset_access(dataset_id, current_user)
    dataset = dashboard_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found. It may have expired after a backend restart.")
    return {"rows": dataset["rows"][:rows], "total": len(dataset["rows"])}


@router.post("/analyze/batch/{dataset_id}/retry-failed")
def retry_failed_translations(dataset_id: str, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Re-attempts translation + analysis ONLY for the reviews in this
    dataset that couldn't be reliably analyzed the first time (translation
    failure), and updates their stored results in place. Reviews that were
    already reliably analyzed are left untouched. Unlike a dashboard
    refresh (GET /dashboard, which just re-reads whatever is already
    stored), this endpoint actually re-runs translation for the affected
    rows."""
    _assert_dataset_access(dataset_id, current_user)
    summary = dashboard_service.retry_failed_translations(dataset_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Dataset not found. It may have expired after a backend restart.")
    return summary


@router.get("/analyze/batch/{dataset_id}/download")
def download_results(dataset_id: str, current_user: Optional[dict] = Depends(get_current_user_optional)):
    _assert_dataset_access(dataset_id, current_user)
    csv_bytes = dashboard_service.export_csv(dataset_id)
    if csv_bytes is None:
        raise HTTPException(status_code=404, detail="Dataset not found. It may have expired after a backend restart.")
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=cxiq_results_{dataset_id[:8]}.csv"},
    )


@router.get("/dashboard")
def dashboard(
    dataset_id: str = Query(dashboard_service.DEFAULT_DATASET_ID), language: Optional[str] = Query(None),
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    _assert_dataset_access(dataset_id, current_user)
    result = dashboard_service.build_dashboard(dataset_id, language=language)
    if result is None:
        raise HTTPException(status_code=404, detail="Dataset not found. Upload a dataset first, or use the sample dataset.")
    return result


@router.post("/dashboard/ask", response_model=AskResponse)
def dashboard_ask(payload: AskRequest, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Ask CXIQ: answers a natural-language question grounded entirely in
    the already-computed dashboard statistics for this dataset."""
    _assert_dataset_access(payload.dataset_id, current_user)
    dashboard_data = dashboard_service.build_dashboard(payload.dataset_id)
    if dashboard_data is None:
        raise HTTPException(status_code=404, detail="Dataset not found. Upload a dataset first, or use the sample dataset.")
    if dashboard_data.get("total_reviews", 0) == 0:
        raise HTTPException(status_code=422, detail="This dataset has no analyzed reviews yet.")
    try:
        result = ask_service.answer_question(payload.question, dashboard_data)
    except Exception:
        logger.exception("Ask CXIQ failed")
        raise HTTPException(status_code=500, detail="Something went wrong answering that question. Please try again.")
    return AskResponse(answer=result["answer"], source=result["source"])
