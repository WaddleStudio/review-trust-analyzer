# Review Trust Analyzer — Phase 1 開發簡報

> 本文件為 Claude Code / Cowork Desktop 執行用簡報，包含專案現狀、完整開發計畫、Agent 可加速環節、及具體實作指引。

---

## 一、專案現狀（V1 已完成）

### 已實現功能

- FastAPI 後端 API，Docker 容器化部署
- 真實 Google Maps 評論抓取整合（透過 SerpAPI）
- 混合評分系統（規則引擎 + 基礎 ML + 文字嵌入）
- 信任分數 0-1 輸出，PostgreSQL 儲存
- API 端點可供外部調用
- Vanilla HTML/JS 前端（glassmorphism 設計）：單筆分析、批次 CSV 上傳、商家評論分析（`/places`）
- NLP 情感分析整合（TextBlob，已合併 `feature/nlp-sentiment` 分支，v1.0.0）

### 技術架構

- **框架：** FastAPI + PostgreSQL + Docker
- **規則層：** 關鍵字偵測（中英文促銷詞庫）、文字長度、情感分數、用戶評論頻率（mock，待實作真實 DB 查詢）
- **ML 層：** Logistic Regression（sklearn），以 1,000 筆合成資料訓練（`ml/train.py`）
- **Embedding 層：** 本地 sentence-transformers（`paraphrase-multilingual-MiniLM-L12-v2`），語意相似度偵測灌水/模板化評論，免費無限額度

> **Note:** 現有 v2 升級設計文件 `docs/plans/2026-02-06-system-upgrade-design.md` 已包含 Qwen2.5 LLM 裁判、Cloudflare Tunnel 部署、閾值優化等詳細規劃，與 Phase 2 內容有重疊，實作時應參照該文件避免重複規劃。

---

## 二、三階段推進計畫

### Phase 1：自訓練模型開發（近期重點）⬅ 當前焦點

**目標：** 從通用規則升級為領域專精的分類模型

| 步驟 | 內容 |
|------|------|
| 資料收集 | 基於現有 SerpAPI 整合（`app/services/serpapi.py`）批次爬取 Google Maps 評論，目標 5,000+ 筆標註資料 |
| 特徵工程 | 結構特徵 + 語意特徵（embedding）+ 行為特徵（評分偏差） |
| 模型訓練 | scikit-learn（RandomForest / XGBoost），驗證後可升級 fine-tuned transformer |
| 評估管線 | precision / recall / F1 / AUC-ROC，precision 優先策略 |
| 部署策略 | 模型序列化後掛載到 FastAPI，與規則引擎並行，加權融合分數 |

**成本控制：** Embedding 使用本地 sentence-transformers（免費無限額度），SerpAPI 為付費服務需注意 API 用量

### Phase 2：LLM 裁判層（中期）

系統邏輯：

```
評論輸入
  → 規則引擎（硬判斷：0.0-1.0）
  → ML 模型（軟判斷：0.0-1.0）
  → 若兩者差異 > 閾值（e.g. 0.3）
      → LLM adjudicator（Claude / Gemini）
      → 結構化判決 + 理由
  → 最終信任分數 + 可解釋報告
```

LLM 只處理 ~5-15% 邊界案例，控制成本與延遲。

### Phase 3：OpenClaw Agent SDK 整合（中後期）

目標：將 Review Trust Analyzer 包裝為 Agent 可調用的工具 / 技能

使用場景：

1. **Review Monitor Agent（監控代理）**
   - Cron 觸發 → Agent 調用 Review Trust API → 偵測異常模式（短期大量高分湧入）→ Discord/LINE 通知
   - 包裝為 OpenClaw Agent Skill

2. **Competitive Intelligence Agent（競品情報代理）**
   - 輸入商家列表 → 批次分析 → 真實評分 vs 表面評分比較報告
   - B2B SaaS 核心賣點功能

3. **Multi-Agent 協作**
   - Review Agent（抓取分析）+ Report Agent（報告生成）+ Notification Agent（多通路通知）
   - Router 根據任務類型分配（multi-agent routing）

4. **跨專案整合**
   - Japan Trip OS：餐廳/景點評論可信度 → 旅行決策參考
   - Smart Menu Decision：推薦時加入評論可信度權重

---

## 三、Phase 1 — Agent / Code 可加速環節（具體實作指引）

### Step 1：批次爬取腳本

**目標：** 系統性收集 Google Maps 評論，建立訓練資料基礎

**現有基礎：** `app/services/serpapi.py` 已實作 `SerpAPIService`，包含 `search_places(query)` 和 `fetch_reviews(data_id, num)` 方法，支援分頁抓取（`next_page_token`）。

**需要擴展的功能：**

- 批次腳本：輸入商家 `data_id` 列表（SerpAPI 使用 `data_id`，非 `place_id`）→ 批次抓取所有評論 → 存入 PostgreSQL
- 自動去重（基於 content hash，SerpAPI 無穩定 review_id）
- 資料品質檢查：排除空評論、非目標語言、重複內容
- 進度追蹤：已抓商家數 / 評論總數 / 語言分布統計

**技術要求：**

- 擴展現有 `SerpAPIService`（`app/services/serpapi.py`），復用 `fetch_reviews()` 分頁邏輯
- SerpAPI 為付費 API，需注意用量控制（每次搜尋 = 1 credit）
- 加入 rate limiting 和 retry 機制（現有程式碼已有 `timeout=30` 但無 retry）

### Step 2：半自動標註管線（最高 ROI）

**目標：** 將 5,000 筆人工標註壓縮到 500-750 筆

**標註管線設計：**

```
原始評論
  → Rule Engine 預標註
      → 高信心（> 0.85）自動標為「真實」
      → 低信心（< 0.15）自動標為「可疑」
  → LLM 輔助標註（0.15-0.85 中間地帶）
      → Gemini Flash 批次判斷（Google AI Studio 免費額度）
      → 輸出 JSON：{ label, confidence, reasoning }
  → 人工審核（僅 LLM 不確定的 ~10-15%）
  → 標註結果存入 training_labels 表
```

**標註 UI（擴展現有前端）：**

- 現有前端：Vanilla HTML/JS + glassmorphism CSS（`app/static/`），已有 `index.html`（單筆/批次分析）和 `places.html`（商家分析），由 FastAPI `StaticFiles` 提供靜態服務
- 新增路由：`/admin/labeling`（新建 `app/static/labeling.html`，沿用現有 `style.css` 設計系統）
- 功能：顯示待標註評論 + 預判結果 → 人工 ✅/❌ 確認或翻轉 → 進度統計
- DB 表設計（通用結構，未來可跨專案復用）：

```sql
CREATE TABLE labeling_tasks (
    id SERIAL PRIMARY KEY,
    project_type VARCHAR(50) DEFAULT 'review_trust',  -- 跨專案識別
    source_id VARCHAR(255) NOT NULL,                   -- 原始資料 ID
    content_json JSONB NOT NULL,                       -- 評論內容（通用 JSON）
    pre_label VARCHAR(20),                             -- 規則/LLM 預標結果
    pre_confidence FLOAT,                              -- 預標信心度
    human_label VARCHAR(20),                           -- 人工最終標註
    status VARCHAR(20) DEFAULT 'pending',              -- pending / labeled / skipped
    labeled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

- 元件命名保持通用：`LabelingQueue`, `ReviewCard`, `ConfirmButton`
- 未來 SEEDCRAFT 標註教育內容品質、Smart Menu Decision 標註 OCR 結果 → 改 config + 換資料源即可復用

### Step 3：特徵工程腳本

**目標：** 一鍵從 raw reviews 計算全部特徵，寫入 `review_features` 表

**需要生成 `feature_engineering.py`：**

| 特徵類別 | 具體欄位 | 計算方式 |
|---------|---------|---------|
| 結構特徵 | 評論字數、標點比例、大寫比例、emoji 數量 | Python 文字處理 |
| 時序特徵 | 同商家評論時間間隔、用戶評論頻率、是否群發 | SQL 聚合 + pandas |
| 語意特徵 | embedding 向量、與同商家其他評論的餘弦相似度 | 本地 sentence-transformers（`features/semantic_features.py` 已實作） |
| 行為特徵 | 評分偏差（用戶平均分 vs 該評論分）、是否只給 5 星 / 1 星 | SQL 聚合 |

**現有基礎：** `features/` 目錄已有三個模組：
- `text_features.py`：文字長度、平均詞長、情感分數（TextBlob）、促銷關鍵字偵測（中英文詞庫）
- `semantic_features.py`：本地 sentence-transformers embedding + 對比式促銷分數（promo seeds vs safe seeds）
- `user_behavior_features.py`：**Mock 實作**（`user_review_count_last_30d` 固定回傳 1，`same_ip_review_count_last_7d` 固定回傳 0，含 TODO 註解待實作實際 DB 查詢）

新的 `feature_engineering.py` 應整合/擴展這些模組，而非重寫。

**流程：** 讀取 `raw_reviews` 表 → 計算全部特徵 → 寫入 `review_features` 表

### Step 4：模型訓練 + 評估管線

**目標：** 可重跑的訓練管線，每次新增標註資料後重跑持續改善

**需要生成 `train_pipeline.py`：**

```python
# 架構
1. load_data()        # 從 DB 讀取 features + labels
2. split_data()       # stratified train/val/test (70/15/15)
3. train_models()     # 同時跑 RandomForest / XGBoost / LightGBM
4. evaluate()         # precision, recall, F1, AUC-ROC，自動輸出比較表
5. select_best()      # 根據 precision 優先策略選最佳模型
6. serialize()        # joblib 序列化 → 存到指定路徑
7. generate_report()  # 自動產出訓練報告 markdown（含混淆矩陣圖）
```

**Precision 優先原因：** 誤判真評論為假的代價 > 漏放假評論

### Step 5：模型整合到現有 API

**目標：** 新模型無縫接入 FastAPI，不破壞現有 contract

**需要做的事：**

- 修改現有 FastAPI endpoint，加入模型推論路徑
- A/B 比較模式：同時回傳規則分數 + 模型分數 + 融合分數
- 整合測試確保不破壞現有 API contract
- 模型版本管理（model_version 欄位追蹤）

---

## 四、OpenClaw 跨 Phase 整合藍圖

### OpenClaw 現狀

- 自建 Agent 框架，運行於本機 WSL
- 已驗證能力：Cron 定時任務 + Discord 通知 + 外部 API 呼叫 + Notion 寫入
- 實測場景：定時抓取美股即時股價 → 存入 Notion
- 核心價值：**需要多步驟協調、定時觸發、或多工具串接**的場景

### Phase 1 整合點（資料工程加速）

**1. 評論收集 Cron Agent（對應 Step 1）**

- 定時觸發 → 呼叫 SerpAPI 抓新評論 → 存入 PostgreSQL → Discord 推送進度
- 動態決策：SerpAPI credit 快用完就暫停並通知、某商家評論夠多就跳過
- 每日摘要推送 `#rta-collect-log`：新增 X 筆、累計 Y 筆、距目標 Z 筆
- 直接復用已驗證的 Cron + API + Discord 模式

**2. 標註管線通知 Agent（對應 Step 2）**

- 監控 `labeling_tasks` 表 → 發現新 pending → Discord 推送「X 筆待人工審核」到 `#rta-labeling-queue`
- 規則引擎預標 + Gemini Flash 批次標註完成後 → 推送批次報告

**3. 訓練結果推送 Agent（對應 Step 4）**

- 訓練完成 → 讀取 evaluation report → 提取 precision/F1/AUC → Discord 推送到 `#rta-training-report`
- 指標低於閾值自動警告到 `#rta-alerts`

### Phase 2 整合點（LLM 裁判 + 監控）

**4. LLM 裁判觸發 Agent**

- 監控邊界案例佇列（trust score 30-70%）→ 批次送本地 Qwen2.5 → 寫回判定結果
- 結合 v2 設計文件（`docs/plans/2026-02-06-system-upgrade-design.md`）的 Ollama 整合方案

**5. 即時異常偵測 Agent**

- 監控特定商家（watchlist）→ 發現短時間大量高分湧入 → Discord 即時警報到 `#rta-alerts`
- 觸發條件可配置（例：24hr 內新增 >10 筆 5 星評論）

### Phase 3 整合點（產品化 + 跨專案）

**6. 競品情報定期報告 Agent**

- 輸入商家列表 → 批次分析 → 真實評分 vs 表面評分比較 → 定期報告推送 Discord + 存 Notion
- B2B SaaS 核心賣點功能原型

**7. 跨專案復用**

- Japan Trip OS：餐廳/景點評論可信度自動更新
- Smart Menu Decision：推薦權重自動調整
- 復用模式：OpenClaw 調用 Review Trust API → 結果寫入各專案資料庫

### 不需要 OpenClaw 的部分（純腳本即可）

- **特徵工程（Step 3）**：一次性計算腳本
- **模型訓練本身（Step 4 核心）**：`train_pipeline.py` 就是腳本
- **API 整合（Step 5）**：純程式碼修改
- **前端 UI 開發**：靜態檔案，無需 Agent

### 建議實作：統一 ReviewTrustAgent Skill

```
ReviewTrustAgent (OpenClaw Skill)
├── collect_reviews()     → 定時抓新評論（Phase 1）
├── notify_labeling()     → 標註進度/待審核通知（Phase 1）
├── report_training()     → 訓練結果推送（Phase 1）
├── trigger_llm_judge()   → 邊界案例批次送 LLM（Phase 2）
├── monitor_anomaly()     → 即時異常偵測（Phase 2）
└── generate_report()     → 競品情報定期報告（Phase 3）
```

**建議從 Phase 1 的 `collect_reviews()` 開始**，這是最接近已驗證場景（定時 API 呼叫 + 存資料庫 + Discord 通知）的擴展。Phase 1 就開始用 OpenClaw，到 Phase 3 擴展成完整 Review Monitor Agent 會非常順。

---

## 五、Discord 頻道設計

### Bot 策略

一個 Bot 即可，根據事件類型往不同頻道發送訊息。

### 頻道結構

```
📂 review-trust-analyzer
├── #rta-collect-log      → 資料收集進度（每日摘要：新增 X 筆、累計 Y 筆、距目標 Z 筆）
├── #rta-labeling-queue   → 標註管線通知（「32 筆待人工審核」、LLM 批次完成報告）
├── #rta-training-report  → 訓練結果推送（precision/F1/AUC 摘要、模型版本比較）
└── #rta-alerts           → 異常警報（API quota 快用完、爬取失敗、資料品質異常）
```

### 設計理由

- **collect-log** vs **labeling-queue** 分開：頻率不同（每日定時 vs 批次觸發），混在一起互相淹沒
- **alerts** 獨立：只對此頻道開通知，其他有空再看，避免通知疲勞
- **training-report** 頻率最低但內容最重要，獨立方便歷史比較
- 命名加 `rta-` prefix：未來跨專案擴展不衝突

### 未來擴展（現在不用建）

```
📂 review-trust-analyzer（現有）
📂 seedcraft（未來）
📂 japan-trip-os（未來）
📁 general
└── #agent-health         → 所有 Agent 心跳 / 錯誤彙整
```

---

## 六、執行順序與依賴關係

```
Step 1（批次爬取）→ 建立資料基礎
        ↓
Step 2（半自動標註）→ 最耗時環節，先啟動
        ↓ （Step 3 可在標註進行中同步開發）
Step 3（特徵工程）→ 標註完成前就可以先寫好腳本
        ↓
Step 4（訓練管線）→ 標註完成後一鍵跑
        ↓
Step 5（API 整合）→ 模型驗證通過後接入
```

---

## 七、商業化路徑

```
Free Tier:   50 次/月 API 查詢（個人用戶）
Pro Tier:    $9.99/月 — 1,000 次查詢 + 監控 Agent + 報告匯出
Enterprise:  客製化 — 批次分析 + 競品情報 + API 白標
```

---

## 八、版權 / IP 風險提醒

| 風險項目 | 狀態 | 建議 |
|---------|------|------|
| Google Maps 評論抓取（via SerpAPI） | 🟡 低風險 | 已使用 SerpAPI（合規第三方 API），非直接爬蟲；商用時需評估 SerpAPI 定價 |
| UGC 訓練資料 | 🟡 低風險 | 一般屬合理使用，但商用分發需加使用者同意條款 |
| 模型輸出 | ✅ 安全 | 原創分析結果，無 IP 問題 |
| API 回應 | 🟡 建議 | 標註資料來源，增加法律安全性 |

---

## 九、備註

- 以上開發前確認事項均已透過 codebase 審查解答：repo 結構見 `docs/plans/2026-02-06-system-upgrade-design.md` Section 3.3；前端為 Vanilla HTML/JS（`app/static/`）；API 使用 SerpAPI（需 `SERPAPI_KEY`）；PostgreSQL schema 見 `app/models.py`（3 張表：`reviews_raw`, `reviews_features`, `reviews_score`）；部署使用 Docker Compose（見 `docker-compose.yml`），目前無 CI/CD。
