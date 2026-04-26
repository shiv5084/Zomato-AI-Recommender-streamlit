from typing import Any

from phase3.integration.retrieval import filter_and_rank
from phase3.integration.prompt import build_prompt_payload

def build_integration_output(restaurants: list, prefs: Any, top_n: int = 15) -> dict:
    """
    Run the full Phase 3 integration pipeline.
    
    1. Filter and rank candidates based on user preferences.
    2. Build the prompt payload for the LLM.
    
    Returns:
        dict: A dictionary containing the candidates list and the prompt payload.
    """
    candidates = filter_and_rank(restaurants, prefs, top_n=top_n)
    prompt_payload = build_prompt_payload(prefs, candidates)
    
    return {
        "candidates": candidates,
        "prompt_payload": prompt_payload
    }
