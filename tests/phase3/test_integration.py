import pytest

from phase1.ingestion.models import Restaurant
from phase2.preferences.types import UserPreferences
from phase3.integration.retrieval import filter_and_rank, get_budget_range
from phase3.integration.prompt import build_prompt_payload
from phase3.integration.pipeline import build_integration_output

@pytest.fixture
def sample_restaurants():
    return [
        Restaurant(
            restaurant_id="1",
            name="Cheap Delhi Bites",
            location="New Delhi",
            cuisines=["North Indian", "Street Food"],
            cost=200.0,
            rating=4.5
        ),
        Restaurant(
            restaurant_id="2",
            name="Fancy Delhi Dining",
            location="New Delhi",
            cuisines=["North Indian", "Mughlai"],
            cost=2000.0,
            rating=4.8
        ),
        Restaurant(
            restaurant_id="3",
            name="Mumbai Cafe",
            location="Mumbai",
            cuisines=["Cafe", "Desserts"],
            cost=800.0,
            rating=4.2
        ),
        Restaurant(
            restaurant_id="4",
            name="Medium Delhi North",
            location="New Delhi",
            cuisines=["North Indian"],
            cost=1000.0,
            rating=3.5
        ),
        Restaurant(
            restaurant_id="5",
            name="Unrated Delhi",
            location="New Delhi",
            cuisines=["North Indian"],
            cost=1000.0,
            rating=None
        ),
    ]

def test_budget_range():
    assert get_budget_range("low")[1] == 500.0
    assert get_budget_range("medium")[1] == 1500.0
    assert get_budget_range("high")[0] > 1500.0

def test_filter_and_rank_location(sample_restaurants):
    prefs = UserPreferences(location="mumbai", budget_band="medium")
    results = filter_and_rank(sample_restaurants, prefs)
    assert len(results) == 1
    assert results[0].name == "Mumbai Cafe"

def test_filter_and_rank_budget(sample_restaurants):
    prefs = UserPreferences(location="new delhi", budget_band="low")
    results = filter_and_rank(sample_restaurants, prefs)
    assert len(results) == 1
    assert results[0].name == "Cheap Delhi Bites"

    prefs_high = UserPreferences(location="new delhi", budget_band="high")
    results_high = filter_and_rank(sample_restaurants, prefs_high)
    assert len(results_high) == 1
    assert results_high[0].name == "Fancy Delhi Dining"

def test_filter_and_rank_cuisines(sample_restaurants):
    prefs = UserPreferences(location="new delhi", budget_band="medium", cuisines=["Street Food"])
    # No medium budget place in New Delhi has street food in sample
    results = filter_and_rank(sample_restaurants, prefs)
    assert len(results) == 0

def test_filter_and_rank_minimum_rating(sample_restaurants):
    prefs = UserPreferences(location="new delhi", budget_band="medium", minimum_rating=4.0)
    results = filter_and_rank(sample_restaurants, prefs)
    # The only medium place in Delhi is 3.5, and the unrated one
    assert len(results) == 0
    
    prefs2 = UserPreferences(location="new delhi", budget_band="medium", minimum_rating=3.0)
    results2 = filter_and_rank(sample_restaurants, prefs2)
    assert len(results2) == 1
    assert results2[0].name == "Medium Delhi North"

def test_filter_and_rank_sorting(sample_restaurants):
    prefs = UserPreferences(location="new delhi", budget_band="medium")
    results = filter_and_rank(sample_restaurants, prefs)
    # Should contain "Medium Delhi North" (3.5) and "Unrated Delhi" (None)
    assert len(results) == 2
    assert results[0].name == "Medium Delhi North"
    assert results[1].name == "Unrated Delhi"


def test_filter_and_rank_word_level_location_matching():
    """Longest-word matching allows 'Bannerghatta Road' to match 'Bannerghatta' but not 'Sarjapur Road'."""
    restaurants = [
        Restaurant(
            restaurant_id="x1",
            name="Bannerghatta Grill",
            location="Bannerghatta",
            cuisines=["North Indian"],
            cost=1200.0,
            rating=4.2,
        ),
        Restaurant(
            restaurant_id="x2",
            name="Roadside Cafe",
            location="Bannerghatta Road",
            cuisines=["Cafe"],
            cost=800.0,
            rating=3.8,
        ),
        Restaurant(
            restaurant_id="x3",
            name="Sarjapur Eatery",
            location="Sarjapur Road",
            cuisines=["South Indian"],
            cost=500.0,
            rating=4.0,
        ),
        Restaurant(
            restaurant_id="x4",
            name="BTM Eatery",
            location="BTM",
            cuisines=["South Indian"],
            cost=500.0,
            rating=4.0,
        ),
    ]
    prefs = UserPreferences(location="Bannerghatta Road", budget_band="medium")
    results = filter_and_rank(restaurants, prefs)
    names = {r.name for r in results}
    # "Bannerghatta" (longest word) should match both "Bannerghatta" and "Bannerghatta Road"
    assert "Bannerghatta Grill" in names
    assert "Roadside Cafe" in names
    # "Sarjapur Road" should NOT match because "Sarjapur" != "Bannerghatta"
    assert "Sarjapur Eatery" not in names
    # "BTM" should not match
    assert "BTM Eatery" not in names


def test_filter_and_rank_deduplication():
    # Duplicate restaurants should be collapsed, keeping the highest-rated copy.
    dupes = [
        Restaurant(
            restaurant_id="a1",
            name="Chili's",
            location="Bellandur",
            cuisines=["American"],
            cost=1800.0,
            rating=4.5,
        ),
        Restaurant(
            restaurant_id="a2",
            name="chili's",
            location="bellandur",
            cuisines=["American", "Tex-Mex"],
            cost=1800.0,
            rating=4.2,
        ),
        Restaurant(
            restaurant_id="b1",
            name="Nook",
            location="Bellandur",
            cuisines=["Continental"],
            cost=1800.0,
            rating=4.3,
        ),
    ]
    prefs = UserPreferences(location="Bellandur", budget_band="high")
    results = filter_and_rank(dupes, prefs)
    assert len(results) == 2
    names = {r.name for r in results}
    assert names == {"Chili's", "Nook"}
    # The kept Chili's should have the higher rating (4.5)
    chilis = next(r for r in results if r.name == "Chili's")
    assert chilis.rating == 4.5

def test_build_prompt_payload(sample_restaurants):
    prefs = UserPreferences(location="new delhi", budget_band="medium", additional_preferences="Spicy")
    candidates = sample_restaurants[:1] # Pass 1 candidate
    
    payload = build_prompt_payload(prefs, candidates)
    
    assert "messages" in payload
    assert len(payload["messages"]) == 2
    
    sys_msg = payload["messages"][0]["content"]
    assert "You are a helpful restaurant recommendation assistant." in sys_msg
    assert "rankings" in sys_msg
    
    user_msg = payload["messages"][1]["content"]
    assert "New Delhi" in user_msg
    assert "Spicy" in user_msg
    assert "Cheap Delhi Bites" in user_msg

def test_build_integration_output(sample_restaurants):
    prefs = UserPreferences(location="new delhi", budget_band="low")
    result = build_integration_output(sample_restaurants, prefs)

    assert "candidates" in result
    # Only 1 restaurant matches "low" budget in New Delhi;
    # pipeline pads with supplemental highly-rated candidates to reach min 5.
    assert len(result["candidates"]) == 5

    # First candidate should be the strict rule-based match
    assert result["candidates"][0].name == "Cheap Delhi Bites"

    # Ensure no duplicates by restaurant_id across filtered + supplemental
    ids = [c.restaurant_id for c in result["candidates"]]
    assert len(ids) == len(set(ids))

    assert "prompt_payload" in result
    assert "messages" in result["prompt_payload"]
