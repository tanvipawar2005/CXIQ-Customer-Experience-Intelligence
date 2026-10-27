import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = "CXIQ"
    VERSION: str = "1.0.0"

    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")]

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    # Guards against the .env.example placeholder value being copied as-is
    # and silently treated as a real (but invalid) key.
    GEMINI_ENABLED: bool = bool(GEMINI_API_KEY)

    # Database (optional — see README section 19). If unset or unreachable,
    # CXIQ automatically falls back to in-memory storage, same graceful-
    # degradation pattern used for Gemini and translation. The default below
    # is a generic local-Postgres placeholder (not a real credential) purely
    # so `create_engine()` has a syntactically valid URL to parse when no
    # DATABASE_URL is configured — set your own in `.env` for persistence.
DATABASE_URL: str = os.getenv("DATABASE_URL", "").strip()
    # Clerk authentication (optional — see README section 19). If unset,
    # CXIQ runs entirely in guest mode: every feature works, but uploads
    # aren't tied to a personal account and there's no "My Datasets" list.
    CLERK_PUBLISHABLE_KEY: str = os.getenv("CLERK_PUBLISHABLE_KEY", "")
    CLERK_JWKS_URL: str = os.getenv("CLERK_JWKS_URL", "")  # e.g. https://<your-instance>.clerk.accounts.dev/.well-known/jwks.json
    CLERK_ISSUER: str = os.getenv("CLERK_ISSUER", "")      # e.g. https://<your-instance>.clerk.accounts.dev
    AUTH_ENABLED: bool = bool(CLERK_JWKS_URL and CLERK_ISSUER)

    MAX_TEXT_LENGTH: int = 5000
    MAX_BATCH_ROWS: int = 50000

    # Complaint priority thresholds (0-1 severity score -> label)
    PRIORITY_THRESHOLDS = {
        "critical": 0.75,
        "high": 0.55,
        "medium": 0.30,
    }

    # Customer Experience Score bands (0-100)
    CX_SCORE_BANDS = [
        (80, 100, "Excellent"),
        (65, 79, "Good"),
        (50, 64, "Needs Attention"),
        (0, 49, "Critical"),
    ]

    # Weights used by cxscore_service.compute_cx_score (must sum to 1.0)
    CX_SCORE_WEIGHTS = {
        "sentiment": 0.45,      # share of positive vs negative sentiment
        "aspect_health": 0.25,  # share of aspects that are positive
        "priority_penalty": 0.20,  # penalty from high/critical priority complaints
        "rating": 0.10,         # average star rating, if available
    }

    # Trend detection: minimum number of time buckets required before we
    # attempt emerging-issue detection
    MIN_TIME_BUCKETS_FOR_TREND = 3
    EMERGING_ISSUE_MIN_INCREASE_PP = 8.0  # percentage-point rise to flag as emerging

    # A month with very few reviews produces wildly noisy percentages (one
    # review moving a bucket from 0% to 100% negative). Require at least
    # this many reviews in EVERY month bucket before trusting emerging-
    # issue percentages or a forecast enough to present them as findings.
    MIN_REVIEWS_PER_MONTH_FOR_TREND = 5


settings = Settings()
