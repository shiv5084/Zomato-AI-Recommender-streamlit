import pytest
from unittest.mock import patch
from phase1.ingestion.models import Restaurant
from phase4.llm.parser import parse_rankings
from phase4.llm.fallback import deterministic_fallback
from phase4.llm.engine import recommend_with_groq

@pytest.fixture
def sample_candidates():
    return [
        Restaurant(
            restaurant_id="1",
            name="Cheap Delhi Bites",
            location="New Delhi",
            cost=200.0,
            rating=4.5
        ),
        Restaurant(
            restaurant_id="2",
            name="Fancy Delhi Dining",
            location="New Delhi",
            cost=2000.0,
            rating=4.8
        )
    ]

def test_parse_rankings_valid():
    valid_json = '{"rankings": [{"restaurant_id": "1", "rank": 1, "explanation": "Great.", "restaurant": {"id": "1"}}]}'
    result = parse_rankings(valid_json)
    assert len(result) == 1
    assert result[0]["restaurant_id"] == "1"
    assert result[0]["rank"] == 1
    assert result[0]["restaurant"]["id"] == "1"

def test_parse_rankings_invalid_json():
    with pytest.raises(ValueError):
        parse_rankings("not a json")

def test_parse_rankings_empty():
    assert parse_rankings("") == []
    assert parse_rankings('{"rankings": []}') == []

def test_deterministic_fallback(sample_candidates):
    result = deterministic_fallback(sample_candidates)
    assert len(result) == 2
    assert result[0]["restaurant_id"] == "1"
    assert result[0]["rank"] == 1
    assert "4.5 stars" in result[0]["explanation"]
    assert result[0]["restaurant"]["id"] == "1"
    assert result[0]["restaurant"]["budget_band"] == "low"

@patch("phase4.llm.engine.call_groq_model")
def test_recommend_with_groq_success(mock_call, sample_candidates):
    mock_call.return_value = '{"rankings": [{"restaurant_id": "2", "rank": 1, "explanation": "Best.", "restaurant": {"id": "2"}}]}'
    prompt_payload = {"messages": [{"role": "user", "content": "hello"}]}
    
    result = recommend_with_groq(prompt_payload, sample_candidates)
    assert len(result) == 1
    assert result[0]["restaurant_id"] == "2"

@patch("phase4.llm.engine.call_groq_model")
def test_recommend_with_groq_filters_invalid_ids(mock_call, sample_candidates):
    # ID "3" is not in sample_candidates
    mock_call.return_value = '{"rankings": [{"restaurant_id": "3", "rank": 1, "explanation": "Fake."}]}'
    prompt_payload = {"messages": []}
    
    result = recommend_with_groq(prompt_payload, sample_candidates)
    assert len(result) == 0

@patch("phase4.llm.engine.call_groq_model")
def test_recommend_with_groq_fallback_on_error(mock_call, sample_candidates):
    mock_call.side_effect = RuntimeError("API down")
    prompt_payload = {"messages": []}
    
    result = recommend_with_groq(prompt_payload, sample_candidates)
    assert len(result) == 2 # fallback returns all (within top_n=5)
    assert result[0]["restaurant_id"] == "1"


@patch("phase4.llm.engine.call_groq_model")
def test_recommend_with_groq_respects_top_n(mock_call):
    # Create 10 candidates
    candidates = [
        Restaurant(
            restaurant_id=str(i),
            name=f"Restaurant {i}",
            location="Delhi",
            cost=500.0,
            rating=4.0,
        )
        for i in range(1, 11)
    ]
    # LLM returns all 10
    rankings = [{"restaurant_id": str(i), "rank": i, "explanation": f"Rank {i}", "restaurant": {"id": str(i)}} for i in range(1, 11)]
    mock_call.return_value = f'{{"rankings": {rankings}}}'
    prompt_payload = {"messages": []}

    # Default top_n=5 should return only 5
    result = recommend_with_groq(prompt_payload, candidates)
    assert len(result) == 5
    assert result[0]["rank"] == 1
    assert result[4]["rank"] == 5

    # Explicit top_n=3 should return only 3
    result = recommend_with_groq(prompt_payload, candidates, top_n=3)
    assert len(result) == 3
    assert result[2]["rank"] == 3
