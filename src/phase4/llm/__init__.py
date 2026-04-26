"""Phase 4: Recommendation Engine (LLM)"""

from .engine import recommend_with_groq
from .fallback import deterministic_fallback
from .parser import parse_rankings

__all__ = ["recommend_with_groq", "deterministic_fallback", "parse_rankings"]
