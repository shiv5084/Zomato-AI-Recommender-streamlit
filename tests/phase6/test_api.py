"""Tests for the Phase 6 Backend API."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from phase6.api.main import app

client = TestClient(app)


class FakeRecommendationResult:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_health_endpoint():
    with patch("phase6.api.routers.health.is_groq_configured", return_value=True):
        response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["groq_configured"] is True


def test_health_endpoint_missing_key():
    with patch("phase6.api.routers.health.is_groq_configured", return_value=False):
        response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["groq_configured"] is False


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "Zomato AI Recommender API" in response.json()["message"]


def test_list_cities():
    with patch("phase6.api.routers.metadata.get_cities", return_value=["Delhi", "Mumbai"]):
        response = client.get("/api/v1/metadata/cities")
    assert response.status_code == 200
    assert response.json()["items"] == ["Delhi", "Mumbai"]


def test_list_cuisines():
    with patch("phase6.api.routers.metadata.get_cuisines", return_value=["Italian", "Chinese"]):
        response = client.get("/api/v1/metadata/cuisines")
    assert response.status_code == 200
    assert response.json()["items"] == ["Italian", "Chinese"]


def test_recommend_success():
    fake_result = FakeRecommendationResult(
        rankings=[
            {
                "restaurant_id": "r1",
                "rank": 1,
                "explanation": "Great food!",
                "restaurant": {
                    "id": "r1",
                    "restaurant_name": "Test Cafe",
                    "city": "Delhi",
                    "cuisines": ["Cafe"],
                    "rating": 4.5,
                    "approx_cost_for_two_inr": 800.0,
                    "budget_band": "medium",
                },
            }
        ],
        source="llm",
        filter_count=100,
        candidate_count=10,
        telemetry={"latency_ms": {"load": 50}, "counts": {"total": 100}},
    )

    with patch("phase6.api.routers.recommendations.get_recommendations", return_value=fake_result):
        response = client.post(
            "/api/v1/recommendations",
            json={
                "location": "Delhi",
                "budget_band": "medium",
                "cuisines": ["Cafe"],
                "minimum_rating": 4.0,
                "additional_preferences": None,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "llm"
    assert data["filter_count"] == 100
    assert data["candidate_count"] == 10
    assert len(data["rankings"]) == 1
    assert data["rankings"][0]["restaurant"]["restaurant_name"] == "Test Cafe"


def test_recommend_validation_error():
    # FastAPI/Pydantic validates the enum before it reaches our service.
    response = client.post(
        "/api/v1/recommendations",
        json={
            "location": "Delhi",
            "budget_band": "free",
            "cuisines": [],
            "minimum_rating": 0.0,
        },
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, list)
    assert any("low" in str(err.get("message", "")) for err in detail)
    assert any(err.get("field") == "budget_band" for err in detail)


def test_recommend_no_candidates():
    fake_result = FakeRecommendationResult(
        rankings=[],
        source="no_candidates",
        filter_count=100,
        candidate_count=0,
        telemetry=None,
    )

    with patch("phase6.api.routers.recommendations.get_recommendations", return_value=fake_result):
        response = client.post(
            "/api/v1/recommendations",
            json={
                "location": "UnknownCity",
                "budget_band": "low",
                "cuisines": [],
                "minimum_rating": 5.0,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "no_candidates"
    assert data["rankings"] == []


def test_recommend_missing_location():
    response = client.post(
        "/api/v1/recommendations",
        json={
            "budget_band": "medium",
            "cuisines": [],
            "minimum_rating": 0.0,
        },
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, list)
    assert any(err.get("field") == "location" for err in detail)


def test_recommend_phase2_validation_error():
    # Phase2 business-logic validation (e.g. unknown city) should also return
    # the same unified 422 format.
    from phase2.preferences.service import ValidationError

    with patch(
        "phase6.api.routers.recommendations.get_recommendations",
        side_effect=ValidationError("Unknown location 'Xyz'. Provide a known city/locality from the dataset."),
    ):
        response = client.post(
            "/api/v1/recommendations",
            json={
                "location": "Xyz",
                "budget_band": "medium",
                "cuisines": [],
                "minimum_rating": 0.0,
            },
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, list)
    assert detail[0]["field"] == "location"
    assert "Unknown location" in detail[0]["message"]
    assert detail[0]["type"] == "validation_error"
