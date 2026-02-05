# Review Trust Analyzer v2 系統升級設計

> **For Claude:** 此文件為設計規格，實作時使用 superpowers:writing-plans 建立詳細實作計畫。

**Goal:** 升級檢測系統架構、優化專案結構、改善開發流程、建立本地部署方案。

**Architecture:** Hybrid 初篩 + 本地 LLM 裁判，資料驅動閾值優化，Cloudflare Tunnel 部署。

**Tech Stack:** Python/FastAPI, uv, Qwen2.5-7B (Ollama), Sentence-Transformers, Docker, Cloudflare Tunnel

---

## 1. 系統架構升級

### 1.1 檢測流程 (Hybrid + LLM 裁判)

```
┌─────────────────────────────────────────────────────────────┐
│                    Review Trust Analyzer v2                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   [評論輸入]                                                 │
│        │                                                     │
│        ▼                                                     │
│   ┌─────────────┐                                           │
│   │ Hybrid 初篩  │  ← 現有系統 (Rules + ML + Embeddings)     │
│   └─────────────┘                                           │
│        │                                                     │
│        ├── 明確可信 (>70%) ──────→ ✅ 直接通過               │
│        ├── 明確可疑 (<30%) ──────→ ❌ 直接標記               │
│        │                                                     │
│        └── 邊界案例 (30-70%) ───→ ┌─────────────┐           │
│                                    │ LLM 裁判    │           │
│                                    │ (Qwen2.5-7B)│           │
│                                    └─────────────┘           │
│                                          │                   │
│                                          ▼                   │
│                                    最終判定 + 標註收集        │
└─────────────────────────────────────────────────────────────┘
```

**設計決策：**
- 90% 案例用 Hybrid 秒判（快速、免費）
- 10% 邊界案例送本地 Qwen2.5-7B（準確、可控）
- LLM 判斷結果自動收集，累積訓練資料

### 1.2 LLM 配置

| 項目 | 選擇 | 原因 |
|------|------|------|
| 模型 | Qwen2.5-7B-Instruct | 中文能力最強 |
| 量化 | Q8 或 Q4 | 16GB VRAM 夠用 |
| 框架 | Ollama | 簡單、Docker 友善 |
| 呼叫時機 | Trust score 30-70% | 只處理邊界案例 |

---

## 2. 閾值優化流程

### 2.1 資料收集策略

```
┌──────────────────────────────────────────────────────────┐
│ A. SerpAPI 抓真實評論 (30-50 筆)                          │
│    → /places/analyze 抓評論                              │
│    → 匯出 CSV                                            │
│    → 人工標註 is_fake 欄位                               │
├──────────────────────────────────────────────────────────┤
│ B. LLM 生成邊界案例 (50-100 筆)                           │
│    → Qwen 生成各種情境                                   │
│    → 人工審核標籤                                        │
└──────────────────────────────────────────────────────────┘
         │
         ▼
    data/labeled/google_maps_reviews.csv
```

### 2.2 Grid Search 參數

```python
param_grid = {
    "semantic_threshold": [0.4, 0.5, 0.6, 0.7],
    "suspicious_threshold": [0.3, 0.4, 0.5],
    "trust_boost_threshold": [0.6, 0.7, 0.8],
}
# 評估指標: F1-score
```

### 2.3 產出檔案

- `data/labeled/google_maps_reviews.csv` — 標註資料
- `ml/optimize_thresholds.py` — 閾值優化腳本
- `app/core/config.py` — 可配置閾值（從 .env 讀取）

---

## 3. 專案目錄清理

### 3.1 刪除清單

| 檔案 | 原因 |
|------|------|
| `debug_full_flow.py` | 臨時除錯腳本，內容併入 skill |
| `integration_test_server.py` | 臨時測試腳本，內容併入 skill |
| `reproduce_500.py` | 臨時除錯腳本 |
| `test_db.py` | 臨時測試腳本，內容併入 skill |
| `COMMIT_LOG.md` | 可從 git log 取得 |
| `FRONTEND_DEMO.md` | 內容過時 |
| `VERSION_COMPARISON.md` | 內容過時 |
| `review_trust_analyzer.egg-info/` | 建置產物 |

### 3.2 .gitignore 更新

```gitignore
# Build artifacts
*.egg-info/
dist/
build/

# Environment
.venv/
.env
```

### 3.3 整理後目錄結構

```
review-trust-analyzer/
├── app/                    # FastAPI 應用
│   ├── api/
│   ├── core/
│   ├── services/
│   └── static/
├── features/               # 特徵工程
├── ml/                     # ML 訓練 + 評估
├── data/                   # 資料
│   └── labeled/            # [新增] 標註資料
├── tests/                  # 測試
├── docs/                   # 文件
│   └── plans/
├── verification/           # 驗證截圖
├── .claude/                # Claude Code 設定
│   └── skills/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## 4. Skill 更新

### 4.1 所有 Skill 統一使用 uv 指令

需更新檔案：
- `.claude/skills/dev-setup/SKILL.md`
- `.claude/skills/run-tests/SKILL.md`
- `.claude/skills/docker-dev/SKILL.md`
- `.claude/skills/train-model/SKILL.md`
- `.claude/skills/evaluate-model/SKILL.md`
- `.claude/skills/batch-analyze/SKILL.md`
- `README.md`

**指令對照：**

| 舊 (pip) | 新 (uv) |
|----------|---------|
| `pip install -r requirements.txt` | `uv sync` |
| `python script.py` | `uv run python script.py` |
| `pytest` | `uv run pytest` |
| `uvicorn app.main:app` | `uv run uvicorn app.main:app` |
| `pip install package` | `uv add package` |

### 4.2 /docker-dev 新增除錯區塊

```markdown
## Debugging Commands

**Test database connection:**
docker-compose exec app uv run python -c "
from app.core.config import settings
from sqlmodel import create_engine, Session, text
engine = create_engine(settings.DATABASE_URL)
with Session(engine) as s:
    print(s.exec(text('SELECT 1')).one())
"

**Test full analysis flow:**
docker-compose exec app uv run python -c "
from app.services.serpapi import SerpAPIService
svc = SerpAPIService()
print(f'API Key: {bool(svc.api_key)}')
"

**Test HTTP endpoint:**
curl -X POST http://localhost:8000/places/analyze \
  -H 'Content-Type: application/json' \
  -d '{"query": "測試店名"}'
```

### 4.3 /run-tests 新增整合測試區塊

```markdown
## Integration Tests

**With running server:**
# Terminal 1
uv run uvicorn app.main:app --port 8001

# Terminal 2
curl -X POST http://localhost:8001/places/analyze \
  -H 'Content-Type: application/json' \
  -d '{"query": "測試店名"}'
```

---

## 5. Docker 改善

### 5.1 修正 Hot Reload (Windows)

**docker-compose.yml 更新：**

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/review_trust_db
      - WATCHFILES_FORCE_POLLING=true  # Windows hot reload 修正
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=review_trust_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

### 5.2 未來：新增 Ollama 服務

```yaml
services:
  # ... existing services ...

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  postgres_data:
  ollama_data:
```

---

## 6. 部署方案 (Cloudflare Tunnel)

### 6.1 架構圖

```
┌─────────────────────────────────────────────────────────────┐
│   [本地電腦 - RTX 5060 Ti 16GB / RAM 32GB]                  │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  Docker Compose                                      │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│   │  │ FastAPI     │  │ PostgreSQL  │  │ Ollama      │  │   │
│   │  │ :8000       │  │ :5432       │  │ (Qwen2.5)   │  │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│   └─────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ▼                                  │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  Cloudflare Tunnel (cloudflared)                     │   │
│   │  localhost:8000 ──→ your-app.domain.com              │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   Cloudflare Edge      │
              │   (HTTPS, DDoS 保護)    │
              └────────────────────────┘
                           │
                           ▼
                      [使用者]
```

### 6.2 設定步驟

```bash
# 1. 安裝 cloudflared
winget install Cloudflare.cloudflared

# 2. 登入 Cloudflare
cloudflared tunnel login

# 3. 建立 tunnel
cloudflared tunnel create review-trust-analyzer

# 4. 設定 DNS
cloudflared tunnel route dns review-trust-analyzer app.yourdomain.com

# 5. 啟動 tunnel
cloudflared tunnel run review-trust-analyzer
```

### 6.3 資源需求確認

| 資源 | 需求 | 你的配置 | 狀態 |
|------|------|----------|------|
| RAM | ~15 GB | 32 GB | ✅ 充裕 |
| VRAM | ~8 GB (Q8) | 16 GB | ✅ 充裕 |
| Storage | ~20 GB | - | ✅ |

---

## 7. 實作優先順序

| 優先級 | 項目 | 預估工作量 |
|--------|------|-----------|
| P0 | 專案清理 + .gitignore | 30 分鐘 |
| P0 | Skills 更新為 uv 風格 | 1 小時 |
| P0 | Docker hot reload 修正 | 30 分鐘 |
| P1 | 閾值優化（資料收集 + Grid Search） | 2-3 小時 |
| P1 | 減少 False Positive/Negative（已有計畫） | 2 小時 |
| P2 | Ollama + Qwen2.5 整合 | 2-3 小時 |
| P2 | Cloudflare Tunnel 部署 | 1 小時 |
| P3 | LLM 裁判邏輯整合 | 2-3 小時 |

---

## 8. 決策記錄

| 問題 | 決策 | 原因 |
|------|------|------|
| 檢測方法 | B+C (強化 Hybrid + 開源 LLM) | 可行性高、成本低 |
| LLM 整合方式 | A (LLM 作為裁判) | 省資源、漸進式改善 |
| LLM 模型 | Qwen2.5-7B | 中文最強、16GB VRAM 可跑 |
| 閾值優化 | 資料驅動 (F1-score) | 取代硬編碼 magic numbers |
| 資料收集 | SerpAPI + LLM 生成 | 利用現有 API + 快速擴充 |
| 專案清理 | 激進清理 | 移除所有臨時檔案 |
| 套件管理 | uv | 快速、自動管理 venv |
| 部署方案 | Cloudflare Tunnel | 免費、用本地 GPU |
| 未來擴展 | 自架 VPS | 當本地不夠用時 |
