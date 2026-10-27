from __future__ import annotations
import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.routes import router
from app.services import dashboard_service, repository
from app.services.sentiment_service import get_sentiment_service
from app.utils.file_utils import load_dataframe, detect_review_column
from app.db import check_db_connection, db_available

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cxiq")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_CSV_PATH = os.path.join(BASE_DIR, "data", "sample_customer_reviews.csv")

app = FastAPI(
    title="CXIQ API",
    description="AI-Driven Customer Experience Intelligence and Decision Support System",
    version=settings.VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url)
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred. Please try again."})


@app.on_event("startup")
def on_startup():
    logger.info("Checking database connection...")
    if check_db_connection():
        logger.info("Running with PostgreSQL-backed storage (datasets persist across restarts).")
    else:
        logger.info("Running with in-memory storage (no database configured/reachable).")

    logger.info("Warming up sentiment model...")
    get_sentiment_service()

    # Skip re-analyzing the sample dataset if it's already persisted from a
    # previous run — a real benefit of the database: 655 rows don't need to
    # be re-run through the NLP pipeline on every restart.
    if db_available() and repository.dataset_exists(dashboard_service.DEFAULT_DATASET_ID):
        logger.info("Sample dataset already present in the database — skipping re-analysis.")
        return

    if os.path.exists(SAMPLE_CSV_PATH):
        try:
            with open(SAMPLE_CSV_PATH, "rb") as f:
                content = f.read()
            df = load_dataframe("sample_customer_reviews.csv", content)
            review_col = detect_review_column(df)
            if review_col:
                logger.info("Preloading sample dataset (%s rows)...", len(df))
                dashboard_service.process_batch(
                    df, review_col, domain="other", dataset_id=dashboard_service.DEFAULT_DATASET_ID,
                    filename="sample_customer_reviews.csv",
                )
                logger.info("Sample dataset ready as dataset_id='%s'.", dashboard_service.DEFAULT_DATASET_ID)
        except Exception:
            logger.exception("Failed to preload sample dataset")


app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {"message": "CXIQ API is running. See /docs for API documentation."}
