from collections.abc import Mapping, Sequence

from phase1.ingestion import Restaurant, load_restaurants

from .types import BudgetBand, UserPreferences, ValidationError

ALLOWED_BUDGET_BANDS: tuple[BudgetBand, ...] = ("low", "medium", "high")
RATING_MIN = 0.0
RATING_MAX = 5.0


def _normalize_text(value: object) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def _normalize_budget(value: object) -> BudgetBand:
    budget = _normalize_text(value).lower()
    aliases = {
        "l": "low",
        "m": "medium",
        "h": "high",
    }
    budget = aliases.get(budget, budget)
    if budget not in ALLOWED_BUDGET_BANDS:
        raise ValidationError(
            f"Invalid budget_band '{value}'. Allowed values: {', '.join(ALLOWED_BUDGET_BANDS)}"
        )
    return budget  # type: ignore[return-value]


def _normalize_cuisines(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw = value.replace("|", ",").replace("/", ",")
        cuisines = [part.strip() for part in raw.split(",")]
    elif isinstance(value, Sequence):
        cuisines = [_normalize_text(v) for v in value]
    else:
        raise ValidationError("cuisines must be a string or list of strings")

    lowered = {c.lower(): c for c in cuisines if c}
    # Return deduplicated cuisines preserving lowercase normalization.
    return [text.title() for text in sorted(lowered.keys())]


def _normalize_rating(value: object) -> float:
    if value is None or _normalize_text(value) == "":
        return RATING_MIN
    try:
        rating = float(str(value).strip())
    except ValueError as exc:
        raise ValidationError(f"minimum_rating must be a number, got '{value}'") from exc

    if rating < RATING_MIN or rating > RATING_MAX:
        raise ValidationError(f"minimum_rating must be between {RATING_MIN} and {RATING_MAX}")
    return round(rating, 2)


def _normalize_location(value: object, allowed_city_names: set[str] | None = None) -> str:
    location = _normalize_text(value)
    if not location:
        raise ValidationError("location is required")
    if allowed_city_names:
        if location.lower() not in allowed_city_names:
            raise ValidationError(
                f"Unknown location '{location}'. Provide a known city/locality from the dataset."
            )
    return location


def preferences_from_mapping(
    raw: Mapping[str, object],
    allowed_city_names: set[str] | None = None,
) -> UserPreferences:
    location = _normalize_location(raw.get("location"), allowed_city_names=allowed_city_names)
    budget = _normalize_budget(raw.get("budget_band", "medium"))
    cuisines = _normalize_cuisines(raw.get("cuisines"))
    min_rating = _normalize_rating(raw.get("minimum_rating", 0))
    additional = _normalize_text(raw.get("additional_preferences")) or None

    return UserPreferences(
        location=location,
        budget_band=budget,
        cuisines=cuisines,
        minimum_rating=min_rating,
        additional_preferences=additional,
    )


def allowed_cities_from_restaurants(restaurants: Sequence[Restaurant]) -> set[str]:
    return {r.location.lower() for r in restaurants if r.location}


def allowed_city_names_from_dataset(limit: int = 5000) -> set[str]:
    restaurants = load_restaurants(limit=limit)
    return allowed_cities_from_restaurants(restaurants)
