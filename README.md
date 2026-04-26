# ZomatoUseCase

Phase-wise implementation of an AI-powered restaurant recommendation system inspired by Zomato.

## Current Status

- Implemented: **Phase 0 (Scope and Foundations)**
- Implemented: **Phase 1 (Data ingestion and canonical model)**
- Implemented: **Phase 2 (User preferences and validation)**
- Implemented: **Phase 3 (Integration layer: retrieval + prompt assembly)**
- Implemented: **Phase 4 (Recommendation engine with Groq LLM)**
- Implemented: **Phase 5 (Output rendering and telemetry)**
- Implemented: **Phase 6 (Backend API Service with FastAPI)**
- Implemented: **Phase 7 (Frontend Web Application with React + Vite)**
- Implemented: **Phase 8 (Streamlit Deployment)**
- Pending: **Phase 9 (Deployment, Hardening and Handoff)**

## Architecture

```
Data ingestion -> User input -> Integration -> LLM recommendation -> Output display -> Backend API -> Frontend
```

See [`docs/phased-architecture.md`](docs/phased-architecture.md) for full details.

## Tech Stack

- **Language/runtime:** Python 3.10+
- **Core engine:** `src/phase0/` through `src/phase5/`
- **Backend API:** FastAPI + Uvicorn (`src/phase6/api/`)
- **Frontend:** React + Vite + Tailwind CSS (`frontend/`)
- **Streamlit app:** `streamlit_app.py` + `src/phase8/app.py`
- **Dataset:** Hugging Face `datasets` library
- **LLM:** Groq API (OpenAI-compatible)
- **Packaging:** `pyproject.toml` (`setuptools`)
- **Secrets:** environment variables via `.env` (never commit secrets)

## Quick Start

### 1. Install dependencies

```bash
python -m pip install -e .
```

### 2. Configure environment

Copy `.env.example` to `.env` and set your keys:

```bash
GROQ_API_KEY=your_groq_key_here
```

### 3. Run CLI diagnostics

```bash
milestone1 info
milestone1 doctor
milestone1 ingest-smoke --limit 5
milestone1 prefs-parse --location Bangalore --budget-band medium --cuisines "Italian,Chinese" --minimum-rating 4
```

### 4. Run the Backend API

```bash
uvicorn phase6.api.main:app --reload
python -m uvicorn phase6.api.main:app --host 127.0.0.1 --port 8000
```

Then open `http://localhost:8000/docs` for interactive Swagger UI.

### 5. Run the Frontend

In a separate terminal:

```bash
cd frontend
npm install
npm run dev

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; cd "c:\Users\HP\Desktop\shiv\programming project\Git_hub project\ZomatoUseCase\frontend"; npm run dev

```

Then open `http://localhost:5173` in your browser.

The frontend proxies API calls to the backend running on `localhost:8000`.

### 6. Run the Streamlit App (Phase 8)

In a separate terminal:

```bash
python -m pip install -r requirements-streamlit.txt
streamlit run streamlit_app.py
```

Then open `http://localhost:8501` in your browser.

This is a standalone, Python-only deployment path that runs the full recommendation pipeline (Phases 1–5) without requiring the FastAPI backend or React frontend. See [`docs/streamlit-deploy.md`](docs/streamlit-deploy.md) for Cloud deployment instructions.

## CLI Commands

| Command | Description |
|---------|-------------|
| `milestone1 info` | Project and runtime overview |
| `milestone1 doctor` | Environment and setup checks |
| `milestone1 ingest-smoke --limit N` | Load and normalize sample dataset records |
| `milestone1 prefs-parse ...` | Parse and validate user preferences |
| `milestone1 prompt-build ...` | Build LLM prompt payload from preferences |
| `milestone1 recommend ...` | Run end-to-end LLM recommendation (JSON output) |
| `milestone1 recommend-run ...` | Run end-to-end recommendation with readable output + telemetry |

## Backend API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API info |
| GET | `/api/v1/health` | Health check + Groq key status |
| GET | `/api/v1/metadata/cities` | Available locations from dataset |
| GET | `/api/v1/metadata/cuisines` | Available cuisines from dataset |
| POST | `/api/v1/recommendations` | Main recommendation flow |

Example:

```bash
curl -X POST "http://localhost:8000/api/v1/recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Delhi",
    "budget_band": "medium",
    "cuisines": ["North Indian"],
    "minimum_rating": 4.0,
    "additional_preferences": "family-friendly"
  }'
```

## Project Structure

```
.
├── docs/                    # Architecture and planning docs
├── src/
│   ├── phase0/              # CLI and foundations
│   ├── phase1/              # Data ingestion
│   ├── phase2/              # Preferences and validation
│   ├── phase3/              # Integration (filter + prompt)
│   ├── phase4/              # LLM recommendation engine
│   ├── phase5/              # Output rendering and telemetry
│   ├── phase6/              # Backend API service
│   │   └── api/
│   │       ├── routers/
│   │       │   ├── health.py
│   │       │   ├── metadata.py
│   │       │   └── recommendations.py
│   │       ├── schemas.py
│   │       ├── service.py
│   │       └── main.py
│   └── phase8/              # Streamlit deployment
├── frontend/                # React + Vite frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── PreferenceForm.jsx
│   │   │   ├── RestaurantCard.jsx
│   │   │   ├── RecommendationList.jsx
│   │   │   └── EmptyState.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── streamlit_app.py         # Streamlit Cloud entrypoint
├── requirements-streamlit.txt
├── requirements.txt
├── .streamlit/
│   └── config.toml
├── tests/                   # Unit and API tests
└── pyproject.toml
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Next Implementation Target

**Phase 9: Deployment, Hardening and Handoff** — Docker, CI/CD, rate limiting, and production readiness.
