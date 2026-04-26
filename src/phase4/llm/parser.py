import json


def _extract_json(text: str) -> str | None:
    """Extract the first JSON object from a string that may contain extra text."""
    text = text.strip()
    # Strip markdown code blocks
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    # Find the first '{' and matching last '}'
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return None


def parse_rankings(json_str: str) -> list[dict]:
    """
    Parse the JSON output from the LLM.
    Expected structure: {"rankings": [{"restaurant_id": "...", "rank": 1, "explanation": "..."}]}
    """
    if not json_str or not json_str.strip():
        return []

    raw = _extract_json(json_str)
    if raw is None:
        raise ValueError("Failed to parse JSON from LLM response.")

    try:
        data = json.loads(raw)
        rankings = data.get("rankings", [])
        if not isinstance(rankings, list):
            return []
        return rankings
    except json.JSONDecodeError:
        raise ValueError("Failed to parse JSON from LLM response.")
