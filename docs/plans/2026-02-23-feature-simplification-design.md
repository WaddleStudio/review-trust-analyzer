# Feature Simplification & Phase 2 LLM Integration

> **For Claude:** 此文件為設計規格，實作時使用 superpowers:writing-plans 建立詳細實作計畫。

**Goal:** 精簡功能至核心工作流（Place Analysis + Labeling Queue），整合 Qwen3-14B 本地 LLM 裁判，並透過 OpenClaw 開放 Discord 遠端操控介面。

---

## 1. 功能去留決策

### 1.1 移除項目

| 項目 | 原因 |
|------|------|
| Single Review Analysis（`index.html`、`script.js`） | 其他平台無法串接真實評論來源，手動貼單筆使用率極低 |
| Batch Upload（`/reviews/batch` endpoint） | 實務上無使用，工作流已由 Place Analysis 取代 |
| `ReviewCreate` / `ReviewResponse` models | 隨對應 endpoint 一併移除 |
| `/reviews/score` endpoint | 同上 |
| `.claude/skills/batch-analyze/` skill | 對應功能移除 |

### 1.2 保留項目

| 項目 | 說明 |
|------|------|
| `app/static/places.html` | 唯一主介面 |
| `app/static/labeling.html` | 資料標記介面 |
| `app/services/inference.py` | Hybrid 初篩邏輯（Rules + ML），擴充 LLM 裁判 |
| `app/services/serpapi.py` | Google Maps 評論抓取 |
| `features/`、`ml/` | 特徵工程與 ML 模型，完整保留 |

### 1.3 路由調整

```python
# app/main.py
@app.get("/")
async def read_root():
    return RedirectResponse(url="/places")  # 改為 redirect

@app.get("/places")
async def read_places():
    return FileResponse('app/static/places.html')

@app.get("/admin/labeling")
async def read_labeling():
    return FileResponse('app/static/labeling.html')
```

---

## 2. Qwen3-14B LLM 裁判整合

### 2.1 檢測流程

```
Hybrid 初篩 (Rules + ML)
    │
    ├── trust_score > 0.70 → 直接通過 ✅  (llm_verdict = None, 不入佇列)
    ├── trust_score < 0.30 → 直接標記 ❌  (llm_verdict = None, 不入佇列)
    └── 0.30 ~ 0.70 → 呼叫 Qwen3-14B 裁判
                          │
                          ├── llm_verdict: "real" | "fake"
                          │   llm_reasoning: 中文推理說明
                          │
                          └── 自動寫入 LabelingTask ← NEW
                                  pre_label = llm_verdict
                                  pre_confidence = trust_score
                                  status = "pending"
                                  → /admin/labeling 等人工確認
                                  → (未來) OpenClaw Discord 按鈕推送
```

設計決策：90% 案例由 Hybrid 秒判（免費、快速），僅邊界案例送 LLM（準確、可控）。LLM 判斷結果自動入佇列，形成人機協作標記回路。

### 2.2 新增 `app/services/llm_judge.py`

```python
class LLMJudgeService:
    def __init__(self, base_url: str = "http://host.docker.internal:11434"):
        self.base_url = base_url
        self.model = "qwen3:14b"

    def judge(self, text: str, hybrid_score: float) -> dict:
        # POST {base_url}/api/generate
        # prompt: 給評論文本 + hybrid_score context，要求中文推理
        # 回傳: {"verdict": "real" | "fake", "reasoning": "..."}
```

**Prompt 設計原則：**
- 提供評論原文、目前 Hybrid 分數作為 context
- 要求模型以繁體中文說明判斷理由
- 輸出格式固定（JSON），方便解析

### 2.3 `inference.py` 擴充

`predict()` 新增回傳值：

```python
def predict(self, features: dict, text: str = "") -> tuple:
    # 現有：(trust_prob, is_suspicious, reasons, rule_score, model_score)
    # 擴充：(trust_prob, is_suspicious, reasons, rule_score, model_score,
    #         llm_verdict, llm_reasoning)
    #
    # llm_verdict / llm_reasoning 僅在 0.30~0.70 邊界案例有值，其餘為 None
```

### 2.4 API Schema 擴充

```python
class PlaceReviewResult(BaseModel):
    # ... 現有欄位 ...
    llm_verdict: Optional[str] = None      # "real" | "fake" | None
    llm_reasoning: Optional[str] = None    # 中文推理，邊界案例才有值
```

### 2.5 places.html 顯示調整

邊界案例 review card 額外顯示 LLM 裁判區塊：

```
┌─────────────────────────────────────────────┐
│  ★★★★☆  2025/01/15  作者名                  │
│  評論內容...                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━  68%             │
│  [promotional keywords]                      │
│  🤖 LLM 裁判: 可疑                           │
│  "用詞模板化，缺乏具體消費細節，..."           │
└─────────────────────────────────────────────┘
```

---

## 3. 部署架構（WSL2 + Ollama）

### 3.1 整體架構

```
[Windows Host]
    ├── Docker Desktop (WSL2 backend)
    │     ├── FastAPI :8000
    │     │     └── OLLAMA_URL=http://host.docker.internal:11434
    │     └── PostgreSQL :5432
    └── WSL2 (2.6.1)
          ├── OpenClaw (Discord 控制介面)
          └── Ollama :11434
                └── Qwen3-14B (透過 Windows NVIDIA 驅動存取 5060 Ti)
```

### 3.2 選型原因

| 方案 | 評估 |
|------|------|
| Ollama in Docker（GPU passthrough） | 需額外裝 NVIDIA Container Toolkit，Windows 上設定複雜 |
| Ollama native on Windows | 與 OpenClaw（WSL2）跨環境，管理不便 |
| **Ollama native in WSL2（採用）** | WSL2 已存在、GPU 透過 Windows 驅動自動繼承、OpenClaw 同環境可直接管理 |

### 3.3 Ollama 安裝（WSL2）

```bash
# 安裝 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 拉取模型（9.3GB）
ollama pull qwen3:14b

# 確認 GPU 已啟用
ollama ps
```

CUDA 前提：Windows NVIDIA 驅動支援 CUDA 12.8+（RTX 5060 Ti / Blackwell 架構需求）。WSL2 無需另裝 Linux 驅動，Ollama 自帶 CUDA 函式庫。

### 3.4 docker-compose.yml 調整

```yaml
# 移除 ollama service block
# app service 新增環境變數：
app:
  environment:
    - OLLAMA_URL=http://host.docker.internal:11434
```

### 3.5 .env 新增

```bash
OLLAMA_URL=http://host.docker.internal:11434  # Docker 環境
# OLLAMA_URL=http://localhost:11434           # 本機直接跑時
```

---

## 4. OpenClaw 整合

### 4.1 新增 `GET /api/status` endpoint

供 OpenClaw 定期呼叫做健康監控：

```json
{
  "server": "ok",
  "ollama": "ok" | "unavailable",
  "ollama_model": "qwen3:14b",
  "labeling_pending": 12,
  "serpapi_credits": 85
}
```

### 4.2 Discord 指令清單

| 指令 | OpenClaw 執行 | 說明 |
|------|--------------|------|
| 分析 [地點] | `POST /places/analyze` | 回傳摘要（信任分數、可疑比例、LLM 裁判結果） |
| 系統狀態 | `GET /api/status` | 一鍵確認所有服務健康 |
| 跑測試 | `uv run pytest` | 回報通過/失敗數 |
| 重新訓練 | `uv run python ml/train.py` | 回報訓練完成 |
| 待標記數量 | `GET /api/labeling/pending` | 顯示 queue 狀態 |
| 重啟 server | `pkill uvicorn && uv run uvicorn app.main:app` | 遠端重啟 |
| 更新模型 | `ollama pull qwen3:14b` | 拉取最新版本 |

### 4.3 Discord 互動式標記流程

OpenClaw 拉取待標記資料後，以帶按鈕的訊息逐筆推送：

```
┌─────────────────────────────────────────────┐
│  📋 待標記 #42    Pre-label: 可疑 (68%)      │
│                                              │
│  "這家餐廳真的太棒了！服務員很熱情，食物非常   │
│   美味，環境乾淨，下次一定再來！CP值超高"      │
│                                              │
│  [✅ 真實]   [❌ 假評論]   [⏭️ 跳過]          │
└─────────────────────────────────────────────┘
```

點選後 OpenClaw 呼叫 `POST /api/labeling/{task_id}/submit`，並自動推送下一筆。

**後端無需改動**，現有 labeling endpoint 已足夠支援此流程。

---

## 5. 實作優先順序

| 優先級 | 項目 | 說明 |
|--------|------|------|
| P0 | 功能精簡 | 移除 index.html、script.js、兩個 endpoint、batch-analyze skill |
| P0 | 路由調整 | `GET /` redirect 到 `/places` |
| P1 | Ollama 環境建立 | WSL2 安裝 + `ollama pull qwen3:14b` |
| P1 | `llm_judge.py` 新增 | Ollama HTTP 呼叫封裝 |
| P1 | `inference.py` 擴充 | 邊界案例接入 LLM 裁判 |
| P1 | API schema 擴充 | `PlaceReviewResult` 加 llm 欄位 |
| P1 | `places.html` 顯示調整 | LLM 裁判區塊 |
| P2 | `GET /api/status` | OpenClaw 健康監控 endpoint |
| P2 | OpenClaw Discord 指令 | 依 4.2 清單設定 |
| P3 | Discord 互動式標記 | 4.3 按鈕流程 |

---

## 6. 決策記錄

| 問題 | 決策 | 原因 |
|------|------|------|
| Single Review 去留 | 移除 | 其他平台無法串接真實資料，失去核心價值 |
| Batch Upload 去留 | 移除 | 實務上無使用 |
| LLM 模型選擇 | Qwen3-14B | 比 Qwen2.5-7B/14B 更新一代，9.3GB 符合 16GB VRAM |
| Qwen3.5 | 暫不採用 | 目前只有 397B MoE 旗艦版，等小尺寸版本發布後評估升級 |
| Ollama 部署位置 | WSL2 原生 | OpenClaw 同環境、GPU 透過 Windows 驅動繼承、設定最簡單 |
| LLM 呼叫時機 | trust_score 0.30~0.70 | 省資源，僅處理邊界案例 |
| 標記流程 | Discord 互動按鈕 | 手機即可操作，無需開啟 Web UI |
