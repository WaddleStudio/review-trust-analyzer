# Commit Log - Semantic Analysis & Batch Processing Update

Here are the suggested commit messages for the changes made in this session.

## 1. feat(nlp): Implement multilingual semantic analysis
**Files:**
- `requirements.txt`
- `features/semantic_features.py`
- `app/services/inference.py`

**Description:**
- Added `sentence-transformers` dependency.
- Implemented `calculate_semantic_promo_score` using `paraphrase-multilingual-MiniLM-L12-v2`.
- Defined `PROMO_SEEDS` for both English and Chinese promotional content.
- Integrated semantic scoring into `ModelService` with hybrid detection logic.

## 2. fix(nlp): Enhance semantic analysis accuracy
**Files:**
- `features/semantic_features.py`

**Description:**
- Added minimum text length filter (< 5 chars) to prevent false positives on short texts (e.g., "讚").
- Implemented **Contrastive Semantic Analysis** using `SAFE_SEEDS`.
- Added logic to compare similarity between promo seeds and safe seeds (e.g., "好吃給店家五星好評" is now correctly identified as safe).
- Added anti-promo patterns to handle negation (e.g., "沒送贈品也值得五星").

## 3. feat(batch): Add batch review analysis backend
**Files:**
- `app/api/endpoints.py`
- `data/sample_reviews.csv`

**Description:**
- Added `POST /reviews/batch` endpoint to accept CSV file uploads.
- Updated `ReviewResponse` model to include the review text.
- Optimized `ModelService` usage to avoid reloading the model on every batch request.
- Created `data/sample_reviews.csv` for testing purposes.

## 4. feat(ui): Implement batch upload and results interface
**Files:**
- `app/static/index.html`
- `app/static/script.js`
- `app/static/style.css`

**Description:**
- Added tab navigation for switching between Single Review and Batch Upload modes.
- Implemented file upload form and batch results table.
- Added "View Details" modal to display full review content from batch results.
- Updated CSS for wider layout support and responsive table design.
- Fixed syntax error in `script.js` and added `background-clip` compatibility in `style.css`.

## 5. docs: Add validation documentation
**Files:**
- `docs/TEST_CASES.md`
- `docs/screenshots/*`

**Description:**
- Documented key test cases (Chinese promo, short text, false positives, anti-promo).
- Included screenshots verifying the fixes for edge cases.
