def get_budget_range(budget_band: str) -> tuple[float, float]:
    """Map budget band to a cost range (min, max)."""
    if budget_band == "low":
        return 0.0, 500.0
    elif budget_band == "medium":
        return 500.0001, 1500.0
    elif budget_band == "high":
        return 1500.0001, float('inf')
    # Default fallback
    return 0.0, float('inf')

def _deduplicate_restaurants(restaurants: list) -> list:
    """
    Remove duplicate restaurants by (name, location), keeping the highest-rated copy.
    Preserves original order for first occurrences.
    """
    seen: dict[tuple[str, str], object] = {}
    for r in restaurants:
        key = (r.name.lower(), r.location.lower())
        if key not in seen:
            seen[key] = r
        else:
            existing = seen[key]
            existing_rating = existing.rating if existing.rating is not None else -1.0
            current_rating = r.rating if r.rating is not None else -1.0
            if current_rating > existing_rating:
                seen[key] = r
    return list(seen.values())


def _location_matches(pref_location: str, rest_location: str) -> bool:
    """
    Check if a restaurant location matches the user's preferred location.
    Uses the longest word (most specific) for matching to avoid false positives
    from common words like "Road", "Street", "Layout", etc.
    """
    pref_lower = pref_location.lower()
    rest_lower = rest_location.lower()

    # Direct substring match in either direction
    if pref_lower in rest_lower or rest_lower in pref_lower:
        return True

    words = pref_lower.split()
    if not words:
        return False

    # Use the longest word as the primary match — it's usually the most specific
    longest = max(words, key=len)
    if len(longest) >= 5:
        return longest in rest_lower

    # For very short locations, require exact match
    return pref_lower == rest_lower


def filter_and_rank(restaurants: list, prefs, top_n: int = 15) -> list:
    """
    Filter restaurants based on user preferences and return the top_n ranked candidates.
    """
    candidates = []
    min_cost, max_cost = get_budget_range(prefs.budget_band)

    for r in restaurants:
        # 1. Filter by location (word-level matching)
        if prefs.location and not _location_matches(prefs.location, r.location):
            continue

        # 2. Filter by minimum rating
        if prefs.minimum_rating > 0.0:
            if r.rating is None or r.rating < prefs.minimum_rating:
                continue

        # 3. Filter by budget band
        if r.cost is not None:
            if not (min_cost <= r.cost <= max_cost):
                continue

        # 4. Filter by cuisine overlap
        if prefs.cuisines:
            # We want at least one cuisine to match
            r_cuisines = {c.lower().strip() for c in r.cuisines}
            p_cuisines = {c.lower().strip() for c in prefs.cuisines}
            if not r_cuisines.intersection(p_cuisines):
                continue

        candidates.append(r)

    # Deduplicate before ranking to avoid sending duplicates to the LLM
    candidates = _deduplicate_restaurants(candidates)

    # Sort candidates by rating descending (None ratings go to bottom)
    candidates.sort(key=lambda x: x.rating if x.rating is not None else -1.0, reverse=True)

    return candidates[:top_n]
