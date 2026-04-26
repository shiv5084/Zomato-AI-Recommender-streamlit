"""Metadata router for cities and cuisines."""

from fastapi import APIRouter

from phase6.api.schemas import MetadataResponse
from phase6.api.service import get_cities, get_cuisines

router = APIRouter(tags=["metadata"])


@router.get("/api/v1/metadata/cities", response_model=MetadataResponse)
def list_cities() -> MetadataResponse:
    """Return available locations from the dataset."""
    return MetadataResponse(items=get_cities())


@router.get("/api/v1/metadata/cuisines", response_model=MetadataResponse)
def list_cuisines() -> MetadataResponse:
    """Return available cuisines from the dataset."""
    return MetadataResponse(items=get_cuisines())
