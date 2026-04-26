"""Pydantic schemas for the Backend API."""

from pydantic import BaseModel, Field
from typing import Literal


class PreferencesRequest(BaseModel):
    """User preferences submitted to the recommendation endpoint."""

    location: str = Field(..., description="City or locality to search in")
    budget_band: Literal["low", "medium", "high"] = Field(
        ..., description="Budget band: low, medium, or high"
    )
    cuisines: list[str] = Field(default_factory=list, description="Preferred cuisines")
    minimum_rating: float = Field(
        default=0.0, ge=0.0, le=5.0, description="Minimum acceptable rating (0-5)"
    )
    additional_preferences: str | None = Field(
        default=None, description="Optional free-text preferences"
    )


class RestaurantDto(BaseModel):
    """Restaurant data transfer object for API responses."""

    id: str
    restaurant_name: str
    city: str
    cuisines: list[str]
    rating: float | None
    approx_cost_for_two_inr: float | None
    budget_band: str


class RankingItem(BaseModel):
    """A single ranked recommendation."""

    restaurant_id: str
    rank: int
    explanation: str
    restaurant: RestaurantDto


class RecommendationResult(BaseModel):
    """Full response from the recommendation endpoint."""

    rankings: list[RankingItem]
    source: Literal["llm", "fallback", "no_candidates"]
    filter_count: int = Field(
        ..., description="Total number of restaurants loaded from dataset"
    )
    candidate_count: int = Field(
        ..., description="Number of candidates after applying filters"
    )
    telemetry: dict | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    groq_configured: bool


class MetadataResponse(BaseModel):
    """Metadata response for cities or cuisines."""

    items: list[str]
