"""Streamlit app for Phase 8: lightweight deployment of the recommendation pipeline."""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path

# Ensure src/ is on PYTHONPATH when running this file directly
_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Load .env from repo root if present
_repo_root = _SRC.parent
_env_path = _repo_root / ".env"
if _env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=_env_path)
    except Exception:
        pass

import streamlit as st

from phase1.ingestion.loader import load_restaurants
from phase1.ingestion.models import Restaurant
from phase2.preferences.service import (
    ValidationError,
    allowed_cities_from_restaurants,
    preferences_from_mapping,
)
from phase3.integration.pipeline import build_integration_output
from phase4.llm.engine import recommend_with_groq

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATASET_LIMIT = 5000
CANDIDATE_TOP_N = 15
RECOMMENDATION_TOP_N = 5

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_api_key() -> str | None:
    """Resolve GROQ_API_KEY from Streamlit secrets (Cloud) or environment."""
    try:
        return st.secrets["GROQ_API_KEY"]
    except (KeyError, FileNotFoundError):
        return os.getenv("GROQ_API_KEY")


@st.cache_data(show_spinner="Loading restaurants from dataset...")
def _cached_load_restaurants(limit: int = DATASET_LIMIT) -> list[Restaurant]:
    return load_restaurants(limit=limit)


def _get_cities(restaurants: list[Restaurant]) -> list[str]:
    return sorted({r.location for r in restaurants if r.location})


def _get_cuisines(restaurants: list[Restaurant]) -> list[str]:
    cuisine_set: set[str] = set()
    for r in restaurants:
        for c in r.cuisines:
            if c:
                cuisine_set.add(c)
    return sorted(cuisine_set)


def _lookup_restaurant(candidates: list[Restaurant], restaurant_id: str) -> Restaurant | None:
    for c in candidates:
        if c.restaurant_id == restaurant_id:
            return c
    return None


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------


def _render_header() -> None:
    banner_html = """
    <div class="hero-banner">
        <div class="hero-content">
            <h1>🍽️ Zomato AI Restaurant Recommender</h1>
        </div>
        <div class="hero-shapes">
            <span class="shape">🍜</span>
            <span class="shape">🥗</span>
            <span class="shape">🍰</span>
            <span class="shape">🍹</span>
        </div>
    </div>
    """
    st.markdown(banner_html, unsafe_allow_html=True)


def _render_preferences_form(cities: list[str], all_cuisines: list[str]) -> dict | None:
    with st.form("preferences_form"):
        st.subheader("Your Preferences")

        # Row 1: Location & Rating
        col1, col2 = st.columns(2)
        with col1:
            location = st.selectbox(
                "Location",
                options=cities,
                help="Choose a city or locality from the dataset.",
            )
        with col2:
            minimum_rating = st.select_slider(
                "Minimum Rating",
                options=[round(x * 0.1, 1) for x in range(0, 51)],
                value=0.0,
                help="Filter restaurants with rating at least this value.",
            )

        # Row 2: Cuisines
        cuisines = st.multiselect(
            "Preferred Cuisines",
            options=all_cuisines,
            help="Leave empty to allow any cuisine.",
        )

        # Row 3: Budget Band as elegant cards
        st.markdown("<p style='margin-bottom:0.3rem; font-size:0.9rem; color:#666;'>Budget Band</p>", unsafe_allow_html=True)
        budget_band = st.radio(
            "Budget Band",
            options=["low", "medium", "high"],
            horizontal=True,
            help="Low: ≤ ₹500 | Medium: ₹501–₹1500 | High: > ₹1500 (for two people)",
            label_visibility="collapsed",
        )

        # Row 4: Additional Preferences
        additional_preferences = st.text_area(
            "Additional Preferences",
            placeholder="E.g., rooftop seating, vegan options, kid-friendly...",
            help="Optional free-text hints for the AI.",
        )

        submitted = st.form_submit_button("Get Recommendations", use_container_width=True)

    if not submitted:
        return None

    return {
        "location": location,
        "budget_band": budget_band,
        "cuisines": cuisines,
        "minimum_rating": minimum_rating,
        "additional_preferences": additional_preferences or None,
    }


def _render_metrics(filter_count: int, candidate_count: int, latency_ms: float) -> None:
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Restaurants", filter_count)
    c2.metric("Candidates", candidate_count)
    c3.metric("Latency", f"{latency_ms:.0f} ms")


def _render_empty_state(source: str) -> None:
    if source == "no_candidates":
        st.info(
            "No restaurants matched your filters. Try relaxing your criteria "
            "(e.g., lower the minimum rating, choose a different location, or clear cuisine selections)."
        )
    else:
        st.warning("No recommendations could be generated. Please try again.")


def _render_rankings(rankings: list[dict], candidates: list[Restaurant]) -> None:
    st.subheader("Top Recommendations")
    for idx, item in enumerate(rankings):
        rank = item.get("rank", 0)
        explanation = item.get("explanation", "No explanation provided.")
        restaurant_data = item.get("restaurant", {})
        restaurant_id = item.get("restaurant_id", "")

        # Fallback lookup if LLM didn't embed restaurant details
        if not restaurant_data:
            rest = _lookup_restaurant(candidates, restaurant_id)
            if rest:
                restaurant_data = {
                    "restaurant_name": rest.name,
                    "city": rest.location,
                    "cuisines": rest.cuisines,
                    "rating": rest.rating,
                    "approx_cost_for_two_inr": rest.cost,
                    "budget_band": "unknown",
                }

        name = restaurant_data.get("restaurant_name", "Unknown")
        city = restaurant_data.get("city", "")
        cuisines = restaurant_data.get("cuisines", [])
        rating = restaurant_data.get("rating")
        cost = restaurant_data.get("approx_cost_for_two_inr")
        budget = restaurant_data.get("budget_band", "unknown")

        meta_parts = []
        if city:
            meta_parts.append(f"📍 {city}")
        if rating is not None:
            meta_parts.append(f"⭐ {rating}")
        if cost is not None:
            meta_parts.append(f"₹{cost:.0f} for two")
        if cuisines:
            meta_parts.append(f"🍽️ {', '.join(cuisines)}")

        meta_html = " ・ ".join(meta_parts) if meta_parts else ""

        card_html = f"""
        <div class="rec-card" style="animation-delay: {idx * 0.12}s;">
            <div class="rec-card-header">
                <span class="rec-card-title">#{rank} — {name}</span>
                <span class="rec-card-badge">{budget}</span>
            </div>
            <div class="rec-card-meta">{meta_html}</div>
            <div class="rec-card-explanation">{explanation}</div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)


def _render_source_badge(source: str) -> None:
    if source == "fallback":
        st.info("Recommendations were generated using a deterministic fallback because the LLM call failed or returned invalid output.")
    elif source == "llm":
        st.success("Recommendations powered by Groq LLM.")


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def _run_pipeline(raw_prefs: dict, restaurants: list[Restaurant]) -> dict:
    t0 = time.time()
    allowed_cities = allowed_cities_from_restaurants(restaurants)

    try:
        prefs = preferences_from_mapping(raw_prefs, allowed_city_names=allowed_cities)
    except ValidationError as exc:
        st.error(str(exc))
        return {"error": True}

    integration_output = build_integration_output(restaurants, prefs, top_n=CANDIDATE_TOP_N)
    candidates = integration_output["candidates"]
    prompt_payload = integration_output["prompt_payload"]

    latency_ms = round((time.time() - t0) * 1000, 2)

    if not candidates:
        _render_metrics(len(restaurants), 0, latency_ms)
        _render_empty_state("no_candidates")
        return {"source": "no_candidates", "rankings": [], "candidates": [], "filter_count": len(restaurants), "latency_ms": latency_ms}

    _render_metrics(len(restaurants), len(candidates), latency_ms)

    with st.spinner("Asking AI for recommendations..."):
        t1 = time.time()
        rankings = recommend_with_groq(prompt_payload, candidates, top_n=RECOMMENDATION_TOP_N)
        llm_latency_ms = round((time.time() - t1) * 1000, 2)

    # Detect fallback
    source = "llm"
    if rankings and any("fallback" in r.get("explanation", "") for r in rankings):
        source = "fallback"
    if not rankings:
        source = "no_candidates"

    st.caption(f"LLM latency: {llm_latency_ms} ms")

    if not rankings:
        _render_empty_state("no_candidates")
        return {"source": source, "rankings": [], "candidates": candidates, "filter_count": len(restaurants), "latency_ms": latency_ms + llm_latency_ms}

    _render_source_badge(source)
    _render_rankings(rankings, candidates)

    return {
        "source": source,
        "rankings": rankings,
        "candidates": candidates,
        "filter_count": len(restaurants),
        "latency_ms": latency_ms + llm_latency_ms,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    # Inject comprehensive custom CSS for micro-interactions
    st.markdown(
        """
        <style>
        /* ── Global smooth transitions ── */
        * {
            transition-property: box-shadow, transform, background-color, border-color, opacity;
            transition-duration: 0.2s;
            transition-timing-function: ease;
        }

        /* ── Hero banner ── */
        .hero-banner {
            background: linear-gradient(135deg, #FF6F00 0%, #E53935 50%, #FF8F00 100%);
            border-radius: 18px;
            padding: 2.2rem 2rem;
            margin-bottom: 1.5rem;
            position: relative;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(229, 57, 53, 0.25);
            animation: bannerFadeIn 0.8s ease-out;
        }
        @keyframes bannerFadeIn {
            from { opacity: 0; transform: translateY(-12px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        .hero-banner::before {
            content: "";
            position: absolute;
            top: -40%;
            right: -10%;
            width: 300px;
            height: 300px;
            background: rgba(255,255,255,0.08);
            border-radius: 50%;
            animation: floatCircle 8s ease-in-out infinite;
        }
        @keyframes floatCircle {
            0%, 100% { transform: translate(0, 0); }
            50%      { transform: translate(-20px, 15px); }
        }
        .hero-content {
            position: relative;
            z-index: 1;
        }
        .hero-content h1 {
            color: #ffffff;
            font-size: 1.8rem;
            font-weight: 800;
            margin: 0 0 0.4rem 0;
            letter-spacing: -0.5px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.15);
        }
        .hero-content p {
            color: rgba(255,255,255,0.92);
            font-size: 1rem;
            margin: 0 0 1rem 0;
            font-weight: 400;
        }
        .hero-pills {
            display: flex;
            gap: 0.6rem;
            flex-wrap: wrap;
        }
        .pill {
            background: rgba(255,255,255,0.2);
            backdrop-filter: blur(8px);
            color: #ffffff;
            padding: 0.35rem 0.9rem;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 600;
            border: 1px solid rgba(255,255,255,0.3);
            transition: all 0.25s ease;
        }
        .pill:hover {
            background: rgba(255,255,255,0.35);
            transform: translateY(-2px);
        }
        .hero-shapes {
            position: absolute;
            right: 1.5rem;
            bottom: 1rem;
            display: flex;
            gap: 0.8rem;
            z-index: 1;
        }
        .hero-shapes .shape {
            font-size: 1.8rem;
            opacity: 0.85;
            animation: foodBounce 2.5s ease-in-out infinite;
            display: inline-block;
        }
        .hero-shapes .shape:nth-child(2) { animation-delay: 0.3s; }
        .hero-shapes .shape:nth-child(3) { animation-delay: 0.6s; }
        .hero-shapes .shape:nth-child(4) { animation-delay: 0.9s; }
        @keyframes foodBounce {
            0%, 100% { transform: translateY(0); }
            50%      { transform: translateY(-8px); }
        }

        /* ── Orange sidebar ── */
        [data-testid="stSidebar"] {
            background-color: #FFA500;
        }
        [data-testid="stSidebar"] * {
            color: #1a1a1a;
        }

        /* ── Red interactive submit button ── */
        [data-testid="stFormSubmitButton"] > button {
            background-color: #E53935 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.6rem 1.2rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.5px !important;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 4px 6px rgba(229, 57, 53, 0.3) !important;
            cursor: pointer !important;
        }
        [data-testid="stFormSubmitButton"] > button:hover {
            background-color: #C62828 !important;
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 8px 16px rgba(229, 57, 53, 0.4) !important;
        }
        [data-testid="stFormSubmitButton"] > button:active {
            transform: translateY(0px) scale(0.98) !important;
            box-shadow: 0 2px 4px rgba(229, 57, 53, 0.3) !important;
        }

        /* ── Budget Band radio cards ── */
        [data-testid="stRadio"] > div[role="radiogroup"] {
            display: flex !important;
            gap: 0.75rem !important;
            flex-wrap: wrap !important;
        }
        [data-testid="stRadio"] > div[role="radiogroup"] > label {
            flex: 1 1 30% !important;
            min-width: 100px !important;
            padding: 1rem 0.5rem !important;
            border-radius: 12px !important;
            border: 2px solid #e8e8e8 !important;
            background: #ffffff !important;
            cursor: pointer !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            text-align: center !important;
            position: relative !important;
            overflow: hidden !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04) !important;
        }
        [data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
            transform: translateY(-4px) !important;
            box-shadow: 0 12px 24px rgba(0,0,0,0.1) !important;
            border-color: #FFA500 !important;
        }
        [data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) {
            background: #FFF8E1 !important;
            border-color: #FF6F00 !important;
            box-shadow: 0 4px 12px rgba(255, 111, 0, 0.2) !important;
            transform: translateY(-2px) !important;
        }

        /* Colored accent bars per budget card */
        [data-testid="stRadio"] > div[role="radiogroup"] > label:nth-child(1)::before {
            content: "" !important;
            position: absolute !important;
            top: 0 !important; left: 0 !important;
            width: 100% !important; height: 4px !important;
            background: linear-gradient(90deg, #66BB6A, #43A047) !important;
        }
        [data-testid="stRadio"] > div[role="radiogroup"] > label:nth-child(2)::before {
            content: "" !important;
            position: absolute !important;
            top: 0 !important; left: 0 !important;
            width: 100% !important; height: 4px !important;
            background: linear-gradient(90deg, #FFA726, #FB8C00) !important;
        }
        [data-testid="stRadio"] > div[role="radiogroup"] > label:nth-child(3)::before {
            content: "" !important;
            position: absolute !important;
            top: 0 !important; left: 0 !important;
            width: 100% !important; height: 4px !important;
            background: linear-gradient(90deg, #EF5350, #C62828) !important;
        }

        /* Hide the default radio circle and enlarge tap target text */
        [data-testid="stRadio"] > div[role="radiogroup"] > label input {
            display: none !important;
        }
        [data-testid="stRadio"] > div[role="radiogroup"] > label span {
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            text-transform: capitalize !important;
        }

        /* ── Form inputs focus glow ── */
        [data-testid="stSelectbox"] > div,
        [data-testid="stTextArea"] > div,
        [data-testid="stMultiSelect"] > div {
            border-radius: 8px !important;
        }
        [data-testid="stSelectbox"]:focus-within > div,
        [data-testid="stTextArea"]:focus-within > div,
        [data-testid="stMultiSelect"]:focus-within > div {
            box-shadow: 0 0 0 3px rgba(255, 165, 0, 0.25) !important;
            border-color: #FFA500 !important;
        }

        /* ── Result cards with staggered fade-in ── */
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(20px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        .rec-card {
            background: #ffffff;
            border: 1px solid #e8e8e8;
            border-radius: 14px;
            padding: 1.1rem 1.3rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            animation: fadeInUp 0.5s ease forwards;
            opacity: 0;
        }
        .rec-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.08);
            border-color: #FFD180;
        }
        .rec-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.4rem;
        }
        .rec-card-title {
            font-weight: 700;
            font-size: 1.05rem;
            color: #1a1a1a;
        }
        .rec-card-badge {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: capitalize;
            color: #888;
            background: #f5f5f5;
            padding: 0.2rem 0.6rem;
            border-radius: 20px;
        }
        .rec-card-meta {
            font-size: 0.85rem;
            color: #666;
            margin-bottom: 0.6rem;
        }
        .rec-card-explanation {
            font-size: 0.92rem;
            color: #444;
            line-height: 1.5;
            padding-left: 0.7rem;
            border-left: 3px solid #FFA500;
        }

        /* ── Metric cards micro-interaction ── */
        [data-testid="stMetric"] {
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            border-radius: 10px;
            padding: 0.5rem;
        }
        [data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.06);
            background: #fafafa;
        }

        /* ── Subheaders with subtle accent ── */
        h3 {
            border-bottom: 2px solid #FFE0B2;
            padding-bottom: 0.3rem;
            margin-bottom: 1rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _render_header()

    # Validate API key
    api_key = _get_api_key()
    if not api_key:
        st.error(
            "GROQ_API_KEY is not configured. Set it via:\n"
            "- Streamlit secrets (Cloud), or\n"
            "- Environment variable, or\n"
            "- `.env` file in the repo root."
        )
        st.stop()

    # Ensure downstream code sees the key
    os.environ["GROQ_API_KEY"] = api_key

    # Load data
    try:
        restaurants = _cached_load_restaurants(DATASET_LIMIT)
    except Exception as exc:
        logger.exception("Failed to load restaurants: %s", exc)
        st.error(f"Failed to load dataset: {exc}")
        st.stop()

    if not restaurants:
        st.error("No restaurants loaded from the dataset.")
        st.stop()

    cities = _get_cities(restaurants)
    all_cuisines = _get_cuisines(restaurants)

    # Sidebar info
    with st.sidebar:
        st.header("About")
        st.markdown(
            "Discover restaurants tailored to your taste, mood, and cravings. "
            "This app helps you explore the best dining options around you with smart, "
            "personalized suggestions—making it easier to decide what to eat, anytime."
        )
        st.divider()
        st.markdown(f"**Dataset:** {len(restaurants):,} restaurants loaded")
        st.markdown(f"**Locations:** {len(cities):,} unique")
        st.markdown(f"**Cuisines:** {len(all_cuisines):,} unique")

    # Preferences form
    raw_prefs = _render_preferences_form(cities, all_cuisines)
    if raw_prefs is not None:
        _run_pipeline(raw_prefs, restaurants)


# Streamlit executes top-to-bottom; calling main() keeps the script tidy.
if __name__ == "__main__":
    main()
