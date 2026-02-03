from app.core.config import settings


def test_settings_has_serpapi_key():
    assert hasattr(settings, "SERPAPI_KEY")
