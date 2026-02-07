# Google Maps Place Analysis Feature Design

## Overview

Add a "Place Analysis" tab to the Web UI. Users can paste a Google Maps URL or search by place name. The system fetches the latest 20 reviews via SerpAPI, runs each through the existing hybrid analysis engine (ML + NLP + Semantic), and presents a trust summary report with expandable per-review details.

## Architecture

```
User Input (URL or keyword)
  -> Backend: detect input type
  -> SerpAPI: fetch place info + latest 20 reviews
  -> Existing analysis engine: score each review
  -> Aggregate into place trust report
  -> Return to UI: summary + expandable details
```

## API Design

### GET /places/search?q={keyword}

Search for places by keyword via SerpAPI Google Maps Search.

**Response:**
```json
{
  "results": [
    {
      "name": "Store Name",
      "address": "...",
      "rating": 4.5,
      "total_reviews": 320,
      "data_id": "0x...",
      "gps_coordinates": { "lat": 25.03, "lng": 121.56 }
    }
  ]
}
```

### POST /places/analyze

Analyze a place's reviews.

**Request:**
```json
{
  "query": "Google Maps URL or data_id",
  "api_key": "optional, user's own SerpAPI key"
}
```

**Response:**
```json
{
  "place": {
    "name": "...",
    "address": "...",
    "rating": 4.5,
    "total_reviews": 320
  },
  "summary": {
    "overall_trust_score": 0.72,
    "suspicious_count": 4,
    "total_analyzed": 20,
    "suspicious_ratio": 0.20,
    "key_findings": ["20% of reviews contain promotional keywords"]
  },
  "reviews": [
    {
      "text": "...",
      "rating": 5,
      "trust_score": 0.35,
      "is_suspicious": true,
      "reasons": ["Contains promotional keywords"],
      "author": "...",
      "date": "..."
    }
  ]
}
```

## Web UI Design

New third tab "Place Analysis" in the existing UI, with three sections:

### 1. Input Area
- Single input field: "Paste a Google Maps URL or enter a place name"
- Auto-detect URL vs keyword
- Keyword input shows candidate place list for user selection
- Expandable "Advanced Settings" for custom SerpAPI key
- "Analyze" button

### 2. Summary Report
- Place info card (name, address, Google rating, total review count)
- Overall trust score (large number + color indicator: green/yellow/red)
- Suspicious review ratio (e.g. "4 / 20 suspicious")
- Key findings summary (2-3 bullet points)

### 3. Review Details (collapsed by default)
- "View detailed review analysis" to expand
- Per-review card: author, date, star rating, text, trust score, suspicious reasons
- Red border for suspicious, green for trustworthy
- Sortable by trust score (suspicious first by default)

Visual style: match existing glassmorphism dark theme.

## SerpAPI Integration

### New module: `app/services/serpapi.py`

**Place Search:**
- SerpAPI `engine=google_maps`, `q=keyword`, `type=search`
- Parse `local_results` for name, address, rating, reviews count, data_id

**URL Parsing:**
- Support `maps.google.com/maps/place/...` and `goo.gl/maps/...` short URLs
- Extract place name or coordinates from URL, search via SerpAPI to get data_id

**Review Fetching:**
- SerpAPI `engine=google_maps_reviews`, `data_id=...`
- `sort_by=newestFirst`, `num=20`
- Parse each review: `snippet`, `rating`, `date`, `user.name`

**Error Handling:**
- Invalid API key: clear error message
- Place not found: prompt user to retry
- Quota exhausted: suggest switching key or retrying later

### Configuration
- `.env`: add `SERPAPI_KEY=your_key_here`
- `app/core/config.py`: add `serpapi_key` field

## API Key Management

- Backend `.env` holds default key
- Users can optionally enter their own key in UI
- Frontend sends key to backend; backend makes the SerpAPI call (key never exposed in client-side requests)
- Priority: user key > default key

## File Changes

| Action | File |
|--------|------|
| Add | `app/services/serpapi.py` |
| Add | `app/static/places.html` |
| Add | `tests/test_places.py` |
| Modify | `app/api/endpoints.py` |
| Modify | `app/core/config.py` |
| Modify | `app/static/index.html` (add tab link) |
| Modify | `.env` / `.env.example` |
| Modify | `pyproject.toml` (migrate to uv) |

## Package Management Migration

Migrate from setuptools + requirements.txt to `uv`:
- Install uv if not present
- Use `uv init` or adapt existing `pyproject.toml`
- Replace `pip install -r requirements.txt` with `uv sync`
- No new dependencies needed (SerpAPI called via `requests`, already in deps)

## Out of Scope

- No review caching or database storage (future enhancement)
- No user accounts or rate limiting
- No Chrome extension (future roadmap)
- No changes to existing analysis engine logic
- No pagination (fixed 20 reviews)

## Scoring

| Dimension | Score (1-10) | Notes |
|-----------|:------------:|-------|
| Innovation | 7 | Few competitors for Google Maps fake review detection, especially for Chinese + multilingual |
| Market Demand | 8 | Google Maps fake reviews is a known pain point; Taiwan market lacks such tools |
| Technical Feasibility | 9 | Core engine exists; just need SerpAPI integration + new UI |
| Business Potential | 6 | SerpAPI has costs; need freemium or B2B model for sustainability |
| MVP Leanness | 9 | Scope is well-controlled, clear exclusions |

## Future Roadmap

- Chrome extension for in-page analysis on Google Maps
- Review caching to reduce API costs on repeated queries
- User accounts with usage tracking
- Batch place analysis (multiple places at once)
- Export analysis report as PDF
