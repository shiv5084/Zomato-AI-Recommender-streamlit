# Edge Cases: AI-Powered Restaurant Recommendation System

This document lists detailed edge cases for the Zomato-inspired recommendation system, based on:

- `docs/problemstatement.md`
- `docs/phased-architecture.md`

It is organized phase-wise so each case can be traced to architecture responsibilities and test plans.

## How to Use This Document

For every edge case, define:

- **Detection:** how the system identifies the case
- **Expected behavior:** what the user should see
- **Handling strategy:** fallback, retry, or validation logic
- **Test coverage:** unit/integration/e2e test type

---

## Phase 0: Scope and Foundations

### 0.1 Configuration and Environment
- Missing `.env` file or missing API key.
- Invalid API key format or expired key.
- Wrong model/provider name configured.
- App runs in one environment (CLI) but fails in another (web/API) due to config mismatch.

**Expected behavior:** Fail fast with actionable startup error; do not crash mid-request.

### 0.2 Dependency and Runtime Mismatch
- Different Python/Node runtime than documented.
- Dependency lock mismatch causing parser or client failures.
- Optional integrations treated as required (for example, telemetry).

**Expected behavior:** Clear install diagnostics (`doctor` command) and startup compatibility checks.

### 0.3 Scope Creep Edge Cases
- Requests for unsupported features (accounts, maps, live APIs) appear in free-text input.
- Team accidentally starts implementing non-goals, delaying core flow.

**Expected behavior:** Keep non-goals explicitly documented and enforced in milestones.

---

## Phase 1: Data Ingestion and Canonical Model

### 1.1 Dataset Access and Freshness
- Hugging Face dataset unreachable (network outage, rate limit, DNS issue).
- Dataset revision changes silently; schema drifts.
- Partial download or corrupted local cache.

**Handling strategy:**
- Retry with backoff for transient fetch failures.
- Pin dataset revision/version.
- Validate checksum/row counts when possible.
- Fall back to last known good cached snapshot.

### 1.2 Schema and Type Issues
- Missing required columns (`name`, `location`, `rating`, etc.).
- Rating represented as text (`"4.2/5"`, `"NEW"`, `"N/A"`).
- Cost in mixed formats/currencies (`₹800 for two`, `1000`, empty).
- Cuisine as a single string with separators or malformed list.

**Expected behavior:** Normalize aggressively where safe; reject rows that cannot be trusted.

### 1.3 Data Quality and Consistency
- Duplicate restaurants with slight name differences.
- Same restaurant in multiple localities with conflicting ratings/cost.
- Outlier ratings/cost (negative, impossible high values).
- Empty location/cuisine causing unfilterable records.

**Handling strategy:**
- Deduplicate with deterministic keys and tie-break rules.
- Apply bounds validation on numeric fields.
- Track rejected rows and reasons for observability.

### 1.4 Encoding and Locale
- Non-ASCII restaurant names/cuisines break parsing or sorting.
- Location spellings vary (`Bengaluru` vs `Bangalore`).

**Expected behavior:** Preserve Unicode safely and maintain alias mapping for location normalization.

---

## Phase 2: User Preferences and Validation

### 2.1 Missing or Ambiguous Inputs
- User submits form with no location.
- User provides only free-text preference with no structured fields.
- Cuisine is empty but user expects recommendations.

**Expected behavior:** Prompt for required fields, apply sensible defaults only when explicit.

### 2.2 Invalid Range/Type
- Minimum rating below 0 or above allowed max.
- Budget value outside supported bands (`low/medium/high`).
- Numeric fields sent as strings with spaces or symbols.

**Handling strategy:** Coerce where safe; otherwise block with field-level error messages.

### 2.3 Conflicting Preferences
- Low budget + very high minimum rating + rare cuisine in small city.
- Vegetarian-only + seafood-only in same request.

**Expected behavior:** Explain conflict clearly and suggest which constraint to relax.

### 2.4 Input Normalization
- Case and whitespace variation (`  delhi  `, `ITALIAN`).
- Synonyms (`north indian` vs `north-indian`, `veg` vs `vegetarian`).
- Spelling mistakes in location/cuisine.

**Handling strategy:** Normalize case/spacing, support synonyms, and optionally suggest closest valid values.

### 2.5 Abuse and Safety
- Prompt-injection style text in additional preferences (`ignore above filters...`).
- Extremely long free-text input causing prompt bloat.

**Expected behavior:** Sanitize and truncate free-text; never let free-text override system constraints.

---

## Phase 3: Integration Layer (Retrieval + Prompt Assembly)

### 3.1 Filtering Edge Cases
- Zero candidates after applying hard filters.
- Too many candidates (prompt context overflow).
- All candidates missing one key field (cost/rating/cuisine).

**Handling strategy:**
- If zero: return graceful empty state + relaxation suggestions.
- If too many: deterministic top-N cap.
- Exclude low-quality records before prompt assembly.

### 3.2 Determinism and Stability
- Same query produces different candidate sets due to unstable ordering.
- Floating-point ties in scoring produce random order.

**Expected behavior:** Use stable sorting with secondary keys (rating, reviews, name/id).

### 3.3 Prompt Construction Failures
- Prompt exceeds token budget.
- Candidate table malformed JSON/Markdown.
- Missing instruction that recommendations must come only from shortlist.

**Handling strategy:**
- Enforce strict prompt budget with truncation policy.
- Validate prompt payload schema before model call.
- Include hard grounding instructions every time.

### 3.4 Data Leakage Risks
- Internal fields (debug flags, raw metadata) accidentally sent to LLM.
- PII accidentally included in prompt from logs/context.

**Expected behavior:** Prompt allowlist for fields; blocklist sensitive/internal attributes.

---

## Phase 4: Recommendation Engine (LLM)

### 4.1 Provider/API Failures
- Timeout, 429 rate limit, 5xx server errors.
- Authentication errors due to invalid/rotated key.
- Network disruptions during completion.

**Handling strategy:**
- Retry idempotent requests with exponential backoff.
- Distinguish retryable vs non-retryable errors.
- Fall back to deterministic ranking with template explanation.

### 4.2 Ungrounded or Hallucinated Output
- LLM recommends restaurants not in candidate list.
- LLM fabricates ratings/costs.
- LLM ignores budget/rating constraints.

**Expected behavior:** Post-validate response against candidate set; reject invalid items and re-ask or fallback.

### 4.3 Structured Output Violations
- Invalid JSON (trailing commas, prose mixed with JSON).
- Missing required keys (`restaurant_id`, `rank`, `explanation`).
- Duplicate ranks or duplicate restaurant IDs.

**Handling strategy:** Parse with strict schema validation; auto-repair only if deterministic; otherwise fallback.

### 4.4 Quality and Explainability Issues
- Explanations are generic and not preference-specific.
- Top-ranked item has weaker fit than lower-ranked item.
- Offensive/unsafe language in generated explanation.

**Expected behavior:** Quality checks for relevance, grounding, and safety before rendering.

### 4.5 Cost and Latency
- Large candidate sets cause high token usage and slow responses.
- Concurrent users trigger quota exhaustion.

**Handling strategy:** Cap candidate size, cache frequent queries, and track token/latency metrics.

---

## Phase 5: Output and User Experience

### 5.1 Rendering and Formatting
- Missing fields in final payload (no cuisine/cost).
- Overly long explanation breaks UI layout.
- Unicode/special characters render incorrectly.

**Expected behavior:** Render placeholders (`N/A`), truncate with expand option, and ensure encoding-safe UI.

### 5.2 Empty and Partial States
- No restaurants match filters.
- LLM fails but fallback ranking is available.
- Only partial recommendation list returned.

**Expected behavior:** Different, clear messages per case; never show raw stack traces to users.

### 5.3 Consistency Across Interfaces
- CLI and web UI show different ranking for same input.
- API response format diverges from UI contract.

**Handling strategy:** Single shared response formatter and contract tests.

### 5.4 Observability Gaps
- Request fails but no logs connect failure point.
- Logs include sensitive user details.

**Expected behavior:** Correlation IDs, structured logs, and no PII unless explicitly required.

---

## Phase 6: Hardening and Handoff

### 6.1 Test Coverage Gaps
- Happy-path tests pass; edge-path logic untested.
- No fixtures for malformed LLM responses.
- No regression tests for known bug cases.

**Expected behavior:** Add targeted unit/integration tests for each phase edge case cluster.

### 6.2 Documentation Drift
- README commands outdated after refactor.
- Env var names changed but docs unchanged.
- Unsupported behavior accidentally documented as supported.

**Handling strategy:** Release checklist includes docs validation and smoke run.

### 6.3 Operational Readiness
- App works locally but fails in clean environment.
- No monitoring thresholds for latency/error rates.

**Expected behavior:** Reproducible setup with baseline SLO-style operational targets.

---

## Cross-Phase Critical Edge Cases

These require end-to-end handling across multiple phases:

1. **No-match query**
   - Filters return zero candidates.
   - System should avoid calling LLM unnecessarily.
   - UI should suggest relaxing one or more constraints.

2. **LLM unavailable at runtime**
   - Retrieval works, model fails.
   - Return deterministic top-K with transparent fallback messaging.

3. **Schema drift in source dataset**
   - Ingestion fails or silently mis-maps fields.
   - Detection should block release pipeline and trigger contract update.

4. **Prompt injection through additional preferences**
   - User text attempts to override rules.
   - System and parser must enforce shortlist-only recommendations.

5. **Token overflow due to large candidate context**
   - Prompt too large for model window.
   - Apply candidate capping + compact prompt templates.

6. **Inconsistent results across interfaces**
   - Same input differs between CLI/web/API due to duplicated logic.
   - Centralize filtering, ranking validation, and response formatting.

---

## Suggested Test Matrix (Minimal)

- **Unit tests**
  - Field normalization (rating/cost/cuisine/location)
  - Preference validation and coercion
  - Filtering behavior for no-match and tie-break scenarios
  - Prompt payload schema and size checks
  - LLM response parser (valid, malformed, ungrounded)

- **Integration tests**
  - Dataset load + canonical mapping
  - End-to-end pipeline with mocked LLM
  - Retry/fallback behavior under simulated API errors

- **E2E tests**
  - Valid user query with grounded recommendations
  - Conflicting preferences flow with guidance
  - LLM outage fallback rendered correctly

---

## Acceptance Criteria for Edge-Case Readiness

The system is edge-case ready when:

- Every phase has explicit failure handling and user-facing behavior.
- No known failure path results in an unhandled exception.
- LLM outputs are always validated before display.
- Empty states are informative and actionable.
- Logs are useful for debugging without exposing secrets/PII.
- Regression tests exist for previously encountered failures.
