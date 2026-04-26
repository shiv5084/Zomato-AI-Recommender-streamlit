# Phase 0 Scope and Foundations

## Goal

Establish project boundaries, baseline tooling, and repeatable setup before implementing data and recommendation logic.

## Product Slice for Milestone 1

- A basic web UI will be the source of user input in milestone 1.
- The same web UI will be the primary user-facing surface for result display.
- CLI remains available for developer diagnostics and setup checks.
- Initial recommendation flow will support core preferences only:
  - location
  - budget band
  - cuisine
  - minimum rating
  - optional additional preferences text

## Technical Decisions

- Runtime: Python 3.10+
- Package layout: `src/` structure
- Dependency management: `pip` with `pyproject.toml`
- Secrets: `.env` (excluded from version control), with `.env.example` template

## Supported Inputs (v1)

- Location: city-level input
- Budget: low/medium/high
- Cuisine: one or multiple values
- Minimum rating: numeric threshold
- Additional preferences: optional free-text hint

## Non-Goals for Milestone 1

- User authentication and profiles
- Live Zomato APIs
- Map integration
- Advanced personalization/history-aware recommendations
- Multi-tenant or production deployment automation

## Exit Criteria Checklist

- [x] Scope and non-goals documented
- [x] Tech baseline finalized
- [x] Environment variable template provided
- [x] Local diagnostics commands available (`milestone1 info`, `milestone1 doctor`)
- [x] Local project run path documented in `README.md`
