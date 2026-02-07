import re
from urllib.parse import unquote

import requests

from app.core.config import settings

SERPAPI_BASE = "https://serpapi.com/search"


class SerpAPIService:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.SERPAPI_KEY

    def is_google_maps_url(self, text: str) -> bool:
        patterns = [
            r"google\.\w+/maps",
            r"maps\.google\.",
            r"maps\.app\.goo\.gl",
            r"goo\.gl/maps",
        ]
        return any(re.search(p, text) for p in patterns)

    def parse_google_maps_url(self, url: str) -> str | None:
        """Extract place name from a Google Maps URL."""
        match = re.search(r"/maps/place/([^/@]+)", url)
        if match:
            return unquote(match.group(1).replace("+", " "))
        return None

    def search_places(self, query: str) -> list[dict]:
        """Search Google Maps for places matching the query."""
        params = {
            "engine": "google_maps",
            "q": query,
            "type": "search",
            "api_key": self.api_key,
        }
        resp = requests.get(SERPAPI_BASE, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("local_results", []):
            coords = item.get("gps_coordinates", {})
            results.append(
                {
                    "name": item.get("title", ""),
                    "address": item.get("address", ""),
                    "rating": item.get("rating"),
                    "total_reviews": item.get("reviews", 0),
                    "data_id": item.get("data_id", ""),
                    "gps_coordinates": {
                        "lat": coords.get("latitude"),
                        "lng": coords.get("longitude"),
                    },
                }
            )
        return results

    def fetch_reviews(self, data_id: str, num: int = 20) -> tuple[dict, list[dict]]:
        """Fetch reviews for a place by data_id."""
        params = {
            "engine": "google_maps_reviews",
            "data_id": data_id,
            "sort_by": "newestFirst",
            "num": num,
            "hl": "zh-TW",
            "api_key": self.api_key,
        }
        resp = requests.get(SERPAPI_BASE, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        pi = data.get("place_info", {})
        place_info = {
            "name": pi.get("title", ""),
            "address": pi.get("address", ""),
            "rating": pi.get("rating"),
            "total_reviews": pi.get("reviews", 0),
        }

        reviews = []
        for r in data.get("reviews", []):
            user = r.get("user", {})
            extracted = r.get("extracted_snippet", {})
            text = extracted.get("original") or r.get("snippet", "")
            reviews.append(
                {
                    "text": text,
                    "rating": r.get("rating"),
                    "author": user.get("name", "Anonymous"),
                    "date": r.get("date", ""),
                    "iso_date": r.get("iso_date", ""),
                }
            )
        return place_info, reviews
