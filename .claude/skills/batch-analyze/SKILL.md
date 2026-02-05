---
name: batch-analyze
description: Use when processing multiple reviews from CSV files or analyzing large review datasets
---

# Batch Review Analysis

## Overview
Process multiple reviews simultaneously using the `/reviews/batch` API endpoint. Accepts CSV files and returns trust scores for each review.

## When to Use
- Analyzing historical review data
- Processing bulk exports from platforms
- Generating trust reports
- Data quality audits
- Testing model on real-world data

## Core Workflow

### 1. Prepare CSV File

**Required columns:**
- `platform` - google_maps, booking, agoda, tripadvisor
- `rating` - 1-5
- `user_id` - Reviewer ID
- `text` - Review content

**Example:**
```csv
platform,rating,user_id,text
google_maps,5,user123,"Amazing food! Free dessert!"
booking,4,user456,"Clean room, helpful staff"
```

### 2. Start Server
```bash
uv run uvicorn app.main:app --reload
```

### 3. Process via API

**Using curl:**
```bash
curl -X POST "http://localhost:8000/reviews/batch" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/sample_reviews.csv"
```

**Using Python:**
```python
import requests

with open('reviews.csv', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/reviews/batch',
        files={'file': f}
    )
    results = response.json()

for review in results:
    print(f"Trust: {review['trust_score']:.2f}, Suspicious: {review['is_suspicious']}")
```

### 4. Response Format
```json
[
  {
    "text": "Amazing food!",
    "trust_score": 0.23,
    "is_suspicious": true,
    "reasons": ["Promotional keywords detected"]
  }
]
```

## Using Web UI

1. Navigate to http://localhost:8000
2. Click "Batch Analysis" tab
3. Upload CSV file
4. View results in table

## Performance

| Size | Reviews | Time |
|------|---------|------|
| Small | < 100 | ~5s |
| Medium | 100-1000 | ~30s |
| Large | 1000-10000 | ~5min |

## Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| CSV parse error | Wrong encoding | Save as UTF-8 |
| Missing column | Header typo | Check column names |
| Model error | Not trained | `uv run python ml/train.py` |

## Quick Reference

```bash
# Start server
uv run uvicorn app.main:app --reload

# Process file
curl -X POST "http://localhost:8000/reviews/batch" \
  -F "file=@data/sample_reviews.csv" > results.json

# Run batch test
uv run pytest tests/test_batch_manual.py -v
```
