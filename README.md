# CXIQ — Customer Experience Intelligence Platform

**AI-Driven Customer Experience Intelligence and Decision Support System using Aspect-Based Sentiment Analysis and Machine Learning**

CXIQ turns unstructured customer feedback into actionable business intelligence. Instead of a single positive/negative label, it identifies *what* customers are talking about (aspects), *how* they feel about each aspect, *what emotion* they're expressing, *how urgent* the issue is, and *what the business should do next* — all explainable, all traceable to real analytical signals.

> This is an MSc Data Analytics project built to feel like a real SaaS analytics product rather than a classroom demo. Every number on the dashboard is calculated from actual analyzed data — nothing is hard-coded or randomly generated.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Features](#2-features)
3. [Architecture](#3-architecture)
4. [Technology Stack](#4-technology-stack)
5. [Folder Structure](#5-folder-structure)
6. [Installation](#6-installation)
7. [Backend Setup](#7-backend-setup)
8. [Frontend Setup](#8-frontend-setup)
9. [Environment Variables](#9-environment-variables)
10. [Gemini API Setup (Optional)](#10-gemini-api-setup-optional)
11. [Running the Application](#11-running-the-application)
12. [Dataset Format](#12-dataset-format)
13. [ML / NLP Pipeline](#13-ml--nlp-pipeline)
14. [API Documentation](#14-api-documentation)
15. [Model Information](#15-model-information)
16. [Limitations](#16-limitations)
17. [Future Improvements](#17-future-improvements)
18. [Multilingual & Advanced Intelligence (v2 Upgrade)](#18-multilingual--advanced-intelligence-v2-upgrade)
19. [Database & Authentication (v3 Upgrade)](#19-database--authentication-v3-upgrade)
20. [Real Trained ABSA Model (v4 Upgrade)](#20-real-trained-absa-model-v4-upgrade)
21. [My Datasets / Analysis History (v5 Upgrade)](#21-my-datasets--analysis-history-v5-upgrade)

---

## 1. Project Overview

CXIQ analyzes customer feedback — single reviews or entire datasets — and produces:

- Overall sentiment (positive / neutral / negative) with confidence
- Aspect-Based Sentiment Analysis (ABSA): multiple aspects per review, each with its own sentiment
- Emotion detection (Joy, Love, Anger, Sadness, Fear, Surprise)
- Complaint/issue priority (Low / Medium / High / Critical), fully explainable
- A transparent, formula-based Customer Experience Score (0–100)
- Trend analysis and emerging-issue detection over time
- AI-generated (or rule-based fallback) business insights and recommended actions

It works out of the box with a bundled sample dataset — no database, no external API key required.

## 2. Features

- **Multilingual CX Intelligence**: automatically detects English, Hindi, Marathi, Spanish, French, or Hinglish/code-mixed feedback and normalizes it to English before analysis — see [section 18](#18-multilingual--advanced-intelligence-v2-upgrade) for the full honest architecture.
- **Domain-aware analysis**: Electronics, E-commerce, Restaurant, Hotel, Travel, Banking, Food Delivery, or Other — aspect vocabulary adapts automatically.
- **Three analysis modes**: Single Feedback, Batch Dataset Upload (CSV/Excel), and Compare Languages — all inside one Analyze page.
- **One consolidated Dashboard**, organized into intelligence zones: CX Pulse, Customer Voice Intelligence, CX Issue Radar, Multilingual Intelligence, Trends & Forecast, Decision Center, and Ask CXIQ — no fragmented navigation.
- **Inline explainability**: every analysis result includes a "Why this prediction?" panel with highlighted words and contributing signals — no separate explainability page.
- **Ask CXIQ**: a natural-language Q&A box grounded entirely in real, pre-computed dashboard statistics.
- **Optional Gemini-powered business assistant**: layered on top of the ML/NLP results, with automatic rule-based fallback if unavailable.
- **No database required**: everything runs from uploaded files and in-memory processing.

## 3. Architecture

```
Customer Feedback
      │
      ▼
Text Preprocessing (cleaning, sentence/clause splitting)
      │
      ▼
Overall Sentiment (TF-IDF + Logistic Regression, blended with an explainable lexicon signal)
      │
      ▼
Aspect Extraction (domain vocabulary + rule-based hybrid)
      │
      ▼
Aspect-Level Sentiment (per-clause lexicon scoring)
      │
      ▼
Emotion Detection (NRC-style lexicon + negation handling)
      │
      ▼
Complaint Priority (explainable rule/signal aggregation)
      │
      ▼
Explainability (token highlighting + contributing signals)
      │
      ▼
Business Insight + Recommendations (rule-based, optionally polished by Gemini)
      │
      ▼
Dashboard Aggregation (KPIs, charts, trends, emerging issues)
```

Batch analysis runs every row through the exact same pipeline as single-feedback analysis, so results are always consistent between the two modes.

## 4. Technology Stack

**Frontend**: React 18, Vite, Tailwind CSS, React Router, Axios, Recharts, Lucide React, @clerk/clerk-react (optional)
**Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic, pandas, scikit-learn, joblib, httpx, langdetect, deep-translator, SQLAlchemy, psycopg2, PyJWT
**Storage**: PostgreSQL (optional — see section 19), with automatic in-memory fallback if unconfigured/unreachable
**Auth**: Clerk (optional — see section 19), with the app running fully in guest mode if unconfigured

No MongoDB / MySQL, no Docker — by design, for a fast local prototype (see [Limitations](#16-limitations)). PostgreSQL and Clerk authentication are supported as optional additions (v3 upgrade — see [section 19](#19-database--authentication-v3-upgrade)); the original zero-database, zero-login design remains the default if neither is configured.

## 5. Folder Structure

```
CXIQ/
├── frontend/
│   ├── src/
│   │   ├── components/       # Navbar, charts, badges, forms, states, MyDatasets
│   │   ├── pages/             # Landing, Analyze, Dashboard
│   │   ├── services/          # api.js (Axios client), authConfig.js (Clerk flag)
│   │   └── App.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example            # optional VITE_CLERK_PUBLISHABLE_KEY
│
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app entrypoint (DB check + startup)
│   │   ├── config.py          # thresholds, CX score weights, settings
│   │   ├── db.py               # PostgreSQL connection + graceful fallback
│   │   ├── models_db.py        # SQLAlchemy models: users, datasets, reviews
│   │   ├── auth.py             # Clerk JWT verification (optional)
│   │   ├── api/routes.py      # REST endpoints
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── services/          # sentiment, aspect, emotion, priority,
│   │   │                      # explainability, CX score, trends, insights,
│   │   │                      # Gemini, dashboard aggregation, pipeline,
│   │   │                      # language, translation, intelligence, ask,
│   │   │                      # repository (database access layer)
│   │   ├── utils/              # lexicons, file parsing
│   │   └── models/             # cached trained model artifact (.joblib)
│   ├── data/
│   │   ├── sample_customer_reviews.csv
│   │   └── training/sentiment_train.csv
│   ├── scripts/train_sentiment_model.py
│   ├── requirements.txt
│   └── .env.example             # optional DATABASE_URL, CLERK_ISSUER, CLERK_JWKS_URL, GEMINI_API_KEY
│
└── README.md
```

## 6. Installation

You will need:

- **Python 3.10 or later** — [python.org/downloads](https://www.python.org/downloads/)
- **Node.js 18 or later** (includes npm) — [nodejs.org](https://nodejs.org/)

Extract the project ZIP anywhere on your computer, e.g. `C:\Projects\CXIQ`.

## 7. Backend Setup

Open a terminal (Command Prompt or PowerShell on Windows) in the `backend` folder:

```bash
cd CXIQ/backend
```

Create and activate a virtual environment:

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy the example environment file:

**Windows:**
```cmd
copy .env.example .env
```

**macOS / Linux:**
```bash
cp .env.example .env
```

You can leave `.env` as-is — Gemini is optional (see [section 10](#10-gemini-api-setup-optional)).

Start the backend:

```bash
uvicorn app.main:app --reload --port 8000
```

On first run, this will automatically train the sentiment classifier from the bundled dataset (a few seconds) and preload the sample dataset. You should see:

```
INFO:cxiq:Sample dataset ready as dataset_id='sample'.
INFO:     Application startup complete.
```

The API is now running at `http://localhost:8000`. Interactive API docs are available at `http://localhost:8000/docs`.

## 8. Frontend Setup

Open a **second terminal** in the `frontend` folder:

```bash
cd CXIQ/frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`. The Vite dev server proxies `/api/*` requests to the backend at `http://localhost:8000`, so both servers must be running.

## 9. Environment Variables

Defined in `backend/.env` (copy from `.env.example`):

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | No | Enables the optional AI Business Assistant layer. Leave blank to use the built-in rule-based insight engine. |
| `GEMINI_MODEL` | No | Gemini model name. Defaults to `gemini-1.5-flash`. |
| `CORS_ORIGINS` | No | Comma-separated list of allowed frontend origins. Defaults to `http://localhost:5173`. |

## 10. Gemini API Setup (Optional)

CXIQ works completely without Gemini — the rule-based `insight_service` always runs and produces business insights and recommendations grounded in the actual analysis.

To enable the enriched Gemini narrative layer:

1. Get an API key from [Google AI Studio](https://aistudio.google.com/).
2. Add it to `backend/.env`:
   ```
   GEMINI_API_KEY=your_actual_key_here
   ```
3. Restart the backend.

If the key is invalid, the quota is exceeded, or the network call fails for any reason, CXIQ automatically and silently falls back to the rule-based recommendations — the application never breaks because of Gemini.

## 11. Running the Application

1. Start the backend (`uvicorn app.main:app --reload --port 8000`).
2. Start the frontend (`npm run dev`).
3. Open `http://localhost:5173` in your browser.
4. Go to **Analyze** to try a single review or upload a dataset.
5. Go to **Dashboard** to see the sample dataset's analytics immediately, or view your uploaded dataset via the "View Dashboard" button after batch analysis.

## 12. Dataset Format

Upload a `.csv` or `.xlsx` file. CXIQ auto-detects the review text column from these common names (case-insensitive): `review`, `text`, `review_text`, `feedback`, `comment`. If none match, it falls back to the longest average-length text column.

Optional columns (also auto-detected):

| Column | Purpose |
|---|---|
| `rating` | Factored into complaint priority and the CX Score |
| `date` | Enables trend analysis and emerging-issue detection |
| `product` | Shown in downloaded results |
| `category` | Enables "Sentiment by Category" chart |
| `customer_id` | Shown in downloaded results |

A ready-to-use sample dataset is included at `backend/data/sample_customer_reviews.csv` (655 reviews spanning electronics, e-commerce, restaurant, hotel, banking, and food-delivery domains, in a realistic mix of English, Hindi, Marathi, Hinglish, Spanish, and French) and is preloaded automatically as the default dashboard dataset (`dataset_id=sample`).

## 13. ML / NLP Pipeline

CXIQ is transparent about which components are trained ML models versus rule-based/lexicon components — no accuracy numbers are fabricated anywhere in this project.

| Component | Type | Details |
|---|---|---|
| **Overall Sentiment** | **Trained classical ML model** | TF-IDF (1–2 grams) + Logistic Regression, trained on `data/training/sentiment_train.csv` (a bundled, template-generated labeled dataset covering all supported domains). Trained automatically on first run and cached to `app/models/sentiment_lr.joblib`. Blended with a lexicon signal for robustness on real-world phrasing. |
| **Aspect Extraction & Aspect-Level Sentiment** | Rule-based / domain-vocabulary hybrid | Sentence → clause splitting (at "but", "however", commas, etc.) + domain vocabulary matching + a lexicon-based sentiment score per clause. Falls back to a noun-candidate heuristic for domains/aspects not in the vocabulary. |
| **Emotion Detection** | Rule-based (lexicon) | NRC-inspired lexicon mapped to Joy / Love / Anger / Sadness / Fear / Surprise, with negation handling and a weak sentiment-derived fallback signal. |
| **Complaint Priority** | Rule-based signal aggregation | Combines sentiment, negative aspect ratio, complaint-severity phrase matches, repeated-issue language, and star rating (if present) into an explainable 0–1 score, thresholded into Low/Medium/High/Critical. |
| **Customer Experience Score** | Deterministic formula | See `app/services/cxscore_service.py` — combines sentiment health, aspect health, priority penalty, and rating health with documented, configurable weights. |
| **Trend / Emerging Issue Detection** | Statistical rule | Month-bucketed negative-aspect share; flags an aspect as "emerging" if its share rises by a configurable threshold with a positive linear slope. |
| **Business Insights / Recommendations** | Rule-based, optional Gemini polish | Always computed from real structured results; Gemini (if configured) rewrites them into a management-friendly narrative using the same structured data as grounding — it does not invent metrics. |

**Why not transformers/deep learning?** The brief calls for a CPU-only, offline-runnable, instantly-explainable local prototype. A production upgrade path is documented below.

### Retraining / Fine-tuning

To retrain the sentiment model after editing `data/training/sentiment_train.csv`:

```bash
cd backend
python scripts/train_sentiment_model.py
```

This prints a held-out classification report and overwrites `app/models/sentiment_lr.joblib`.

**To upgrade to a fine-tuned transformer model later**: replace the internals of `SentimentService` in `app/services/sentiment_service.py` (keep the `predict(text) -> dict` interface) and similarly for `extract_aspects()` in `aspect_service.py` if you fine-tune a proper ABSA sequence model. No other code needs to change.

## 14. API Documentation

Base URL: `http://localhost:8000/api`

### `GET /health`
Returns service status and whether the sentiment model / Gemini are configured.

### `POST /analyze`
```json
{ "text": "The camera is excellent but the battery drains quickly.", "domain": "electronics", "rating": null }
```
Returns overall sentiment, aspects, emotion, priority, explanation, business insight, and recommendations.

### `POST /analyze/batch`
`multipart/form-data` with fields `file` (CSV/XLSX) and `domain`. Returns a dataset summary including `dataset_id`, used by the endpoints below.

### `GET /analyze/batch/{dataset_id}/preview?rows=10`
Returns a preview of analyzed rows for a given dataset.

### `GET /analyze/batch/{dataset_id}/download`
Streams back the analyzed dataset as a CSV.

### `GET /dashboard?dataset_id=sample`
Returns the full dashboard payload: KPIs, sentiment distribution, aspect summary, emotion distribution, priority distribution, recurring problems, trends, business insights, and recommendations.

Full interactive documentation (Swagger UI) is available at `http://localhost:8000/docs` while the backend is running.

## 15. Model Information

| Model | Status |
|---|---|
| TF-IDF + Logistic Regression (sentiment) | **Trained** on bundled data (see section 13) — a real, fitted scikit-learn model, not a pretrained download. |
| Sentiment / Emotion / Complaint lexicons | **Rule-based**, hand-curated — not trained on data. |
| Aspect vocabulary | **Rule-based**, hand-curated per domain — not trained on data. |
| Gemini (optional) | **Pretrained**, third-party (Google) — used only for narrative generation, never for classification. |

No accuracy percentage is claimed anywhere in the UI for the trained model beyond what `scripts/train_sentiment_model.py` prints from an actual held-out split of the bundled dataset — treat that number as illustrative, not a production benchmark, since the training data is template-generated rather than real annotated customer reviews.

Both the sentiment model (`app/models/sentiment_lr.joblib`) and the ABSA model (`app/models/absa_context_lr.joblib`) are trained and pickled with the exact scikit-learn version pinned in `requirements.txt`. If you retrain them (`scripts/train_sentiment_model.py`, `scripts/train_absa_model.py`), do so inside an environment using that same pinned version so the saved models don't emit a `InconsistentVersionWarning` when loaded by the running app.

## 16. Limitations

- **In-memory storage by default**: if no `DATABASE_URL` is configured/reachable, uploaded datasets are cleared when the backend restarts. Optional PostgreSQL persistence is available (see section 19) — when connected, datasets survive restarts.
- **Training data is synthetic/template-based**, not real annotated reviews — good for demonstrating the architecture, but the classifier would benefit from real labeled data before any production use.
- **Rule-based ABSA** works well for common aspect vocabulary but can occasionally mis-extract an aspect from free-form text it hasn't seen a pattern for (a fallback heuristic, not a trained sequence tagger).
- **Trend/emerging-issue detection** needs a reasonably sized, dated dataset to produce meaningful results; small datasets will correctly report "not enough data" rather than fabricating a trend.
- No authentication, multi-user accounts, or persistent history — appropriate for a local prototype, not for multi-tenant production use.

## 17. Future Improvements

- Fine-tune a transformer-based ABSA model (e.g. on SemEval ABSA datasets) once GPU resources and labeled data are available, and swap it in behind the existing `extract_aspects()` interface.
- Add a lightweight persistence layer (e.g. SQLite) for dataset history across restarts.
- Expand the sentiment training set with real, diverse customer review data.
- Add SHAP-based explanation for the Logistic Regression model as an additional explainability layer.
- Replace the free translation backend with a paid API (Google Cloud Translate, DeepL) for higher-volume production use — the translation layer is isolated in one service file specifically so this swap doesn't touch anything else.

## 18. Multilingual & Advanced Intelligence (v2 Upgrade)

This section documents the multilingual and advanced-analytics upgrade added on top of the original single-language CXIQ.

### 18.1 Multilingual architecture — honest design

CXIQ does **not** run separate native sentiment models per language. The architecture is deliberately simple:

```
Review
  │
  ▼
Language Detection (langdetect + a Hinglish keyword heuristic)
  │
  ├─ English  ──────────────────────────────┐
  ├─ Hindi / Marathi / Spanish / French ──▶ Translate to English (MyMemory, then Gemini as fallback)
  └─ Hinglish ──▶ Slang normalization ──▶ Translate to English
                                              │
                                              ▼
                                   Single English CXIQ Engine
                            (the same sentiment/ABSA/emotion/priority
                             pipeline documented in section 13)
```

Both `original_text` and `translated_text` are preserved on every result — the UI always shows the customer's original words; English is only what powers the analysis underneath. This is a **translation-based multilingual pipeline**, not native multilingual language understanding, and it's described that way everywhere in this project, including to end users (see the "Detected Language / Translated for Analysis" line on each result).

**Why this approach over training separate/native multilingual models:** one engine to validate and maintain instead of several; no fabricated per-language accuracy claims; translation quality for everyday customer-feedback sentences is generally reliable and is a legitimate, commonly used real-world CX architecture.

**Language priority:** English, Hindi, and Marathi are treated as the core supported languages (reflecting a realistic Indian-market CX product). Spanish and French are supported as a smaller demonstration set. Hinglish/code-mixed text is detected via a practical keyword heuristic (not a trained code-switching classifier) and normalized before translation.

### 18.2 Reliability (production-facing, not just demo-facing)

- **Two independent providers, tried in order**: MyMemory (`deep_translator.MyMemoryTranslator`, keyless) first, then Gemini as a fallback if MyMemory fails or is unreachable. `GoogleTranslator` is intentionally not used.
- **Bounded timeout**: 5s for MyMemory, 8s for the Gemini fallback — a slow/unreachable translation backend can never hang a request.
- **Retry with backoff for transient failures**: a timeout, connection blip, or rate-limit/quota response (429/5xx) is retried against the *same* provider up to twice with a short exponential backoff before falling through to the next provider — this is what keeps a busy batch upload from immediately exhausting the fallback provider's own quota over what was really just a momentary hiccup.
- **Bounded concurrency**: at most 3 translation requests (to either provider) are in flight at once, independent of how wide the overall batch-analysis thread pool is (default 8 workers) — this is specifically what prevents a batch upload from firing off a burst of simultaneous requests that trips MyMemory's rate limit and then Gemini's quota in turn.
- **Graceful fallback**: if translation fails for any reason after retries and both providers, CXIQ analyzes the original text as-is through the English pipeline rather than erroring out. The result is marked `translation_status: "failed"` and `reliable: false` so this is never silently hidden or presented as a confident prediction.
- **In-memory caching of successful translations only**, keyed by (language, text) — a `"failed"` result is deliberately *not* cached, so a transient failure never permanently poisons that exact review text for the rest of the process's lifetime; a later retry (manual or automatic) gets a real attempt, not a stale cached failure.
- **Retry failed reviews on demand**: `POST /api/analyze/batch/{dataset_id}/retry-failed` re-runs translation + analysis only for the rows in an already-saved dataset that couldn't be reliably analyzed the first time, and updates their stored results in place — reviews that were already reliable are left untouched. The Dashboard exposes this as a **"Retry Failed Translations"** button. This is distinct from the plain **Refresh** button, which only re-reads whatever is already stored and does not itself retry translation — the UI copy for both was corrected to say exactly this.
- **Concurrent batch processing**: rows in a batch upload are analyzed on a bounded thread pool (default 8 workers) specifically because translation is network-bound — this keeps a large multilingual dataset from processing one row at a time.
- **Confidence-gated language detection**: `langdetect` is noisy on short, informal text. CXIQ only accepts a non-English classification for supported languages, and requires a confidence floor for Latin-script languages (Spanish/French) to avoid misclassifying ordinary English sentences and triggering pointless translation attempts. Devanagari-script text (Hindi/Marathi) is accepted at any confidence since the script itself is unambiguous.
- **Translation health diagnostic**: the dashboard payload includes a `translation_health` field (non-English review count, how many translated successfully, success rate %) so an operator can see at a glance whether the translation backend is actually reachable in their deployment — without exposing this as a user-facing feature.

**Known sandbox/environment note**: translation requires outbound internet access to MyMemory's and (optionally) Gemini's APIs. In fully offline or firewalled environments, all non-English reviews will fall back to original-text analysis (correctness degrades gracefully, the app never crashes).

### 18.3 New dashboard intelligence zones

All of the following are computed from real analyzed data — no hardcoded or fabricated numbers:

- **Customer Voice Intelligence** — aspect mention volume + sentiment split + a risk label (Low/Medium/High/Critical, based on positive-mention ratio), replacing the old aspect-only bar chart with a combined view.
- **CX Issue Radar** — aspects ranked by a calculated **Risk Score**:
  `risk = frequency_share × negativity_ratio × avg_severity × recency_boost`
  where `frequency_share` is this aspect's mentions relative to the most-mentioned aspect, `negativity_ratio` is its negative-mention share, `avg_severity` is the average complaint-priority score of reviews mentioning it negatively, and `recency_boost` gives up to +50% if trend detection has already flagged the aspect as rising. Bucketed into Critical/High/Medium relative to the top score in the dataset.
- **Decision Center** — for the top-risk issues, assembles the evidence (mentions, negativity, dominant emotion, trend, high-priority count) and a templated recommendation per team (Product / Support / CX). Fully rule-based — Gemini is not involved in this zone.
- **Multilingual Intelligence (Language CX Comparison)** — sentiment split, top negative aspect, and an indicative CX Score per detected language, always computed from the full dataset (independent of the dashboard's language filter, since its purpose is comparing languages against each other).
- **CX Forecast** — a simple linear-regression projection of the negative-sentiment trend two periods forward. Explicitly labeled as a basic trend projection, not a sophisticated forecasting model, and only shown when enough historical data exists (same `MIN_TIME_BUCKETS_FOR_TREND` gate as the existing trend detector).
- **Ask CXIQ** — a small natural-language Q&A box. The flow is always: real pre-computed dashboard statistics → a rule-based answer (always available) → optional Gemini rewrite of that same grounded answer into more natural language. Gemini never sees raw reviews and never invents its own statistics; if it's not configured or fails, the rule-based answer is what the user sees.
- **Language filter** — a single dropdown on the dashboard; every existing chart/KPI already aggregates from row-level data, so it filters for free without any new chart types.

### 18.4 New API endpoints

| Endpoint | Purpose |
|---|---|
| `POST /api/analyze/compare` | Cross-Language Analysis: analyze 2–6 feedback entries (any mix of supported languages) side by side. |
| `POST /api/dashboard/ask` | Ask CXIQ: `{dataset_id, question}` → grounded natural-language answer. |
| `GET /api/dashboard?language=Hindi` | Existing dashboard endpoint, now with an optional language filter. |

`POST /api/analyze` now additionally returns `original_text`, `detected_language`, `language_code`, `is_code_mixed`, `translated_text`, and `translation_status`.

### 18.5 Validating the multilingual pipeline

Because live translation requires outbound internet, the multilingual pipeline should be validated end-to-end on a machine with normal internet access (rather than a locked-down sandbox). A practical validation approach:

1. Take a small set of hand-written sentences per language with a manually-decided expected sentiment/aspect outcome.
2. Run each through `POST /api/analyze` and record: detected language, translated text, and the resulting sentiment/aspects.
3. Compare against the manual expectation and note any mismatches.

This is intentionally a manual/spot-check validation, not an automated accuracy benchmark — CXIQ does not fabricate accuracy, F1, or confusion-matrix numbers for the multilingual layer, since no labeled multilingual test set was available during development. Language **detection** itself was validated programmatically during development against all six target languages (English, Hindi, Marathi, Spanish, French, Hinglish) with zero false positives on the bundled English dataset.

### 18.6 Dataset

The bundled `data/sample_customer_reviews.csv` was expanded from 280 to 655 rows and now includes six domains (electronics, e-commerce, restaurant, hotel, banking, food delivery) and a deliberate language mix reflecting the priority above: English (majority), Hindi and Marathi (substantial), Hinglish (meaningful demonstration), Spanish and French (smaller demonstration set). This remains a constructed/demo dataset, clearly labeled as such — not scraped-and-claimed-as-real data. For production use, a real multilingual dataset (e.g. the Multilingual Amazon Reviews Corpus) should replace it; the architecture (domain-agnostic column detection, language-agnostic pipeline) requires no code changes to accept one.

## 19. Database & Authentication (v3 Upgrade)

This section documents the persistence and login layer added on top of the multilingual upgrade.

### 19.1 Why add these, and what changes for the user

The original CXIQ stored everything in memory — restarting the backend erased every uploaded dataset. This upgrade adds:

- **PostgreSQL** so datasets and their analyzed reviews persist across restarts (a real requirement for anything beyond a local demo).
- **Clerk authentication** so uploads can optionally be tied to a personal account, enabling a "My Datasets" list.

**Both are entirely optional and off by default.** CXIQ runs exactly as before — single analysis, batch upload, dashboard, compare languages, Ask CXIQ — with zero configuration. Adding a database and/or Clerk key only *unlocks* persistence and login; nothing breaks or requires them.

**The one visible UI change**: when Clerk is configured, a "Sign In" button appears in the navigation bar (visible on every page, including Home) and becomes a small account menu once signed in. Until Clerk is configured, the navbar looks exactly as it always has — no login button appears.

### 19.2 Database schema

Three tables, deliberately minimal — each mirrors exactly what the analysis pipeline already produces, so almost none of the existing dashboard/aggregation code needed to change:

| Table | Purpose | Key columns |
|---|---|---|
| `users` | One row per person who has signed in via Clerk | `clerk_user_id` (unique), `email` |
| `datasets` | One row per uploaded batch (or the preloaded `"sample"` dataset) | `id`, `user_id` (nullable — guests can upload too), `filename`, `domain`, `total_records` |
| `reviews` | One row per analyzed review — the big table | `dataset_id`, `review` (original text), `analyzed_text`, `language`, `overall_sentiment`, `emotion`, `priority`, `detected_aspects` (JSON), `aspect_sentiments` (JSON), `rating`, `date`, `product`, `category` |

Tables are created automatically on first startup (`Base.metadata.create_all`) — no manual migration step needed for this version.

### 19.3 Setting up PostgreSQL

**Windows / macOS / Linux**, using a local install:

1. Install PostgreSQL ([postgresql.org/download](https://www.postgresql.org/download/)) or use a free hosted instance (e.g. [Neon](https://neon.tech), [Supabase](https://supabase.com), [Railway](https://railway.app) — all have generous free tiers and give you a ready-to-use connection string).
2. Create a database (locally: `createdb cxiq`).
3. Add the connection string to `backend/.env`:
   ```
   DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/cxiq
   ```
4. Start the backend normally. On startup you'll see either:
   ```
   INFO: Database connected: tables ready.
   INFO: Running with PostgreSQL-backed storage (datasets persist across restarts).
   ```
   or, if unreachable:
   ```
   WARNING: Database unavailable (...). Falling back to in-memory storage...
   ```
   Both are safe — the second just means you're running exactly like before.

**Verified during development**: a local PostgreSQL instance was installed and tested end-to-end — table creation, batch upload, dashboard aggregation from the database, and true persistence across a full backend restart (uploaded a dataset, killed the process completely, started a new process, confirmed the data was still there). The graceful in-memory fallback was also tested by stopping PostgreSQL mid-session and confirming the app kept working.

### 19.4 Setting up Clerk authentication

1. Create a free account at [clerk.com](https://clerk.com) and create an application.
2. From your Clerk dashboard, copy:
   - The **Publishable Key** → `frontend/.env` as `VITE_CLERK_PUBLISHABLE_KEY`
   - Your instance's **Frontend API URL** (looks like `https://your-app.clerk.accounts.dev`) → `backend/.env` as both:
     ```
     CLERK_ISSUER=https://your-app.clerk.accounts.dev
     CLERK_JWKS_URL=https://your-app.clerk.accounts.dev/.well-known/jwks.json
     ```
3. Restart both servers. The "Sign In" button will now appear in the navbar automatically — no other code changes needed.

**How verification works (no Clerk SDK dependency on the backend)**: the frontend attaches the signed-in user's session token as `Authorization: Bearer <token>` on API requests. The backend verifies it using standard JWT + JWKS verification (`PyJWT` + Clerk's public signing keys) — this is Clerk's documented approach for backends not using their Node/Next SDK, and keeps the backend dependency-light.

**Honest limitation**: live Clerk token verification requires reaching Clerk's public JWKS endpoint over the internet, which wasn't reachable from the sandboxed development environment used to build this feature. The verification logic follows Clerk's documented spec exactly, and the surrounding code (guest fallback, optional-vs-required auth dependencies, user upsert on first sign-in) was tested thoroughly — but end-to-end login should be verified once more on a machine with normal internet access before treating it as production-verified. The app is designed so that if anything about the Clerk setup is wrong, it fails safe: requests are simply treated as a guest, never as a crash.

### 19.5 What login unlocks

- Batch uploads made while signed in are tied to your account (`datasets.user_id`).
- A **"My Datasets"** panel appears at the top of the Dashboard (only when signed in) listing your previous uploads, so you can switch between them without needing to remember dataset IDs.
- Guests can still do everything else — single analysis, batch upload (untied to an account), viewing the sample dashboard, compare languages, Ask CXIQ.

### 19.6 New/changed environment variables

**`backend/.env`**:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cxiq
CLERK_ISSUER=
CLERK_JWKS_URL=
```

**`frontend/.env`**:
```
VITE_CLERK_PUBLISHABLE_KEY=
```

All four are optional; leaving them blank preserves the exact behavior of the previous version.

## 20. Real Trained ABSA Model (v4 Upgrade)

This section documents replacing the pure lexicon-based aspect sentiment with a genuinely trained, context-aware model, plus the honesty fixes made alongside it.

### 20.1 What changed and why

Three real bugs were reported and fixed:

1. **"Battery drains extremely fast... very disappointing" scored positive.** Root cause: the old approach scored sentiment word-by-word from a fixed lexicon with no real context understanding — "fast" is a positive word in our lexicon (correct for "fast delivery"), and nothing distinguished that from "drains fast" (bad). **Fixed** by training a real context-aware classifier (below).
2. **Failed translation silently produced a confident (and sometimes wrong) prediction.** Fixed: when translation genuinely fails for non-English text, CXIQ now returns a clearly-marked low-confidence/neutral result with an honest note, instead of running an English-only model on text it can't understand and presenting the result as normal. See `pipeline_service.analyze_review()` — every result now carries a `reliable: bool` flag, and dashboard aggregation excludes unreliable rows from all real statistics (they're still counted in the total and reported separately via `translation_health`).
3. **Stray words like "Highly" and "Everyone" appearing as fake aspects.** Fixed: tightened the aspect-guessing fallback to exclude intensifiers, negations, pronouns, and common adverb endings.

### 20.2 Real dataset used: MAMS-ATSA

Per an explicit "no Hugging Face, pick the dataset most likely to genuinely improve accuracy" decision, CXIQ trains its aspect-sentiment model on **MAMS-ATSA** (Jiang et al., 2019, EMNLP — "A Challenge Dataset and Effective Models for Aspect-Based Sentiment Analysis"), sourced from its official repository: https://github.com/siat-nlp/MAMS-for-ABSA.

MAMS was chosen over generic sentiment datasets because it's specifically constructed so most sentences contain **multiple aspects with different sentiment polarities** — exactly CXIQ's core "camera is great but battery is bad" use case, and exactly the failure mode reported.

13,854 real, human-labeled (sentence, aspect term, polarity) examples, using the dataset's own official train/validation/test split (11,186 / 1,332 / 1,336) — never reshuffled or altered.

Reproduce with:
```bash
python scripts/prepare_mams_dataset.py   # downloads + cleans the dataset
python scripts/train_absa_model.py        # trains + evaluates + saves the model
```

### 20.3 Model & methodology

TF-IDF (1-3 grams) + Logistic Regression, trained on a **local context window** (up to 6 words each side of the aspect term, never crossing a contrastive boundary like "but"/"however" or clause-ending punctuation) rather than the whole sentence — this is what lets the model learn that the same word can mean different things for different aspects in the same sentence, instead of a fixed per-word score.

Hyperparameter (regularization strength C) selected via validation-set macro F1 only; final numbers below are from the held-out test split, evaluated exactly once.

**Real, measured test-set results** (never rounded up, see `docs/absa_model_evaluation.md` for the full report including confusion matrix):

| Metric | Value |
|---|---|
| Accuracy | 68.3% |
| Macro F1 | 67.5% |
| Weighted F1 | 68.3% |

This is consistent with published non-neural baselines on MAMS (papers report ~65-75% for classical models; ~80%+ requires BERT-scale models, out of scope here per the "no heavy/HF training" decision).

At inference, this trained model is **blended** with CXIQ's hand-curated lexicon (60% model / 40% lexicon) — the same blending principle already used for overall sentiment — because the model, trained only on restaurant reviews, can carry restaurant-specific word associations (e.g. "fast"/"quickly" skew positive there — fast service — but not universally). The lexicon corrects for exactly this domain-transfer gap.

### 20.4 Honest, known remaining limitations

- MAMS is restaurant-domain only. Concepts CXIQ needs but MAMS never covers (e.g. "refund", "delivery" in an e-commerce sense) get weaker, sometimes wrong, model predictions — the lexicon blend helps but doesn't fully correct every case. This was directly observed and is not hidden: e.g. "Refund process took forever and support was unhelpful" can still misclassify the Refund aspect as positive, because MAMS has no training signal for what "refund" even means, and only one weak lexicon word ("forever") is available to correct it.
- The reported accuracy (68%) is real but modest — a fair, unexaggerated reflection of a classical (non-neural) model trained on ~11K restaurant-domain examples applied across multiple domains. No claim of 90%+ accuracy is made anywhere in this project.
- The honest fix for the remaining domain-transfer gaps is more/better training data covering CXIQ's actual domains (electronics, e-commerce, hotel), not further hand-tuning of blend weights to force specific examples to pass — which would just be a disguised hardcoded rule.

### 20.5 Clerk login button — investigation result

The frontend code was directly tested (compiled with a real-format Clerk key and the compiled output inspected) and confirmed correct: `ClerkProvider`, `SignInButton`, `SignedIn`/`SignedOut`, and `UserButton` are all present and functional, and the "Sign In" button genuinely renders once a valid publishable key is supplied. If it's not appearing in your deployment, the most likely causes are environmental, not a code defect:
- The key was added to `frontend/.env`, but the Vite dev server wasn't **restarted** afterward (Vite only reads env vars at startup).
- The key was added to the wrong file (must be `frontend/.env`, not `.env.example`, and not the backend's `.env`).
- A typo in the variable name — it must be exactly `VITE_CLERK_PUBLISHABLE_KEY`.

## 21. My Datasets / Analysis History (v5 Upgrade)

This section documents the "My Datasets" SaaS-style history feature, plus two real bugs fixed alongside it.

### 21.1 What changed for the user

- The bundled sample dataset is **no longer auto-loaded** for a signed-in user. Visiting `/dashboard` with nothing analyzed yet now shows a "Welcome to CXIQ" empty state with **Upload Dataset** / **Try Sample Dataset** buttons, matching how a real SaaS product behaves. Signed-in users who *do* have datasets are taken straight to their most recently analyzed one.
- A new **"My Datasets"** nav item/page lists every dataset a signed-in user has analyzed, as compact cards (filename, record count, domain, date, an "Analyzed"/"Sample Dataset" badge, and a "View Analysis" button that reopens it on the existing Dashboard — no re-upload, no re-running the ML pipeline).
- **Guests, and any deployment without Clerk configured, are completely unaffected** — the Dashboard still defaults to the shared sample dataset exactly as before. This feature only changes behavior once someone is signed in.

### 21.2 Files changed

| File | Change |
|---|---|
| `backend/app/models_db.py` | Added `Dataset.is_sample` column |
| `backend/app/services/repository.py` | `create_dataset`/`list_datasets_for_user`/`get_dataset_meta` now carry `is_sample`; added `get_user_sample_dataset_id`, `clone_dataset_for_user` |
| `backend/app/services/dashboard_service.py` | Added `load_sample_dataframe()` (shared with `main.py`'s startup preload); added `_empty_dashboard()` helper (see bug fix below); `process_batch` accepts `is_sample` |
| `backend/app/services/intelligence_service.py` | `compute_language_breakdown` now computes % from *reliable* rows only and reports `unreliable_count`/`unreliable_pct` per language (see bug fix below) |
| `backend/app/services/translation_service.py` | Multi-provider translation fallback + real error logging (see bug fix below) |
| `backend/app/api/routes.py` | Added `_assert_dataset_access` ownership guard, applied to `/dashboard`, `/analyze/batch/{id}/preview`, `/analyze/batch/{id}/download`, `/dashboard/ask` |
| `frontend/src/pages/Dashboard.jsx` | New default-dataset gating logic; crash fix; translation-health banner |
| `frontend/src/pages/Analyze.jsx` | Reads `?mode=batch` to preselect the Upload Dataset tab |
| `frontend/src/components/LanguageComparisonTable.jsx` | Added Neutral column + per-language "⚠ N unreliable" indicator |
| `frontend/src/components/Navbar.jsx` | Added "My Datasets" nav link (shown only when auth is configured) |
| `frontend/src/services/api.js` | `getMyDatasets` now calls `/datasets/my`; added `getDatasetDetail`, `loadSampleDataset` |

### 21.3 Files added

- `frontend/src/pages/MyDatasets.jsx` — the My Datasets page (signed-in / signed-out / no-auth states)
- `frontend/src/components/DatasetCard.jsx` — one dataset history card
- `frontend/src/components/GetStartedActions.jsx` — shared "Upload Dataset" / "Try Sample Dataset" button pair, used by every empty state

`frontend/src/components/MyDatasets.jsx` (the old small inline chip list that used to sit at the top of the Dashboard) was **removed** — its job is now done properly by the full My Datasets page, so keeping both would have been redundant clutter.

### 21.4 Database behavior

One new column: `datasets.is_sample` (boolean, default `false`), marking a user's personal copy of the bundled sample dataset. Tables are still created automatically via `Base.metadata.create_all` on startup, but **that only creates brand-new tables — it does not `ALTER` an existing `datasets` table.** If you already have a running database from the v3 upgrade, run this once:

```sql
ALTER TABLE datasets ADD COLUMN is_sample BOOLEAN DEFAULT FALSE;
```

(Or just drop the `datasets`/`reviews` tables and let the app recreate them, if you don't need to keep existing local dev data.)

### 21.5 New API endpoints

| Endpoint | Auth | Behavior |
|---|---|---|
| `GET /api/datasets/my` | Required | The signed-in user's datasets (same data as the existing `GET /api/datasets`, kept for compatibility) |
| `GET /api/datasets/{dataset_id}` | Required | Metadata for one dataset — 404 if it doesn't belong to the caller |
| `POST /api/datasets/sample` | Required | Idempotent: creates (or reuses) the caller's personal copy of the sample dataset |

### 21.6 How user-level dataset isolation works

Every endpoint that reads back a previously-analyzed dataset (`GET /dashboard`, the batch preview/download endpoints, `POST /dashboard/ask`, and the three endpoints above) now runs through `_assert_dataset_access()` in `routes.py`:

- The caller's identity comes **only** from the verified Clerk session token (`app/auth.py`'s `get_current_user_optional`/`require_user`) — a `user_id` sent from the frontend is never trusted or even read for this purpose.
- If a dataset has an owner (`datasets.user_id` is set) and the caller isn't signed in as that exact owner, the endpoint returns **404** (not 403), so a dataset's existence/ownership can't be probed by guessing IDs.
- Datasets with no owner (guest uploads, and the original shared `"sample"` dataset preloaded at startup) remain openly accessible — this is unchanged, existing guest-mode behavior.
- `POST /api/datasets/sample` gives each signed-in user their **own** `is_sample=true` dataset row, so Account A's sample copy and Account B's sample copy are entirely separate rows with separate `reviews`, not a shared dataset — satisfying the isolation test in section 21.8 even for the sample dataset.

### 21.7 How the sample dataset is now loaded

Clicking **"Try Sample Dataset"** calls `POST /api/datasets/sample`, which:

1. Checks whether the signed-in user already owns a sample dataset (`is_sample=true`) — if so, returns it as-is (idempotent, no duplicates on repeat clicks).
2. Otherwise, **clones** the already-analyzed shared `"sample"` dataset (preloaded once at backend startup, unchanged from the previous version) into a brand-new dataset row + review rows owned by that user — without re-running the ML/translation pipeline. This is both fast and avoids depending on the (sometimes flaky, see 21.9) translation backend just to load a demo dataset.
3. Falls back to analyzing the bundled CSV fresh only if the shared sample dataset somehow isn't present yet (e.g. a brand-new deployment where startup preload hasn't run).

### 21.8 How previous analyses are restored

Clicking **"View Analysis"** on a My Datasets card simply navigates to `/dashboard?dataset_id=<id>` — the existing `GET /api/dashboard` endpoint (unchanged aggregation logic) reads the already-analyzed rows straight from PostgreSQL and rebuilds the dashboard view. **No CSV re-upload and no re-running of the ML pipeline** — this was already true of the existing architecture; the new access-control check only adds an ownership check in front of it.

### 21.9 Two bugs fixed alongside this feature

**Bug 1 — Dashboard crashed when picking a language from the dropdown.**
Root cause: `build_dashboard()` returned a partial payload (missing `kpis`, `sentiment_distribution`, etc.) whenever a language filter matched only reviews whose translation had failed. The frontend read `data.kpis.reviews_analyzed` unconditionally and crashed. **Fixed** with a new `_empty_dashboard()` helper that always returns a complete, zeroed-out payload, plus a matching frontend guard (`!data.kpis || data.kpis.reviews_analyzed === 0`).

**Bug 2 — Non-English reviews showing flat Neutral / 0% positive / 0% negative.**
Root cause: translation was handled by a single provider, with failures silently swallowed. **Fixed** (see section 18.2 for the current, further-hardened implementation — MyMemory first, Gemini as fallback, with retry/backoff and bounded concurrency):
- `translation_service.py` tries MyMemory first, then Gemini as a fallback before giving up, and logs the real error instead of swallowing it — check your backend logs for lines like `Translation: MyMemory failed for 'fr': ...` to see exactly what's failing in your environment.
- `compute_language_breakdown()` now computes Positive/Neutral/Negative percentages from **reliable** rows only, and reports `unreliable_count` per language, so a translation outage shows up as a clear "⚠ N unreliable" indicator instead of silently masquerading as "0% positive, 0% negative" sentiment data.
- The Dashboard now shows a banner when any reviews couldn't be translated, explaining why and how many, with a "Retry Failed Translations" button (see section 22).

**To verify translation connectivity directly** on your machine:
```bash
cd backend
python -c "from deep_translator import MyMemoryTranslator; print(MyMemoryTranslator(source='fr', target='en-GB').translate('Le produit est excellent'))"
```
If that raises an error, MyMemory falls back to Gemini automatically (if `GEMINI_API_KEY` is configured in `.env`) — otherwise, or if both fail, non-English reviews will hit the honest neutral fallback until connectivity is available.

### 21.10 Testing the feature locally

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

With `DATABASE_URL` and the Clerk env vars configured (see section 19), run the isolation test from the feature spec:

1. **Sign in as Account A.** Go to Dashboard → see the "Welcome to CXIQ" empty state (not the sample dataset).
2. Analyze Dataset A and Dataset B (Analyze → Upload Dataset).
3. Open **My Datasets** → confirm both appear as cards.
4. Click Dataset A's "View Analysis" → confirm its dashboard loads without re-uploading.
5. Sign out, sign in as **Account B**.
6. Open Dashboard → confirm Account A's datasets are not shown (Account B gets its own empty state).
7. Open My Datasets → confirm it's empty for Account B.
8. Analyze Dataset C. Open My Datasets → confirm only Dataset C is listed.
9. Sign out, sign back in as **Account A** → confirm Dataset A and B are still there and still load correctly, and Dataset C is never visible.

To check the multilingual fix, upload a dataset with French/Spanish/Hindi reviews (or use `backend/data/sample_customer_reviews.csv`, which already includes non-English rows) and confirm the Language CX Comparison table shows real Positive/Neutral/Negative percentages rather than 0%/0%, and that switching the Dashboard's language dropdown between languages no longer crashes the page.

## 22. Reliability & Honesty Fixes (v6 Upgrade)

This section documents five real bugs reported and fixed after the v5 upgrade above.

### 22.1 Balanced ("neither X nor Y") sentences misclassified

**Bug**: `"I am neither happy nor sad with the phone"` scored Positive sentiment (75%), Joy emotion (75%), and surfaced "Sad" as a product aspect — the business insight then wrongly claimed the customer was satisfied.

**Root causes and fixes**:
- `sentiment_service.is_balanced_neither_nor()` only recognized words in `SENTIMENT_LEXICON` as sentiment-bearing. "happy" is there; "sad" lives only in `EMOTION_LEXICON`, so the balanced-construction check never fired and "happy" leaked through as the (wrong) overall sentiment. **Fixed**: the check now also counts `EMOTION_LEXICON` words.
- `emotion_service.py` had no handling for balanced constructions at all — it counted Joy=1, Sadness=1 and a tie was resolved arbitrarily by dict order (Joy always won). **Fixed**: `detect_emotion()` now detects a genuine balanced construction and returns Neutral instead of guessing.
- `aspect_service.py`'s fallback aspect-guesser (which looks at tokens near a sentiment word) had no filter against emotion words, so "sad" got captured as a fake aspect. **Fixed**: emotion-lexicon words are now excluded from ever being guessed as an aspect.
- **Regression caught during fixing**: the original balanced-detection regex scanned up to 80 characters after "nor", which could pull an unrelated clause into the same "balanced" verdict — e.g. `"the camera is neither the best nor the worst, but delivery was late and rude staff"` was incorrectly forced to fully neutral. **Fixed**: the check is now clause-scoped (via `split_clauses`) and additionally verifies no *other* clause carries its own independent sentiment before treating the whole text as balanced/neutral.
- Two small, related lexicon gaps found and fixed along the way: `"best"` had no positive weight in `SENTIMENT_LEXICON` even though its natural opposite `"worst"` did, and `"crashing"` (present tense) was missing alongside `"crashes"`/`"crashed"`.

### 22.2 Translation failures during batch upload

**Bug**: in a 15-review batch, 4 reviews failed translation — MyMemory failures followed by Gemini HTTP 429 quota errors.

**Fixed** in `translation_service.py` (order preserved: MyMemory first, Gemini fallback; `GoogleTranslator` intentionally not added):
- **Bounded concurrency** — at most 3 translation requests in flight at once (`MAX_CONCURRENT_TRANSLATIONS`), independent of the wider batch thread pool, so a large upload no longer fires a burst of simultaneous requests at either provider.
- **Retry with backoff for transient failures** — timeouts, connection errors, and 429/5xx responses are retried against the same provider (up to `MAX_RETRIES`) with a short exponential backoff before falling through to the next provider.
- **Failed translations are no longer cached permanently** — only successful translations are cached; a transient failure no longer permanently "poisons" that exact review text.
- **New targeted retry endpoint**: `POST /api/analyze/batch/{dataset_id}/retry-failed` re-runs translation + analysis only for the rows that couldn't be reliably analyzed the first time, and updates their stored results in place (reliable rows are left untouched). Exposed on the Dashboard as a **"Retry Failed Translations"** button.
- **Refresh button wording corrected** — it previously said "Refresh to retry them", which was inaccurate (it only reloads already-stored results). It now links to the new retry button instead, and carries a tooltip clarifying it doesn't retry translation.
- A large batch (e.g. 100 reviews) now completes gradually within the bounded concurrency rather than the previous fully-parallel burst; failures are never silently recorded as valid neutral predictions — they're always marked `reliable: false`.

### 22.3 Misleading dashboard numbers for a fully-failed language

**Bug**: when every review for a language failed translation, the Language CX Comparison table still showed e.g. "French: 100% Neutral" with a computed CX Score.

**Root cause**: `compute_language_breakdown()` in `intelligence_service.py` fell back to using *all* rows (including failed-translation placeholders) whenever a language had zero reliable rows: `basis = reliable_rows or lang_rows`. **Fixed**: that fallback was removed. A language with zero reliable rows now gets `status: "no_reliable_analyses"`, `cx_score: null`, and null sentiment percentages instead of a fabricated result; `reviews` (total uploaded), `reliably_analyzed`, and `unreliable_count` are all reported separately so the three quantities are never conflated. `LanguageComparisonTable.jsx` shows "No reliable analyses" in place of the percentage columns for that row.

### 22.4 Small-sample trend/forecast claims

**Bug**: "emerging issue" and forecast claims were presented from months with only a handful of reviews, where a single review could swing a month from 0% to 100%.

**Fixed** in `trend_service.py`: a new `MIN_REVIEWS_PER_MONTH_FOR_TREND` (default 5) check runs alongside the existing `MIN_TIME_BUCKETS_FOR_TREND` (minimum 3 distinct months) check. If any month bucket has fewer reviews than the threshold, both emerging-issue detection and the forecast are skipped in favor of an honest, specific message (e.g. naming which months have too little data) instead of a confident claim. Genuine results for larger, well-populated datasets are unchanged — verified with a synthetic 18-review/3-month dataset that still correctly detects a rising "Battery" complaint trend and produces a forecast.

### 22.5 Model version warning and exposed API key

**Bug**: scikit-learn models saved under version 1.5.1 were being loaded under 1.6.1 (compatibility warning), and the Gemini API key appeared in a logged request URL.

**Fixed**:
- Both `sentiment_lr.joblib` and `absa_context_lr.joblib` were retrained inside an environment matching the scikit-learn version pinned in `requirements.txt` (1.6.1) — confirmed zero `InconsistentVersionWarning` on load.
- `gemini_service.py` now sends the API key via the `x-goog-api-key` request **header** instead of a `?key=...` query parameter, so it can no longer appear in a logged request URL or in an HTTP-client exception message (which tend to include the URL). A `_redact_secret()` helper additionally strips the key from any exception message as a second, defense-in-depth layer.
- The real `.env` files (which contained a live Gemini API key and a database password) were removed from the delivered project; `.env.example` files were rewritten with obvious placeholder values. **A second, more serious instance of the same problem was also found and fixed**: `backend/app/config.py` had a real-looking database password hardcoded directly as the `DATABASE_URL` Python default (not just in `.env`) — this would have shipped with the source code regardless of what happened to `.env`. It's now a generic, clearly-non-secret placeholder.
- **You should still rotate the Gemini API key that was exposed**, as you noted you would — it was live in the code you shared with us.

### 22.6 Files changed

| File | Change |
|---|---|
| `backend/app/services/sentiment_service.py` | Clause-scoped, emotion-aware balanced "neither...nor" detection |
| `backend/app/services/emotion_service.py` | Returns Neutral for genuine balanced constructions |
| `backend/app/services/aspect_service.py` | Excludes emotion-lexicon words from fallback aspect guessing |
| `backend/app/utils/lexicons.py` | Added `"best"` and `"crashing"` |
| `backend/app/services/translation_service.py` | Bounded concurrency, retry-with-backoff, no permanent caching of failures |
| `backend/app/services/gemini_service.py` | API key moved to request header; secret redaction on error paths |
| `backend/app/services/repository.py` | Exposed `Review.id`; added `update_review_analysis()` |
| `backend/app/services/dashboard_service.py` | Added `retry_failed_translations()` |
| `backend/app/api/routes.py` | Added `POST /analyze/batch/{dataset_id}/retry-failed` |
| `backend/app/services/intelligence_service.py` | `compute_language_breakdown()` no longer fabricates results for languages with zero reliable rows |
| `backend/app/services/trend_service.py` | Per-month minimum-reviews check for emerging issues/forecast |
| `backend/app/config.py` | Removed hardcoded database password default; added `MIN_REVIEWS_PER_MONTH_FOR_TREND` |
| `backend/app/models/sentiment_lr.joblib`, `backend/app/models/absa_context_lr.joblib` | Retrained under the pinned scikit-learn version |
| `backend/.env.example`, `frontend/.env.example` | Placeholder values instead of real secrets |
| `frontend/src/components/LanguageComparisonTable.jsx` | Shows "No reliable analyses" instead of a fabricated row |
| `frontend/src/pages/Dashboard.jsx` | "Retry Failed Translations" button; corrected Refresh copy |
| `frontend/src/services/api.js` | Added `retryFailedTranslations()` |
| `backend/tests/test_issue_fixes.py` | New — regression tests for all five issues above |

### 22.7 Verification performed

- `backend/tests/test_issue_fixes.py`: 12 tests, all passing — covering the exact reported neutral sentence, ordinary positive/negative reviews, a mixed-aspect review, the clause-scoping regression, transient-failure retry, permanent-failure non-caching, an unreliable-translation result, a language with zero reliable rows, thin-data trend suppression, and a larger dataset's genuine trend being preserved.
- Both models reloaded with zero scikit-learn version warnings.
- `npm run build` in `frontend/` completes with no errors.
- **Not tested**: live translation against MyMemory/Gemini (this sandbox has no outbound access to either), and the full Windows setup flow end-to-end. Please verify translation connectivity and the retry button against your real `.env` before relying on it for your one-day deadline.

