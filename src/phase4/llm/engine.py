import logging
from phase4.llm.client import call_groq_model
from phase4.llm.parser import parse_rankings
from phase4.llm.fallback import deterministic_fallback

logger = logging.getLogger(__name__)

def recommend_with_groq(prompt_payload: dict, candidates: list, top_n: int = 5) -> list[dict]:
    """
    Execute the recommendation using Groq LLM.
    Returns a list of ranking dictionaries (max top_n items).
    """
    if not candidates:
        return []

    messages = prompt_payload.get("messages", [])
    
    try:
        response_text = call_groq_model(messages)
        rankings = parse_rankings(response_text)
        
        # Validate that the LLM only recommended IDs from the candidate list
        valid_ids = {c.restaurant_id for c in candidates}
        validated_rankings = [r for r in rankings if r.get("restaurant_id") in valid_ids]
        
        # Sort by rank and limit to top_n
        validated_rankings.sort(key=lambda x: x.get("rank", 999))
        return validated_rankings[:top_n]
    except Exception as e:
        logger.warning(f"LLM recommendation failed, using fallback. Error: {e}")
        return deterministic_fallback(candidates, top_k=top_n)
