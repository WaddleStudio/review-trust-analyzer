# Documentation Cleanup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 去蕪存菁 — 刪除已完成的計畫文件、修正過時索引、移除暫存垃圾檔案，讓 `docs/` 只留有效參考。

**Architecture:** 純文件整理，不動程式碼。三類操作：(1) 刪除，(2) 重寫 INDEX.md，(3) 移除根目錄雜物。

**Tech Stack:** git, bash

---

## 分析結論

| 檔案 | 狀態 | 動作 |
|------|------|------|
| `docs/plans/2026-02-04-google-maps-place-analysis-design.md` | ✅ 功能已實作，設計文件過時 | **DELETE** |
| `docs/plans/2026-02-04-google-maps-place-analysis-impl.md` | ✅ 功能已實作，實作計畫已完成 | **DELETE** |
| `docs/plans/2026-02-05-reduce-false-positives-negatives.md` | ✅ FP/FN 修復已合併進主線 | **DELETE** |
| `docs/plans/2026-02-06-system-upgrade-design.md` | 🔄 P1 待辦事項仍有效 | **KEEP** |
| `docs/INDEX.md` | ❌ 引用不存在的檔案 (FRONTEND_DEMO.md, VERSION_COMPARISON.md, COMMIT_LOG.md)，路徑錯誤 | **REWRITE** |
| `docs/MODEL_EVALUATION_REPORT.md` | 📁 歷史資料，v0.1.0 Logistic Regression | **KEEP**（標記為歷史） |
| `docs/review-trust-analyzer-phase1-briefing.md` | 📋 完整三階段路線圖，仍是有效參考 | **KEEP** |
| `docs/TEST_CASES.md` | ✅ 4 個語意分析測試案例，仍有效 | **KEEP** |
| `README.md` | ✅ 準確，維護良好 | **KEEP** |
| `out.txt` | 🗑️ 臨時輸出 | **DELETE** |
| `pytest_out.txt` | 🗑️ 臨時測試輸出 | **DELETE** |
| `review_trust_analyzer.egg-info/` | 🗑️ 建置產物，應被 gitignore | **DELETE** |
| `requirements.txt` | ⚠️ 舊版依賴管理（已改用 uv） | **DELETE**（pyproject.toml + uv.lock 已取代） |

---

### Task 1: 刪除已完成的計畫文件

**Files:**
- Delete: `docs/plans/2026-02-04-google-maps-place-analysis-design.md`
- Delete: `docs/plans/2026-02-04-google-maps-place-analysis-impl.md`
- Delete: `docs/plans/2026-02-05-reduce-false-positives-negatives.md`

**Step 1: 確認這些功能確實已實作**

Run:
```bash
# SerpAPI 服務存在
ls app/services/serpapi.py

# Places 端點存在
grep -n "places" app/api/endpoints.py | head -5

# FP/FN 修復功能存在（promo patterns）
grep -n "detect_promo_patterns\|PROMO_PATTERNS" features/text_features.py | head -5
```

Expected: 三個命令都有輸出，確認功能已落地。

**Step 2: 刪除過時計畫文件**

Run:
```bash
git rm docs/plans/2026-02-04-google-maps-place-analysis-design.md
git rm docs/plans/2026-02-04-google-maps-place-analysis-impl.md
git rm docs/plans/2026-02-05-reduce-false-positives-negatives.md
```

Expected: 三個檔案被標記為 staged deletion。

**Step 3: Commit**

```bash
git commit -m "docs: remove completed implementation plans (place analysis + FP/FN fix)"
```

---

### Task 2: 重寫 docs/INDEX.md

**Files:**
- Modify: `docs/INDEX.md`

**Step 1: 驗證 INDEX.md 中哪些連結已損壞**

Run:
```bash
# 確認以下不存在
ls FRONTEND_DEMO.md VERSION_COMPARISON.md COMMIT_LOG.md 2>&1
```

Expected: `No such file or directory` 三個都不存在。

**Step 2: 確認實際存在的測試檔案**

Run:
```bash
ls tests/
ls ml/
```

Expected:
- `tests/` 包含: `test_api.py`, `test_features.py`, `test_batch_manual.py`, `test_places.py`, `test_serpapi.py`, `test_inference.py`, `test_feature_engineering.py`
- `ml/` 包含: `train.py`, `train_pipeline.py`, `evaluate.py`, `model.pkl`

**Step 3: 重寫 INDEX.md**

用以下內容完整替換 `docs/INDEX.md`：

```markdown
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

---

## 架構速覽

### 後端 (FastAPI)
- `app/main.py` — 應用入口
- `app/api/endpoints.py` — API 路由
- `app/models.py` — SQLModel 資料庫模型
- `app/services/inference.py` — ML 推論服務
- `app/services/serpapi.py` — SerpAPI 整合（Google Maps）

### 機器學習
- `ml/train_pipeline.py` — 主要訓練管線（RandomForest/XGBoost）
- `ml/train.py` — 舊版簡易訓練腳本（Logistic Regression，合成資料）
- `ml/evaluate.py` — 評估模組（含 ground truth 測試案例）
- `ml/model.pkl` — 目前使用的訓練模型

### 特徵工程
- `features/text_features.py` — 文字特徵（TextBlob、中文促銷模式 regex）
- `features/semantic_features.py` — 語意相似度（sentence-transformers，對比分析）
- `features/user_behavior_features.py` — 用戶行為特徵（⚠️ Mock 實作，待連接真實 DB）

### 前端
- `app/static/index.html` — 單筆分析 + 批次上傳
- `app/static/places.html` — 商家評論分析
- `app/static/labeling.html` — 人工標註佇列
- `app/static/style.css` — 共用 Glassmorphism 樣式

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
- 中文促銷模式偵測（打卡送X、好評送X 等）
- 前端 UI（單筆分析、Places、標註佇列）
- 批次 CSV 上傳處理

### 待辦 🔄（見 2026-02-06-system-upgrade-design.md）
- 閾值優化（Grid Search，資料驅動）
- Ollama + Qwen2.5-7B LLM 裁判整合
- `user_behavior_features.py` 真實 DB 查詢實作
- Cloudflare Tunnel 部署

---

**最後更新：** 2026-02-22
**版本：** 0.3.x（feature/nlp-sentiment branch）
```

**Step 4: Commit**

```bash
git add docs/INDEX.md
git commit -m "docs: rewrite INDEX.md to fix broken links and reflect actual codebase"
```

---

### Task 3: 刪除根目錄雜物

**Files:**
- Delete: `out.txt`
- Delete: `pytest_out.txt`
- Delete: `review_trust_analyzer.egg-info/` (directory)
- Delete: `requirements.txt`

**Step 1: 確認 requirements.txt 內容已被 pyproject.toml 涵蓋**

Run:
```bash
cat requirements.txt
grep -A 20 "\[project\]" pyproject.toml | head -25
```

Expected: `requirements.txt` 中的所有依賴都存在於 `pyproject.toml` 的 `dependencies` 列表中。

**Step 2: 刪除雜物**

Run:
```bash
git rm out.txt pytest_out.txt requirements.txt
git rm -r review_trust_analyzer.egg-info/
```

Expected: 所有檔案被標記為 staged deletion。

**Step 3: 更新 .gitignore 防止 egg-info 再次出現**

確認 `.gitignore` 已包含：
```
*.egg-info/
```

Run:
```bash
grep "egg-info" .gitignore
```

Expected: 輸出 `*.egg-info/`（根據 system-upgrade-design.md Section 3.2，這應該已完成）。

如果沒有，手動新增：
```bash
echo "*.egg-info/" >> .gitignore
git add .gitignore
```

**Step 4: Commit**

```bash
git commit -m "chore: remove temp files and build artifacts (out.txt, pytest_out.txt, egg-info, requirements.txt)"
```

---

## 完成後狀態

```
docs/
├── INDEX.md                          ✅ 更新（正確連結、完整架構）
├── MODEL_EVALUATION_REPORT.md        📁 保留（歷史基準記錄）
├── TEST_CASES.md                     ✅ 保留（語意分析邊界案例）
├── review-trust-analyzer-phase1-briefing.md  ✅ 保留（完整路線圖）
├── plans/
│   └── 2026-02-06-system-upgrade-design.md  🔄 保留（P1 待辦）
└── screenshots/                      ✅ 保留（驗證截圖）
```

**刪除：** 3 個完成的計畫文件 + 4 個根目錄雜物 = **7 個檔案清除**
