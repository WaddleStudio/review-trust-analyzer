---
name: batch-analyze
description: Use when processing multiple reviews from CSV files or analyzing large review datasets
---

# Batch Review Analysis

## Overview
Process multiple reviews simultaneously using the `/reviews/batch` API endpoint. Accepts CSV files and returns trust scores, suspicious indicators, and detailed reasoning for each review.

## When to Use
- Analyzing historical review data
- Processing bulk exports from platforms (Google Maps, Booking.com, etc.)
- Generating trust reports for multiple reviews
- Data quality audits
- Research and statistical analysis
- Testing model performance on real-world data

## Core Workflow

### 1. Prepare CSV File

**Required columns:**
- `platform` - Review platform (google_maps, booking, agoda, tripadvisor)
- `rating` - Star rating (1-5)
- `user_id` - Reviewer identifier
- `text` - Review text content

**Example CSV:**
```csv
platform,rating,user_id,text
google_maps,5,user123,"Amazing food! Free dessert! 免費甜點！"
booking,4,user456,"Clean room, helpful staff"
agoda,5,user789,"超棒的體驗！推薦！"
```

### 2. Process via API

**Using curl:**
```bash
curl -X POST "http://localhost:8000/reviews/batch" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/sample_reviews.csv"
```

**Using Python requests:**
```python
import requests

with open('data/sample_reviews.csv', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/reviews/batch',
        files={'file': f}
    )
    results = response.json()

for review in results:
    print(f"Trust Score: {review['trust_score']:.2f}")
    print(f"Suspicious: {review['is_suspicious']}")
    print(f"Reasons: {review['reasons']}")
```

### 3. Analyze Results

**Response format:**
```json
[
  {
    "platform": "google_maps",
    "rating": 5,
    "user_id": "user123",
    "text": "Amazing food! Free dessert!",
    "trust_score": 0.23,
    "is_suspicious": true,
    "reasons": [
      "Promotional keywords detected (free)",
      "High semantic similarity to promotional patterns"
    ],
    "sentiment_score": 0.85
  }
]
```

## Using the Web UI

1. Start server: `python -m uvicorn app.main:app --reload`
2. Navigate to http://localhost:8000
3. Click "Batch Analysis" tab
4. Upload CSV file
5. View results in table format
6. Click rows to see detailed reasons

## CSV Format Requirements

**Validation rules:**
- File size: < 10MB (configurable)
- Encoding: UTF-8 (for multilingual support)
- Headers: Must include platform, rating, user_id, text
- Rating: Integer 1-5
- Platform: One of [google_maps, booking, agoda, tripadvisor]

**Common issues:**
- Extra spaces in headers → Trim whitespace
- Missing columns → Add with default values
- Non-UTF-8 encoding → Convert to UTF-8
- Invalid ratings → Filter out rows

## Sample Data

**Using built-in samples:**
```bash
# Test with provided sample data (20 reviews)
curl -X POST "http://localhost:8000/reviews/batch" \
  -F "file=@data/sample_reviews.csv"
```

**Generate test data:**
```python
import pandas as pd

reviews = [
    {"platform": "google_maps", "rating": 5, "user_id": "u1",
     "text": "Great service! 免費升級！"},
    {"platform": "booking", "rating": 4, "user_id": "u2",
     "text": "Clean and comfortable stay"},
]

df = pd.DataFrame(reviews)
df.to_csv('test_reviews.csv', index=False)
```

## Performance Considerations

**Batch size recommendations:**
- Small: < 100 reviews (~5 seconds)
- Medium: 100-1000 reviews (~30 seconds)
- Large: 1000-10000 reviews (~5 minutes)

**Optimization tips:**
- Model loads once and stays in memory (singleton pattern)
- Semantic analysis cached per unique text
- Use async processing for 1000+ reviews
- Consider pagination for very large files

## Output Formats

**Save results to file:**
```python
import json

# JSON format
with open('results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# CSV format with pandas
import pandas as pd
df = pd.DataFrame(results)
df.to_csv('results.csv', index=False, encoding='utf-8')

# Excel format
df.to_excel('results.xlsx', index=False)
```

## Analysis Patterns

**Flag all suspicious reviews:**
```python
suspicious = [r for r in results if r['is_suspicious']]
print(f"Found {len(suspicious)}/{len(results)} suspicious reviews")
```

**Calculate statistics:**
```python
import numpy as np

trust_scores = [r['trust_score'] for r in results]
print(f"Average trust: {np.mean(trust_scores):.2f}")
print(f"Min trust: {np.min(trust_scores):.2f}")
print(f"Max trust: {np.max(trust_scores):.2f}")
```

**Group by platform:**
```python
from collections import defaultdict

by_platform = defaultdict(list)
for r in results:
    by_platform[r['platform']].append(r['trust_score'])

for platform, scores in by_platform.items():
    print(f"{platform}: avg trust = {np.mean(scores):.2f}")
```

## Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| CSV parse error | Wrong encoding | Save as UTF-8 |
| Missing column error | Header typo | Check exact column names |
| Timeout on large files | > 10000 reviews | Split into smaller batches |
| Memory error | Model loading per row | Fixed in v0.1.0+ (singleton) |
| Wrong results | Model not trained | Run `python ml/train.py` |

## Quick Reference

```bash
# Simple batch analysis
curl -X POST "http://localhost:8000/reviews/batch" \
  -F "file=@data/sample_reviews.csv" > results.json

# With Python
python -c "
import requests
with open('data/sample_reviews.csv', 'rb') as f:
    r = requests.post('http://localhost:8000/reviews/batch', files={'file': f})
    print(r.json())
"

# Test in pytest
python -m pytest tests/test_batch_manual.py -v
```

## Real-World Impact

Batch processing enables:
- Automated review quality monitoring
- Historical data analysis (e.g., "How many fake reviews last month?")
- Platform comparison (e.g., "Which platform has most suspicious reviews?")
- Export to BI tools (Tableau, Power BI) for visualization
- Integration with review management systems

**Example use case:** A hotel chain processes 50,000 reviews monthly, flagging 5-10% as suspicious for manual review, saving 100+ hours of human verification time.
