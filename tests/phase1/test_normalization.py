import pytest
from phase1.ingestion.normalization import (
    normalize_text, normalize_location, normalize_cuisines,
    normalize_rating, normalize_cost
)

def test_normalize_text():
    assert normalize_text(None) == ""
    assert normalize_text("  hello  ") == "hello"

def test_normalize_location():
    # Detects: Location spellings vary, whitespaces
    assert normalize_location("  New   York  ") == "New York"
    assert normalize_location(None) == ""

def test_normalize_cuisines():
    # Detects: Cuisine as a single string with separators or malformed list
    assert normalize_cuisines("Italian, Chinese") == ["Italian", "Chinese"]
    assert normalize_cuisines("Italian/Chinese|Indian") == ["Italian", "Chinese", "Indian"]
    assert normalize_cuisines(None) == []

def test_normalize_rating():
    # Detects: Rating represented as text ("4.2/5", "NEW", "N/A").
    assert normalize_rating("4.2/5") == 4.2
    assert normalize_rating("NEW") is None
    assert normalize_rating("N/A") is None
    assert normalize_rating("  3.5  ") == 3.5
    assert normalize_rating("-1") is None  # Outlier (negative)
    assert normalize_rating("6.0") == 5.0  # Clamped to 5.0
    assert normalize_rating(None) is None

def test_normalize_cost():
    # Detects: Cost in mixed formats/currencies (₹800 for two, 1000, empty).
    assert normalize_cost("₹800 for two") == 800.0
    assert normalize_cost("$50.5") == 50.5
    assert normalize_cost("1,000") == 1000.0
    assert normalize_cost("N/A") is None
    assert normalize_cost("-100") is None  # Outlier
