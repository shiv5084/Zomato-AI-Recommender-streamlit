from typing import Any

from phase3.integration.retrieval import filter_and_rank
from phase3.integration.prompt import build_prompt_payload


def _pad_candidates(filtered: list, all_restaurants: list, min_count: int = 5) -> list:
    """
    If rule-based filtered candidates are fewer than min_count (but > 0),
    pad with additional highly-rated restaurants from the full pool.
    Ensures no duplicate restaurants by ID or (name, location).
    """
    if len(filtered) >= min_count or len(filtered) == 0:
        return filtered

    selected_ids = {c.restaurant_id for c in filtered}
    selected_keys = {(c.name.lower(), c.location.lower()) for c in filtered}

    supplemental = []
    for r in all_restaurants:
        if r.restaurant_id in selected_ids:
            continue
        key = (r.name.lower(), r.location.lower())
        if key in selected_keys:
            continue
        supplemental.append(r)
        selected_ids.add(r.restaurant_id)
        selected_keys.add(key)

    supplemental.sort(key=lambda x: x.rating if x.rating is not None else -1.0, reverse=True)

    needed = min_count - len(filtered)
    return filtered + supplemental[:needed]


def build_integration_output(restaurants: list, prefs: Any, top_n: int = 15) -> dict:
    """
    Run the full Phase 3 integration pipeline.

    1. Filter and rank candidates based on user preferences.
    2. Pad candidates to at least 5 if fewer matched but > 0.
    3. Build the prompt payload for the LLM.

    Returns:
        dict: A dictionary containing the candidates list and the prompt payload.
    """
    candidates = filter_and_rank(restaurants, prefs, top_n=top_n)
    candidates = _pad_candidates(candidates, restaurants, min_count=5)
    prompt_payload = build_prompt_payload(prefs, candidates)

    return {
        "candidates": candidates,
        "prompt_payload": prompt_payload
    }
