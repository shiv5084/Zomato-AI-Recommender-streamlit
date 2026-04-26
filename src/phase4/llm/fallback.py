def deterministic_fallback(candidates: list, top_k: int = 5) -> list[dict]:
    """
    Fallback if LLM fails. Takes the top candidates and returns a generic ranking.
    """
    rankings = []
    for i, c in enumerate(candidates[:top_k], start=1):
        rating_str = f"{c.rating} stars" if c.rating is not None else "no rating"
        
        # Determine budget band heuristically
        budget_band = "unknown"
        if c.cost is not None:
            if c.cost <= 500:
                budget_band = "low"
            elif c.cost <= 1500:
                budget_band = "medium"
            else:
                budget_band = "high"
                
        rankings.append({
            "restaurant_id": c.restaurant_id,
            "rank": i,
            "explanation": f"Recommended based on deterministic fallback (Rating: {rating_str}).",
            "restaurant": {
                "id": c.restaurant_id,
                "restaurant_name": c.name,
                "city": c.location,
                "cuisines": c.cuisines,
                "rating": c.rating if c.rating is not None else 0.0,
                "approx_cost_for_two_inr": c.cost if c.cost is not None else 0.0,
                "budget_band": budget_band
            }
        })
    return rankings
