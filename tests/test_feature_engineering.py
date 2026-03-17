import pytest
from scripts.fetch_batch_reviews import generate_review_hash, is_valid_review

def test_is_valid_review():
    assert is_valid_review("This is a lovely place.") is True
    # Too short
    assert is_valid_review("hi") is False
    # English/Chinese accepted mostly, assuming alphabet > 5
    assert is_valid_review("        ") is False

def test_generate_review_hash():
    h1 = generate_review_hash("Alice", "Great food", "2023-01-01")
    h2 = generate_review_hash("Alice", "Great food", "2023-01-01")
    h3 = generate_review_hash("Bob", "Great food", "2023-01-01")
    
    assert h1 == h2
    assert h1 != h3
