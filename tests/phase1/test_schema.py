import pytest
from phase1.ingestion.schema import build_field_mapping, assert_row_matches_mapping

def test_build_field_mapping_success():
    columns = ["restaurant_name", "city", "cuisines", "average_cost_for_two", "aggregate_rating", "res_id"]
    mapping = build_field_mapping(columns)
    assert mapping["name"] == "restaurant_name"
    assert mapping["location"] == "city"
    assert mapping["cuisines"] == "cuisines"
    assert mapping["cost"] == "average_cost_for_two"
    assert mapping["rating"] == "aggregate_rating"
    assert mapping["id"] == "res_id"

def test_build_field_mapping_missing_required():
    # Detects: Missing required columns (name, location, rating, etc.).
    columns = ["restaurant_name", "city"] # missing cuisines, cost, rating
    with pytest.raises(ValueError, match="Could not map required field"):
        build_field_mapping(columns)

def test_assert_row_matches_mapping():
    mapping = {"name": "restaurant_name"}
    row = {"restaurant_name": "Pizza Hut"}
    assert_row_matches_mapping(row, mapping)  # Should not raise

    with pytest.raises(ValueError, match="Row is missing mapped fields"):
        assert_row_matches_mapping({}, mapping)
