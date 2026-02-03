import pytest
from unittest.mock import patch, MagicMock
from app.core.config import settings


def test_settings_has_serpapi_key():
    assert hasattr(settings, "SERPAPI_KEY")


from app.services.serpapi import SerpAPIService


@pytest.fixture
def serpapi():
    return SerpAPIService(api_key="test_key")


def test_serpapi_service_init(serpapi):
    assert serpapi.api_key == "test_key"


def test_parse_google_maps_url():
    svc = SerpAPIService(api_key="test")
    # Standard URL with place name
    url = "https://www.google.com/maps/place/Taipei+101/@25.0339,121.5645"
    result = svc.parse_google_maps_url(url)
    assert result is not None
    assert "Taipei 101" in result or "Taipei+101" in result


def test_detect_input_type_url():
    svc = SerpAPIService(api_key="test")
    assert svc.is_google_maps_url("https://www.google.com/maps/place/Taipei+101") is True
    assert svc.is_google_maps_url("https://maps.app.goo.gl/abc123") is True
    assert svc.is_google_maps_url("Taipei 101") is False


@patch("app.services.serpapi.requests.get")
def test_search_places(mock_get, serpapi):
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "local_results": [
                {
                    "title": "Taipei 101",
                    "address": "No. 7, Section 5, Xinyi Road",
                    "rating": 4.5,
                    "reviews": 50000,
                    "data_id": "0x3442abc",
                    "gps_coordinates": {"latitude": 25.03, "longitude": 121.56},
                }
            ]
        },
    )
    results = serpapi.search_places("Taipei 101")
    assert len(results) == 1
    assert results[0]["name"] == "Taipei 101"
    assert results[0]["data_id"] == "0x3442abc"


@patch("app.services.serpapi.requests.get")
def test_fetch_reviews(mock_get, serpapi):
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "place_info": {
                "title": "Taipei 101",
                "address": "No. 7, Section 5, Xinyi Road",
                "rating": 4.5,
                "reviews": 50000,
            },
            "reviews": [
                {
                    "user": {"name": "John"},
                    "rating": 5,
                    "snippet": "Amazing place!",
                    "date": "2 months ago",
                    "iso_date": "2025-12-01T00:00:00Z",
                }
            ],
        },
    )
    place_info, reviews = serpapi.fetch_reviews("0x3442abc")
    assert place_info["name"] == "Taipei 101"
    assert len(reviews) == 1
    assert reviews[0]["text"] == "Amazing place!"
    assert reviews[0]["author"] == "John"
