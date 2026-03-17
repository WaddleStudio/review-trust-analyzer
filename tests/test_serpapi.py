import pytest
from unittest.mock import patch, MagicMock
from app.services.serpapi import SerpAPIService

@pytest.fixture
def service():
    return SerpAPIService(api_key="fake_key_123")

def test_is_google_maps_url(service: SerpAPIService):
    assert service.is_google_maps_url("https://goo.gl/maps/1234567") is True
    assert service.is_google_maps_url("https://maps.app.goo.gl/abcdefg") is True
    assert service.is_google_maps_url("https://www.google.com/maps/place/Foo") is True
    assert service.is_google_maps_url("https://www.yahoo.com") is False

def test_parse_google_maps_url(service: SerpAPIService):
    url = "https://www.google.com/maps/place/Ducky+Restaurant/@25.0435,121.5173,17z"
    assert service.parse_google_maps_url(url) == "Ducky Restaurant"
    assert service.parse_google_maps_url("https://goo.gl/maps/123") is None

@patch("app.services.serpapi.requests.get")
def test_get_account_info(mock_get, service: SerpAPIService):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"plan_searches_left": 95}
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    info = service.get_account_info()
    assert info["plan_searches_left"] == 95
    mock_get.assert_called_once()
