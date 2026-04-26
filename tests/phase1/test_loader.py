import pytest
from unittest.mock import patch
from phase1.ingestion.loader import _coerce_restaurant, iter_restaurants

def test_coerce_restaurant_valid():
    row = {
        "name": "Test Res",
        "location": "Test City",
        "cuisines": "Italian, Chinese",
        "cost": "₹500 for two",
        "rating": "4.5/5",
        "id": "123"
    }
    mapping = {
        "name": "name", "location": "location", "cuisines": "cuisines",
        "cost": "cost", "rating": "rating", "id": "id"
    }
    res = _coerce_restaurant(row, mapping, 0)
    assert res is not None
    assert res.name == "Test Res"
    assert res.location == "Test City"
    assert res.cuisines == ["Italian", "Chinese"]
    assert res.cost == 500.0
    assert res.rating == 4.5
    assert res.restaurant_id == "123"

def test_coerce_restaurant_missing_name_or_location():
    # Detects: Empty location/cuisine causing unfilterable records
    mapping = {
        "name": "name", "location": "location", "cuisines": "cuisines",
        "cost": "cost", "rating": "rating", "id": "id"
    }
    row_no_name = {"name": "", "location": "City", "cuisines": "Italian", "cost": "500", "rating": "4.0", "id": "1"}
    assert _coerce_restaurant(row_no_name, mapping, 0) is None
    
    row_no_location = {"name": "Res", "location": "", "cuisines": "Italian", "cost": "500", "rating": "4.0", "id": "2"}
    assert _coerce_restaurant(row_no_location, mapping, 1) is None

@patch("phase1.ingestion.loader._iter_hf_rows")
def test_iter_restaurants_with_revision_pinning(mock_iter):
    # Detects: Dataset revision changes silently; schema drifts (Handling strategy: Pin dataset revision/version)
    mock_iter.return_value = iter([
        {"name": "Res1", "location": "Loc1", "cuisines": "C", "cost": "10", "rating": "3"}
    ])
    list(iter_restaurants(dataset_id="test/dataset", revision="v1.0"))
    mock_iter.assert_called_once_with(dataset_id="test/dataset", split="train", revision="v1.0")

@patch("phase1.ingestion.loader.load_dataset")
def test_hf_dataset_unreachable(mock_load_dataset):
    # Detects: Hugging Face dataset unreachable
    mock_load_dataset.side_effect = Exception("Network error")
    with pytest.raises(Exception, match="Network error"):
        from phase1.ingestion.loader import _iter_hf_rows
        list(_iter_hf_rows("dummy", "train", None))
