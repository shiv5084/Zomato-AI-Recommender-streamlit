"""Health check router."""

from fastapi import APIRouter

from phase6.api.schemas import HealthResponse
from phase6.api.service import is_groq_configured

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return API health status and whether required secrets are configured."""
    return HealthResponse(
        status="ok",
        groq_configured=is_groq_configured(),
    )
