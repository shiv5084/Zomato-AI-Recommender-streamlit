import json
from typing import Any

def build_prompt_payload(preferences: Any, candidates: list) -> dict:
    """
    Construct the prompt payload to send to the LLM.
    Returns a dictionary containing the system and user messages.
    """
    # Create a simplified JSON of candidates to keep prompt size reasonable
    candidates_data = []
    for c in candidates:
        candidates_data.append({
            "restaurant_id": c.restaurant_id,
            "name": c.name,
            "location": c.location,
            "cuisines": c.cuisines,
            "cost": c.cost,
            "rating": c.rating
        })
        
    system_message = (
        "You are a helpful restaurant recommendation assistant.\n"
        "You must recommend restaurants ONLY from the provided candidate list.\n"
        "Your output must be structured as JSON matching the following format:\n"
        "{\n"
        '  "rankings": [\n'
        '    {\n'
        '      "restaurant_id": "string",\n'
        '      "rank": "integer",\n'
        '      "explanation": "string",\n'
        '      "restaurant": {\n'
        '        "id": "string",\n'
        '        "restaurant_name": "string",\n'
        '        "city": "string",\n'
        '        "cuisines": ["string"],\n'
        '        "rating": "number",\n'
        '        "approx_cost_for_two_inr": "number",\n'
        '        "budget_band": "string"\n'
        '      }\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "If no candidates fit the preferences, return an empty rankings list."
    )
    
    # Safely get cuisines
    prefs_cuisines = preferences.cuisines if preferences.cuisines else []
    
    user_message = (
        f"User Preferences:\n"
        f"- Location: {preferences.location}\n"
        f"- Budget Band: {preferences.budget_band}\n"
        f"- Minimum Rating: {preferences.minimum_rating}\n"
        f"- Preferred Cuisines: {', '.join(prefs_cuisines) if prefs_cuisines else 'Any'}\n"
        f"- Additional Preferences: {preferences.additional_preferences or 'None'}\n\n"
        f"Candidate List:\n"
        f"{json.dumps(candidates_data, indent=2)}\n\n"
        f"Please provide the top 5 recommendations based on these preferences and the candidate list. "
        f"Return exactly 5 restaurants ranked from 1 (best) to 5."
    )
    
    return {
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
    }
