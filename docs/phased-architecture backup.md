## Phase-Wise Architecture: Restaurant Recommendation System

This document defines a phase-wise implementation plan aligned with the workflow in `docs/problemstatement.md`:

Data ingestion -> User input -> Integration (filter + prompt assembly) -> LLM recommendation -> Output display -> Backend API -> Frontend

## Phase 0: Scope and Foundations

### Goal
Establish clear project boundaries and setup standards before building core features.

### Key Decisions
- **Product slice:** Milestone 1 uses a basic web UI for user input and result display. CLI remains available for development and diagnostics.
- **Tech stack:** Finalize runtime, dependency manager, and secret handling strategy (`.env`, never committed).
- **Dataset contract:** Confirm supported Hugging Face fields for v1 and map dataset columns to internal model fields.
- **Non-goals:** Explicitly defer out-of-scope items (for example: user accounts, live Zomato API, maps).

### Exit Criteria
- Scope assumptions are documented.
- Supported preference fields are finalized.
- A local run path is defined for end-to-end execution after later phases are implemented.

### Implemented artifacts:
- `phase0-scope.md`
- `dataset-contract.md`
- `README.md`
- `.env.example`
- CLI diagnostics commands (for example: `milestone1 info`, `milestone1 doctor`)

## Phase 1: Data Ingestion and Canonical Model

### Goal
Create a reliable data layer that converts raw dataset records into a normalized internal schema.

### Core Responsibilities
- Acquire data(Download or stream) from `ManikaSaini/           zomato-restaurant-recommendation`; cache locally if useful for iteration.
- Normalize fields (ratings, costs, cuisines, missing values, duplicates).
- Define canonical `Restaurant` model with at least:
  - `name`
  - `location`
  - `cuisines`
  - `cost`
  - `rating`

### Exit Criteria
- A single ingestion module loads and returns typed restaurant records.
- Parsing behavior is covered by unit tests using sample dataset rows.

### Suggested Implementation
- package folder `src/milestone1/ingestion/`(Restaurant, load_restaurants / iter_restaurants, normalization, Hub revision pin, schema assertion).
- CLI: `milestone1 ingest-smoke --limit N`
- Hub integration tests: RUN_HF_INTEGRATION=1 pytest -m integration.

## Phase 2: User Preferences and Validation

### Goal
Convert raw user input into a validated preference object used by downstream logic.

### Core Responsibilities
- Define a `UserPreferences` model with Structured fields:
  - `location`
  - `budget_band`
  - `cuisines`
  - `minimum_rating`
  - optional free-text for `additional_preferences`
- Validate and coerce input where appropriate like(unknown location, rating out of range).
- Return clear error messages for the UI/CLI, user-friendly validation errors.

### Exit Criteria
- Preferences from UI/API/CLI deserialize into one standard object used by the filter layer.
- Invalid inputs are rejected with actionable error messages.

### Suggested Implementation
- package folder `src/milestone1/preferences/`(UserPreferences, preferences_from_mapping, optional allowed_city_names corpus check, allowed_cities_from_restaurants).
- CLI parser command for quick local validation
- CLI: milestone1 prefs-parse ... (prints JSON or field errors on stderr).

## Phase 3: Integration Layer (Retrieval + Prompt Assembly)

### Goal
Build deterministic candidate retrieval and prepare high-quality LLM context.

### Core Responsibilities
- Apply rule-based filters (location, rating, budget, cuisine overlap).
- Shortlist top-N candidates for prompt context (cap for LLM context, e.g.   15-50).
- Optionally pre-sort candidates using rating or a composite score so the LLM sees a sensible default order even before reasoning.
- Build System + user messages(or single structured prompt) payload containing:
  - User preferences as JSON or bullets;
  - candidate table as markdown/JSON;
  - Output format rules(see Phase 4).
  - instructions to only recommend from the list.

### Exit Criteria
- Given preferences and loaded data, system outputs stable `candidates[]` and `prompt_payload` without calling the LLM yet.
- filter Edge cases are tested (`no matches`, `too many matches`, partial filters).

### Implemented
-package `src/milestone1/phase3_integration/` (filter_and_rank, build_prompt_payload, build_integration_output). 
-CLI: milestone1 prompt-build.

## Phase 4: Recommendation Engine (LLM)

### Goal
Generate grounded, explainable recommendations from shortlisted candidates.

### Core Responsibilities
- Implement a thin LLM client (temperature, max tokens, timeout, API key via env).
- Enforce grounding: Prompt requires the model to cite restaurant names from the candidate list only; refuse or return empty if nothing fits.
- Require structured output (prefer JSON) for reliable parsing (e.g. rankings[] with restaurant_id, rank, explanation) or strict markdown sections—then parse and validate.
- Add resilience:
  - Retry transient failures
  - Fallback to deterministic top-K with template explanations if LLM fails

### Exit Criteria
- End-to-end recommendation returns ranked items with explanations.
- Response parsing validates structure and handles malformed outputs gracefully.

### Implemented
-package `src/milestone1/phase4_llm/` (Groq OpenAI-compatible client, JSON rankings parse, deterministic fallback, recommend_with_groq). 
-CLI: milestone1 recommend. 

## Phase 5: Output and User Experience

### Goal
Present recommendations in a clear and useful format for end users.

### Core Responsibilities
- Render each recommendation with:
  - Restaurant name
  - Cuisine
  - Rating
  - Estimated cost
  - AI explanation(per problem statement).
- Differentiate empty states:
  - No candidates after filtering
  - LLM failed to produce valid ranked output
- Add lightweight observability (Log latency, filter counts(no PII in logs unless required), optional token usage).

### Exit Criteria
- Complete demo flow from input to readable recommendation output works in one run.
- Display format matches `docs/problemstatement.md` requirements.

### Implemented
-package `src/milestone1/phase5_output/` (markdown/plain rendering, empty-state copy, stderr telemetry JSON).
-CLI: milestone1 recommend-run (end-to-end readable output + telemetry).

## Phase 6: Backend API Service

### Goal
Expose the core recommendation pipeline as a robust, stateless REST API that the frontend and other clients can consume.

### Core Responsibilities
- Wrap Phases 1-5 into callable service logic with clear interfaces.
-Thin HTTP service that owns server-side secrets (GROQ_API_KEY), dataset access, and orchestration. The browser must not call Groq or Hugging Face directly.

- Define Stable JSON request/response schemas (Pydantic models) for:
  - `UserPreferences` input
  - `RecommendationResult` output
  - Error envelopes
  -preferences body aligned with Phase 2 keys; 
  -response carries ranked items (ids + display fields + explanations),
  - source (llm / fallback / no_candidates), filter/candidate counts, and optional non-sensitive telemetry fields for the UI.

- Implement HTTP endpoints:
  - `POST /api/v1/recommendations` (or equivalent) — validate input, run load_restaurants (with limits/caching policy), recommend_with_groq, return DTOs.  — main recommendation flow
  - `GET /api/v1/health` — process up, keys configured (without exposing values) — health check
  - `GET /api/v1/metadata/cities` — available locations
  - `GET /api/v1/metadata/cuisines` — available cuisines
  - e.g. sample allowed_cities cap for form hints.

- Handle cross-cutting concerns:
  - CORS restricted to the dev frontend origin(s)
  - request size limits on free-text fields (reuse Phase 2 max length).
  - Timeouts aligned with Phase 4; structured server logs (counts, latency, token totals—no raw user notes in info-level logs unless you explicitly choose to)
  - Request validation and structured error responses
  - Async/non-blocking LLM calls (FastAPI background tasks or async await)
  - Graceful degradation when LLM or dataset is unavailable
- Add OpenAPI/Swagger auto-documentation.

- Stack:
 -Python-first is natural: e.g. FastAPI or Flask in src/ or a sibling package, sharing the installed milestone1 library.
 - Alternative stacks (Node, etc.) are possible only if they duplicate contracts and call a Python sidecar—avoid unless required.


### Exit Criteria
- frontend can complete one recommendation flow using only the API;
- API returns the same logical outcomes as milestone1 recommend / recommend-run for the same inputs (modulo caching).
- Frontend can send preferences JSON and receive ranked recommendations over HTTP.
- API contract is versioned and documented.
- All endpoints have unit/integration tests.

### Suggested Implementation
- `backend/` folder at repo root (FastAPI + Uvicorn).
- Service module: `backend/app/recommendation_service.py` orchestrates Phases 1-5.
- Routers: `backend/app/routers/recommendations.py`, `backend/app/routers/metadata.py`.
- Startup script: `python -m backend.main` or `uvicorn backend.main:app --reload`.
- document target layout here when added (e.g. src/milestone1/api/ or apps/api/).



## Phase 7: Frontend (Web UI)

### Goal
Provide an intuitive, responsive web interface that captures user preferences and presents AI-powered recommendations.

### Core Responsibilities
- Preference capture:
  - Location selector (dropdown or autocomplete)
  - Budget band selector (low / medium / high)
  - Cuisine multi-select
  - Minimum rating slider
  - Free-text additional preferences
  - Primary user-facing surface:preference form + results list

- Data flow:
  -Browser only talks to the Phase 6 API. Map form fields to the API JSON schema (location, budget band, cuisines, minimum rating, optional additional text).

- Results display:
  - Restaurant cards with name, cuisine, rating, cost, and AI explanation
  - Ranked list with visual hierarchy
  - Empty-state messaging (no matches, LLM failure)
  - reuse Phase 5 empty-state semantics (“no filter match” vs “model returned no grounded picks”) with clear, distinct copy.

- UX polish:
  - Loading skeletons/spinners during LLM call
  - Form validation with user-friendly errors
  - Responsive layout (mobile + desktop)
  - Loading states, validation errors inline, disabled submit while pending; optional “copy as Markdown” for demo.

- Error handling:
  - Network errors, backend timeouts, malformed responses

- Stack:
  -Choose one and stay consistent: e.g. React + Vite (SPA) or Next.js or HTMX + server templates. Host locally for milestone 1; no production SLA required in Phase 0.

### Exit Criteria
- End-to-end demo works entirely through the browser without CLI.
- UI matches `docs/problemstatement.md` display requirements.
- Frontend communicates only with the backend API, never directly with the LLM or dataset.
- one demo path in the README: start API + UI, submit preferences, see ranked results or an intentional empty state.

### Suggested Implementation
- `frontend/` folder at repo root (React + Vite or Next.js).
- Key components:
  - `PreferenceForm.jsx`
  - `RecommendationList.jsx`
  - `RestaurantCard.jsx`
  - `EmptyState.jsx`
- State management: React hooks or lightweight store (Zustand/Context).
- Styling: Tailwind CSS or similar utility-first framework.
- Proxy config for local dev to reach `localhost:8000`.
- README section “Run the web app


## Phase 8: Deployment, Hardening and Handoff

### Goal
Prepare the full-stack system for production reliability, maintainability, and team handoff.

### Core Responsibilities
- Add automated tests for:
  - Filter logic
  - Prompt payload shape
  - JSON parsing (fixtures with fake LLM responses)
  - API contract (use pytest + TestClient for FastAPI),(golden JSON for happy/empty/error paths)
  - Frontend component rendering (Vitest or React Testing Library).
- Improve documentation README:
  - Setup and run instructions (backend + frontend)
  - Environment variables (`.env` template for both stacks)
  - Architecture decision records (ADRs)
  - Known limitations
  - install, set GROQ_API_KEY, run API + UI, CLI fallbacks, and limitations (dataset revision, rate limits, candidate cap).
- Production readiness:
  - Containerization (`Dockerfile` for backend, optional for frontend)
  - `docker-compose.yml` for one-command local stack
  - Log aggregation and structured logging
  - Basic rate limiting on `/recommend`
- Document performance trade-offs / cost-latency notes:
  - Candidate cap
  - Model selection
  - Caching strategy (Redis for dataset or LLM responses)
  - model id, when to raise load limits, caching strategy for repeated queries (optional in-process LRU of recent Hub windows—only if measured need).

### Exit Criteria
- Project is reproducible for a new developer with `docker-compose up`.
- Known risks and operational constraints are documented.
- CI pipeline runs lint, test, and build for both backend and frontend.

## Phase Dependencies

- Phases 0-2 can run in partial parallel(e.g. stub UI while data loads).
- Phase 3 should be completed before deep LLM tuning.
- Phase 4 should not own business filtering rules that belong in Phase 3.
- Phase 5 depends on a stable payload from Phases 3 and 4.
- Phase 6 (Backend) depends on a stable engine from Phases 0-5.
- Phase 7 (Frontend) depends on the Backend API contract defined in Phase 6.
- Phase 8 runs continuously but is finalized after the full stack stabilizes.

## Traceability to Problem Statement

| Problem Statement Section | Primary Phase |
| --- | --- |
| Data ingestion | 1 |
| User input | 2 |
| Integration layer | 3 |
| Recommendation engine | 4 |
| Output display | 5 |
| Backend API | 6 |
| Frontend UI | 7 |

This architecture supports phase-wise for planning and milestone-based delivery while preserving a clean runtime layering:

Data -> Rules -> Model -> Presentation -> API -> Frontend -> Feedback