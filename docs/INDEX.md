# Review Trust Analyzer — 文件索引

## 主要文件

| 文件 | 說明 |
|------|------|
| [README.md](../README.md) | 專案總覽、快速啟動、API 用法 |
| [TEST_CASES.md](./TEST_CASES.md) | 語意分析模組驗證案例（4 個邊界案例） |
| [MODEL_EVALUATION_REPORT.md](./MODEL_EVALUATION_REPORT.md) | v0.1.0 基準模型評估報告（歷史記錄） |

## 設計與計畫

| 文件 | 說明 | 狀態 |
|------|------|------|
| [review-trust-analyzer-phase1-briefing.md](./review-trust-analyzer-phase1-briefing.md) | Phase 1-3 完整路線圖與 OpenClaw 整合藍圖 | 🔄 進行中 |
| [plans/2026-02-06-system-upgrade-design.md](./plans/2026-02-06-system-upgrade-design.md) | v2 系統升級設計（閾值優化、LLM 裁判、Cloudflare Tunnel） | 🔄 P1 待辦 |
| [plans/2026-02-05-reduce-false-positives-negatives.md](./plans/2026-02-05-reduce-false-positives-negatives.md) | FP/FN 修復計畫（detect_promo_patterns 未實作） | 🔄 待辦 |

---

## 架構速覽

### 後端 (FastAPI)
- `app/main.py` — 應用入口
- `app/api/endpoints.py` — API 路由
- `app/models.py` — SQLModel 資料庫模型
- `app/database.py` — 資料庫連線設定
- `app/services/inference.py` — ML 推論服務
- `app/services/serpapi.py` — SerpAPI 整合（Google Maps）

### 機器學習
- `ml/train_pipeline.py` — 主要訓練管線（RandomForest/XGBoost）
- `ml/train.py` — 舊版簡易訓練腳本（Logistic Regression，合成資料）
- `ml/evaluate.py` — 評估模組（含 ground truth 測試案例）
- `ml/model.pkl` — 目前使用的訓練模型

### 特徵工程
- `features/text_features.py` — 文字特徵（TextBlob、中文促銷關鍵字）
- `features/semantic_features.py` — 語意相似度（sentence-transformers，對比分析）
- `features/user_behavior_features.py` — 用戶行為特徵（⚠️ Mock 實作，待連接真實 DB）

### 前端
- `app/static/index.html` — 單筆分析 + 批次上傳
- `app/static/places.html` — 商家評論分析
- `app/static/labeling.html` — 人工標註佇列
- `app/static/style.css` — 共用 Glassmorphism 樣式
- `app/static/script.js` — 前端互動邏輯（分析表單、批次上傳、Toast 通知）

### 腳本
- `scripts/fetch_batch_reviews.py` — 批次爬取 Google Maps 評論
- `scripts/feature_engineering.py` — 特徵計算管線
- `scripts/generate_pre_labels.py` — LLM 輔助預標籤

### 測試
- `tests/test_api.py` — API 端點測試
- `tests/test_features.py` — 特徵提取測試
- `tests/test_inference.py` — 推論服務測試
- `tests/test_serpapi.py` — SerpAPI 整合測試
- `tests/test_places.py` — Places 端點測試
- `tests/test_feature_engineering.py` — 特徵工程腳本測試
- `tests/test_batch_manual.py` — 批次處理手動測試

---

## 開發工作流

```bash
# 1. 安裝依賴
uv sync

# 2. 訓練模型
uv run python ml/train_pipeline.py

# 3. 啟動伺服器
uv run uvicorn app.main:app --reload

# 4. 執行測試
uv run pytest
```

Claude Code 技能：`/run-tests`, `/train-model`, `/evaluate-model`, `/batch-analyze`, `/docker-dev`

---

## 目前狀態

### 已實作 ✅
- Google Maps 評論抓取（SerpAPI）
- 混合評分引擎（規則 + ML + 語意）
- 前端 UI（單筆分析、Places、標註佇列）
- 批次 CSV 上傳處理

### 待辦 🔄
- `features/text_features.py` 中文促銷模式 regex（`detect_promo_patterns`）— 見 plans/2026-02-05
- 閾值優化（Grid Search，資料驅動）— 見 plans/2026-02-06
- Ollama + Qwen2.5-7B LLM 裁判整合 — 見 plans/2026-02-06
- `user_behavior_features.py` 真實 DB 查詢實作
- Cloudflare Tunnel 部署 — 見 plans/2026-02-06

---

**最後更新：** 2026-02-22
**版本：** 0.3.x（feature/nlp-sentiment branch）
