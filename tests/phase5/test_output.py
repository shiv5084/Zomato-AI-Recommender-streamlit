import json
import sys
from io import StringIO
from unittest.mock import patch
from phase5.output.render import render_recommendations, render_empty_state
from phase5.output.telemetry import TelemetryTracker

def test_render_empty_state():
    assert "No restaurants matched" in render_empty_state("no_candidates")
    assert "couldn't generate a valid ranking" in render_empty_state("llm_failed")
    assert "No recommendations available" in render_empty_state("unknown_reason")

def test_render_recommendations_empty():
    assert "couldn't generate a valid ranking" in render_recommendations([])

def test_render_recommendations_valid():
    rankings = [
        {
            "rank": 1,
            "explanation": "Great food and ambience.",
            "restaurant": {
                "restaurant_name": "Test Cafe",
                "cuisines": ["Cafe", "Desserts"],
                "rating": 4.5,
                "approx_cost_for_two_inr": 800
            }
        }
    ]
    
    output = render_recommendations(rankings)
    assert "# Top Restaurant Recommendations" in output
    assert "## 1. Test Cafe" in output
    assert "**Cuisines**: Cafe, Desserts" in output
    assert "**Rating**: 4.5 stars" in output
    assert "**Estimated Cost**: ₹800 for two" in output
    assert "**Why we recommend it**: Great food and ambience." in output

def test_telemetry_tracker():
    tracker = TelemetryTracker()
    tracker.start_timer("test_step")
    tracker.stop_timer("test_step")
    
    tracker.record_count("test_count", 5)
    
    assert "test_step" in tracker.metrics["latency_ms"]
    assert tracker.metrics["counts"]["test_count"] == 5
    
    with patch("sys.stderr", new=StringIO()) as mock_stderr:
        tracker.flush()
        stderr_output = mock_stderr.getvalue()
        assert "telemetry" in stderr_output
        parsed = json.loads(stderr_output)
        assert parsed["telemetry"]["counts"]["test_count"] == 5
