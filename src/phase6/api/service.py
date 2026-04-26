"""Backend service orchestrating Phases 1-5 of the recommendation pipeline."""

import logging
import os
import time
from typing import Literal

from phase1.ingestion.loader import load_restaurants
from phase1.ingestion.models import Restaurant
from phase2.preferences.service import preferences_from_mapping, ValidationError, allowed_cities_from_restaurants
from phase3.integration.pipeline import build_integration_output
from phase4.llm.engine import recommend_with_groq

from phase6.api.schemas import PreferencesRequest, RecommendationResult, RankingItem, RestaurantDto

logger = logging.getLogger(__name__)

# In-memory cache for loaded restaurants to avoid repeated Hugging Face calls.
_restaurants_cache: list[Restaurant] | None = None
_CACHE_LIMIT = 5000


def _get_restaurants() -> list[Restaurant]:
    """Load restaurants from the dataset with caching."""
    global _restaurants_cache
    if _restaurants_cache is None:
        logger.info("Loading restaurants from dataset (limit=%s)...", _CACHE_LIMIT)
        _restaurants_cache = load_restaurants(limit=_CACHE_LIMIT)
        logger.info("Loaded %d restaurants.", len(_restaurants_cache))
    return _restaurants_cache


def _build_ranking_dtos(rankings: list[dict]) -> list[RankingItem]:
    """Convert raw ranking dictionaries to Pydantic DTOs."""
    dtos = []
    for item in rankings:
        rest = item.get("restaurant", {})
        dto = RankingItem(
            restaurant_id=item.get("restaurant_id", ""),
            rank=item.get("rank", 0),
            explanation=item.get("explanation", "No explanation provided."),
            restaurant=RestaurantDto(
                id=rest.get("id", ""),
                restaurant_name=rest.get("restaurant_name", "Unknown"),
                city=rest.get("city", ""),
                cuisines=rest.get("cuisines", []),
                rating=rest.get("rating"),
                approx_cost_for_two_inr=rest.get("approx_cost_for_two_inr"),
                budget_band=rest.get("budget_band", "unknown"),
            ),
        )
        dtos.append(dto)
    return dtos


def get_recommendations(request: PreferencesRequest) -> RecommendationResult:
    """
    Run the full recommendation pipeline.

    1. Load restaurants (cached).
    2. Parse and validate preferences.
    3. Filter and rank candidates.
    4. Call LLM (with fallback).
    5. Build response DTOs and telemetry.
    """
    telemetry = {
        "latency_ms": {},
        "counts": {},
    }

    t0 = time.time()
    restaurants = _get_restaurants()
    telemetry["latency_ms"]["load_restaurants"] = round((time.time() - t0) * 1000, 2)
    telemetry["counts"]["total_restaurants"] = len(restaurants)

    # Build preferences (with dataset-backed location validation)
    t0 = time.time()
    allowed_cities = allowed_cities_from_restaurants(restaurants)
    try:
        prefs = preferences_from_mapping(request.model_dump(), allowed_city_names=allowed_cities)
    except ValidationError as exc:
        logger.warning("Preference validation failed: %s", exc)
        raise
    telemetry["latency_ms"]["validate_preferences"] = round((time.time() - t0) * 1000, 2)

    # Integration: filter + prompt
    t0 = time.time()
    integration_output = build_integration_output(restaurants, prefs, top_n=15)
    candidates = integration_output["candidates"]
    prompt_payload = integration_output["prompt_payload"]
    telemetry["latency_ms"]["filter_and_rank"] = round((time.time() - t0) * 1000, 2)
    telemetry["counts"]["candidate_count"] = len(candidates)

    if not candidates:
        return RecommendationResult(
            rankings=[],
            source="no_candidates",
            filter_count=len(restaurants),
            candidate_count=0,
            telemetry=telemetry,
        )

    # LLM recommendation
    t0 = time.time()
    try:
        rankings = recommend_with_groq(prompt_payload, candidates, top_n=5)
        source: Literal["llm", "fallback", "no_candidates"] = "llm"
    except Exception as exc:
        logger.exception("LLM recommendation failed: %s", exc)
        rankings = []
        source = "no_candidates"
    telemetry["latency_ms"]["recommend"] = round((time.time() - t0) * 1000, 2)

    # Detect fallback: if rankings came from fallback, engine.py already returns them.
    # We can detect fallback by checking if explanations contain "fallback".
    if rankings and any("fallback" in r.get("explanation", "") for r in rankings):
        source = "fallback"

    if not rankings:
        source = "no_candidates"

    ranking_dtos = _build_ranking_dtos(rankings)

    return RecommendationResult(
        rankings=ranking_dtos,
        source=source,
        filter_count=len(restaurants),
        candidate_count=len(candidates),
        telemetry=telemetry,
    )


def get_cities() -> list[str]:
    """Return sorted list of unique city names from the dataset."""
    restaurants = _get_restaurants()
    cities = sorted({r.location for r in restaurants if r.location})
    return cities


def get_cuisines() -> list[str]:
    """Return sorted list of unique cuisines from the dataset."""
    restaurants = _get_restaurants()
    cuisine_set: set[str] = set()
    for r in restaurants:
        for c in r.cuisines:
            if c:
                cuisine_set.add(c)
    return sorted(cuisine_set)


def is_groq_configured() -> bool:
    """Check whether GROQ_API_KEY is present without exposing its value."""
    return bool(os.getenv("GROQ_API_KEY"))
