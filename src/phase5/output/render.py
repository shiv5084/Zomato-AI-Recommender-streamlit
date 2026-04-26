def render_empty_state(reason: str) -> str:
    """Render a user-friendly message for empty states."""
    if reason == "no_candidates":
        return "No restaurants matched your preferences. Please try relaxing your budget, location, or cuisines."
    elif reason == "llm_failed":
        return "The recommendation engine couldn't generate a valid ranking from the candidates."
    else:
        return "No recommendations available."

def render_recommendations(rankings: list[dict]) -> str:
    """Render the JSON rankings into a readable Markdown string."""
    if not rankings:
        return render_empty_state("llm_failed")
        
    output = []
    output.append("# Top Restaurant Recommendations\n")
    
    for item in rankings:
        rank = item.get("rank", "?")
        explanation = item.get("explanation", "No explanation provided.")
        rest = item.get("restaurant", {})
        
        name = rest.get("restaurant_name", "Unknown Restaurant")
        cuisines = rest.get("cuisines", [])
        cuisine_str = ", ".join(cuisines) if cuisines else "Not specified"
        rating = rest.get("rating", "N/A")
        cost = rest.get("approx_cost_for_two_inr", "N/A")
        
        output.append(f"## {rank}. {name}")
        output.append(f"- **Cuisines**: {cuisine_str}")
        output.append(f"- **Rating**: {rating} stars")
        output.append(f"- **Estimated Cost**: ₹{cost} for two")
        output.append(f"- **Why we recommend it**: {explanation}")
        output.append("")
        
    return "\n".join(output)
