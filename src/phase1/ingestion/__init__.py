"""Phase 1 ingestion package."""

from .loader import iter_restaurants, load_restaurants
from .models import Restaurant

__all__ = ["Restaurant", "iter_restaurants", "load_restaurants"]
