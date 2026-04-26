# Dataset Contract (Phase 0)

## Source

- Provider: Hugging Face
- Dataset ID: `ManikaSaini/zomato-restaurant-recommendation`
- Configurable via environment:
  - `HF_DATASET_ID`
  - `HF_DATASET_REVISION`

## Contract Purpose

Define the minimum fields required by milestone 1 and the canonical internal mapping expected by ingestion and filtering layers.

## Required Canonical Fields

The system expects each restaurant record to contain:

- `name` (string)
- `location` (string)
- `cuisines` (list of strings)
- `cost` (normalized numeric or budget band source)
- `rating` (float in normalized range)

## Suggested Source-to-Canonical Mapping

Because public datasets may vary, ingestion must map source columns defensively:

- Restaurant name-like field -> `name`
- City/locality/address-like field -> `location`
- Cuisine/categories text -> `cuisines`
- Cost-for-two/average-cost-like field -> `cost`
- Aggregate rating/vote score field -> `rating`

## Normalization Rules (Planned for Phase 1)

- Trim whitespace and normalize casing for text fields.
- Convert cuisine text to a list using robust separators.
- Parse rating values into numeric form; reject invalid values.
- Parse cost into comparable numeric or band representation.
- Reject rows missing critical fields (`name`, `location`).

## Validation Expectations

- Contract check runs during ingestion startup.
- If required fields are not mappable, ingestion fails with a clear error.
- Rejected rows are counted and logged with reason categories.

## Versioning

- Pin dataset revision in runtime config for reproducibility.
- Update this contract when new canonical fields are introduced.
