# Streamlit Deployment Guide

This document covers how to run and deploy the **Phase 8 Streamlit app** — a lightweight, Python-only interface for the restaurant recommendation pipeline.

## Overview

The Streamlit app directly orchestrates Phases 1–5 (data ingestion, preference validation, filtering, LLM recommendation, and output display) inside a single Python process. No FastAPI backend or React frontend is required.

| File | Purpose |
|------|---------|
| `streamlit_app.py` | Root-level entrypoint for Streamlit Community Cloud |
| `src/phase8/app.py` | Core application logic (UI widgets + pipeline) |
| `requirements-streamlit.txt` | Local Streamlit dependencies |
| `requirements.txt` | Cloud deployment dependencies |
| `.streamlit/config.toml` | Streamlit server configuration |

---

## Local Development

### Prerequisites

- Python 3.10+
- `GROQ_API_KEY` environment variable (or `.env` file in repo root)

### 1. Install dependencies

```bash
python -m pip install -r requirements-streamlit.txt
```

This installs `streamlit` and the local package in editable mode (`-e .`).

### 2. Configure secrets

Copy `.env.example` to `.env` and add your key:

```bash
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. Launch the app

```bash
streamlit run streamlit_app.py
```

Or directly from the source folder:

```bash
streamlit run src/phase8/app.py
```

Open `http://localhost:8501` in your browser.

### 4. Verify a recommendation flow

1. Select a **Location** from the dropdown.
2. Choose a **Budget Band**.
3. (Optional) Pick **Preferred Cuisines**.
4. Adjust the **Minimum Rating** slider.
5. (Optional) Enter free-text hints in **Additional Preferences**.
6. Click **Get Recommendations**.

You should see:
- Filter/candidate count metrics
- Ranked restaurant cards with name, cuisine, rating, cost, and AI explanation
- Or an intentional empty-state message if no restaurants match

---

## Streamlit Community Cloud Deployment

### 1. Repository layout

Ensure your repo contains these files at the root:

```
.
├── streamlit_app.py
├── requirements.txt
├── .streamlit/
│   └── config.toml
├── src/
│   ├── phase1/
│   ├── phase2/
│   ├── phase3/
│   ├── phase4/
│   ├── phase8/
│   │   ├── __init__.py
│   │   └── app.py
│   └── ...
├── pyproject.toml
└── ...
```

### 2. Set secrets on Streamlit Cloud

1. Go to your app dashboard on [share.streamlit.io](https://share.streamlit.io).
2. Click **Settings** → **Secrets**.
3. Add:

```toml
GROQ_API_KEY = "gsk_xxxxxxxxxxxxxxxxxxxxxxxxxx"
```

4. Click **Save**.

The app reads `st.secrets["GROQ_API_KEY"]` automatically. Keys never leave the server-side process.

### 3. Deploy

1. Connect your GitHub repository to Streamlit Community Cloud.
2. Select the branch (e.g., `main`).
3. The default entrypoint is `streamlit_app.py` at the repo root.
4. Click **Deploy**.

After deployment, open the provided URL and complete one recommendation flow (or observe an intentional empty state) to confirm everything works.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: No module named 'streamlit'` | Streamlit not installed | `python -m pip install streamlit` or use `requirements-streamlit.txt` |
| `GROQ_API_KEY is not configured` | Missing key | Set it in `.env`, environment variable, or Streamlit Cloud Secrets |
| `Failed to load dataset` | Network issue or `datasets` not installed | Run `python -m pip install datasets` and check internet connection |
| Empty results every time | No restaurants match filters | Relax criteria (lower rating, clear cuisines, broader location) |
| Slow initial load | Hugging Face dataset download | Normal on first run; `st.cache_data` caches it for subsequent loads |
| LLM returns fallback rankings | Groq API error or timeout | Check `GROQ_API_KEY` validity and rate limits |

---

## Architecture Notes

- **No backend required:** The Streamlit app imports `phase1`–`phase4` directly and runs everything in-process.
- **Caching:** Dataset loading is cached with `@st.cache_data` to avoid repeated downloads.
- **Secret handling:** `GROQ_API_KEY` is resolved in this priority order:
  1. `st.secrets["GROQ_API_KEY"]` (Streamlit Cloud)
  2. `os.environ["GROQ_API_KEY"]` (local env / `.env`)
- **Complementary to Phase 7:** The React + FastAPI stack remains the primary product UI. The Streamlit app is intended for rapid prototyping, demos, and lightweight hosting.
