"""Recommendation router."""

from fastapi import APIRouter, HTTPException

from phase6.api.schemas import PreferencesRequest, RecommendationResult
from phase6.api.service import get_recommendations
from phase2.preferences.service import ValidationError

router = APIRouter(tags=["recommendations"])


def _extract_field_from_message(message: str) -> str | None:
    message_lower = message.lower()
    for field in ("budget_band", "minimum_rating", "location", "cuisines"):
        if field in message_lower:
            return field
    return None


@router.post("/api/v1/recommendations", response_model=RecommendationResult)
def recommend(request: PreferencesRequest) -> RecommendationResult:
    """
    Submit user preferences and receive AI-powered restaurant recommendations.

    The endpoint runs the full pipeline: load data, filter candidates,
    call the LLM, and return ranked results with explanations.
    """
    try:
        result = get_recommendations(request)
    except ValidationError as exc:
        detail = [
            {
                "field": _extract_field_from_message(str(exc)),
                "message": str(exc),
                "type": "validation_error",
            }
        ]
        raise HTTPException(status_code=422, detail=detail)
    return result
