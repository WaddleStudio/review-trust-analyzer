# Superpowers 技能系統說明

## 簡介

本專案已整合 [Superpowers](https://github.com/obra/superpowers) AI 代理技能框架，提供結構化的開發工作流程自動化。Superpowers 是一個為 AI 編碼代理設計的綜合性軟體開發方法論，透過可組合的「技能」與智慧自動化來引導代理完成整個開發生命週期。

## 什麼是 Superpowers？

Superpowers 提供：
- **7 階段開發方法論**：設計 → 環境設置 → 規劃 → 執行 → 開發 → 審查 → 完成
- **可組合的技能庫**：測試、協作與元操作工具
- **結構化代理指導**：使用蘇格拉底式提問而非直接編碼
- **內建支援**：Git worktrees、TDD 循環、程式碼審查工作流程

## 可用技能

本專案提供以下客製化技能，專為 Review Trust Analyzer 工作流程優化：

### 1. `/train-model` - 訓練機器學習模型

**用途：** 當需要訓練或重新訓練 ML 模型時使用

**功能：**
- 生成合成訓練資料
- 訓練 Logistic Regression 分類器
- 儲存模型至 `ml/model.pkl`
- 顯示訓練指標（準確率、精確率、召回率）

**使用方式：**
```bash
python ml/train.py
```

**預期結果：**
- 建立/更新 `ml/model.pkl` 檔案
- 準確率 > 85%
- 顯示詳細的效能指標

📖 [詳細說明](skills/train-model/SKILL.md)

---

### 2. `/dev-setup` - 開發環境設置

**用途：** 首次設置本地開發環境或全新檢出後使用

**功能：**
- 安裝 Python 相依套件
- 下載 NLP 模型（TextBlob、Sentence Transformers）
- 訓練初始 ML 模型
- 啟動 FastAPI 開發伺服器

**使用方式：**
```bash
# 完整設置流程
pip install -r requirements.txt
python ml/train.py
python -m uvicorn app.main:app --reload
```

**驗證清單：**
- ✅ `ml/model.pkl` 已建立
- ✅ 伺服器成功啟動
- ✅ http://localhost:8000 顯示 UI
- ✅ 測試通過：`python -m pytest`

📖 [詳細說明](skills/dev-setup/SKILL.md)

---

### 3. `/run-tests` - 執行測試套件

**用途：** 執行測試、驗證程式碼變更、除錯測試失敗時使用

**功能：**
- 執行 pytest 測試套件
- 提供詳細輸出與覆蓋率報告
- 測試 API 端點、特徵萃取、批次處理

**使用方式：**
```bash
# 基本測試
python -m pytest

# 詳細輸出
python -m pytest -v

# 附帶覆蓋率報告
python -m pytest --cov=app --cov=features --cov-report=term-missing
```

**測試範圍：**
- `tests/test_api.py` - FastAPI 端點測試
- `tests/test_features.py` - 特徵萃取測試
- `tests/test_batch_manual.py` - 批次處理測試

📖 [詳細說明](skills/run-tests/SKILL.md)

---

### 4. `/batch-analyze` - 批次評論分析

**用途：** 處理 CSV 檔案中的多筆評論或分析大型評論資料集

**功能：**
- 接受 CSV 檔案上傳
- 批次計算信任分數
- 返回每筆評論的可疑標記與詳細原因
- 支援多語言（英文/中文）

**CSV 格式要求：**
```csv
platform,rating,user_id,text
google_maps,5,user123,"超棒的體驗！免費贈品！"
booking,4,user456,"房間乾淨，服務親切"
```

**使用方式：**
```bash
# 透過 API
curl -X POST "http://localhost:8000/reviews/batch" \
  -F "file=@data/sample_reviews.csv"

# 或使用 Web UI
# 1. 訪問 http://localhost:8000
# 2. 點擊「批次分析」標籤
# 3. 上傳 CSV 檔案
```

📖 [詳細說明](skills/batch-analyze/SKILL.md)

---

### 5. `/evaluate-model` - 模型效能評估

**用途：** 評估模型效能、比較版本或分析分類指標

**功能：**
- 計算準確率、精確率、召回率、F1 分數
- 生成混淆矩陣
- 識別改善領域
- 追蹤模型版本間的效能變化

**使用方式：**
```bash
python ml/evaluate.py
```

**輸出範例：**
```
模型評估結果
========================
準確率 (Accuracy):  0.91 (91%)
精確率 (Precision): 1.00 (100%)
召回率 (Recall):    0.47 (47%)
F1 分數:            0.64

混淆矩陣:
                預測為正常  預測為可疑
實際為正常            540         0
實際為可疑            240       220
```

**效能基準：**
- 目前版本 v0.1.0：準確率 91%，精確率 100%，召回率 47%
- 目標 v0.2.0+：準確率 > 93%，精確率 > 95%，召回率 > 70%

📖 [詳細說明](skills/evaluate-model/SKILL.md)

---

### 6. `/docker-dev` - Docker 開發環境

**用途：** 使用 Docker 設置容器化開發環境或部署

**功能：**
- 使用 Docker Compose 啟動 FastAPI + PostgreSQL
- 自動化資料庫初始化
- 程式碼熱重載（透過 volume mounting）
- 生產環境模擬

**使用方式：**
```bash
# 啟動容器
docker-compose up --build

# 背景執行
docker-compose up -d

# 檢視日誌
docker-compose logs -f app

# 在容器內執行命令
docker-compose exec app python -m pytest

# 停止並清理
docker-compose down -v
```

**服務存取：**
- 前端 UI: http://localhost:8000
- API 文件: http://localhost:8000/docs
- PostgreSQL: localhost:5432

📖 [詳細說明](skills/docker-dev/SKILL.md)

---

## 如何使用技能

### 方法 1：直接在 Claude Code 中使用

如果您使用的是 Claude Code CLI，可以直接呼叫技能：

```bash
/train-model      # 訓練模型
/dev-setup        # 設置開發環境
/run-tests        # 執行測試
/batch-analyze    # 批次分析
/evaluate-model   # 評估模型
/docker-dev       # Docker 環境
```

### 方法 2：透過 AI 代理自動觸發

當您與 Claude 代理互動時，技能會根據上下文自動觸發。例如：

- 詢問「我該如何設置專案？」→ 自動建議 `/dev-setup`
- 提到「測試失敗了」→ 自動建議 `/run-tests`
- 討論「模型表現」→ 自動建議 `/evaluate-model`

### 方法 3：手動執行命令

每個技能都對應到標準的 Python/Docker 命令，可直接在終端執行：

| 技能 | 對應命令 |
|------|---------|
| train-model | `python ml/train.py` |
| dev-setup | `pip install -r requirements.txt && python ml/train.py && uvicorn app.main:app --reload` |
| run-tests | `python -m pytest -v` |
| batch-analyze | `curl -X POST "http://localhost:8000/reviews/batch" -F "file=@data.csv"` |
| evaluate-model | `python ml/evaluate.py` |
| docker-dev | `docker-compose up --build` |

---

## 建立自訂技能

如果您想為專案新增自訂技能，請遵循以下步驟：

### 1. 建立技能目錄

```bash
mkdir -p .claude/skills/your-skill-name
```

### 2. 建立 SKILL.md 檔案

技能使用 **Markdown 格式搭配 YAML 前置資料**：

```markdown
---
name: your-skill-name
description: Use when [觸發條件描述]
---

# 技能名稱

## 概述
簡要說明技能的核心功能與原理。

## 何時使用
- 具體使用情境 1
- 具體使用情境 2

## 核心工作流程

### 1. 步驟一
詳細說明...

### 2. 步驟二
詳細說明...

## 快速參考
\```bash
# 常用命令範例
command-here
\```

## 實際影響
說明此技能如何提升開發效率或解決實際問題。
```

### 3. 必要欄位

**YAML 前置資料：**
- `name`: 技能名稱（小寫，使用連字號，例如：`train-model`）
- `description`: 觸發條件說明（必須使用「Use when...」格式）

**內容章節（建議包含）：**
- 概述
- 何時使用
- 核心工作流程
- 常見問題
- 快速參考
- 實際影響

### 4. 命名慣例

使用 **動名詞（-ing 形式）** 搭配主動語態：

✅ 正確：`training-model`, `analyzing-reviews`, `deploying-docker`

❌ 錯誤：`model-training`, `review-analysis`, `docker-deployment`

---

## 技能開發最佳實踐

### 1. 描述欄位 (Description)

**必須專注於問題條件，而非工作流程摘要：**

✅ 正確：「Use when the ML model needs training or retraining」

❌ 錯誤：「Use when implementing model training - run script, verify output」

### 2. 保持簡潔但完整

- 技能文件應能快速掃描，但足夠詳細以有效執行
- 包含範例命令與預期輸出
- 提供疑難排解表格

### 3. 加入關鍵字以利搜尋

在文件中嵌入可搜尋的術語：
- 錯誤訊息（例如：「ImportError」、「ModuleNotFoundError」）
- 症狀描述（例如：「slow」、「hanging」、「timeout」）
- 工具與命令的實際名稱

### 4. 避免過度抽象

- 使用具體範例而非抽象概念
- 提供實際可執行的命令
- 展示真實的輸出範例

---

## 系統架構

```
.claude/
├── README.md                      # 本文件（繁體中文）
└── skills/                        # 技能定義目錄
    ├── train-model/
    │   └── SKILL.md               # 模型訓練技能
    ├── dev-setup/
    │   └── SKILL.md               # 開發環境設置技能
    ├── run-tests/
    │   └── SKILL.md               # 測試執行技能
    ├── batch-analyze/
    │   └── SKILL.md               # 批次分析技能
    ├── evaluate-model/
    │   └── SKILL.md               # 模型評估技能
    └── docker-dev/
        └── SKILL.md               # Docker 環境技能
```

---

## 整合效益

整合 Superpowers 框架後，開發者可以：

- ✅ 使用自然語言命令（如 `/train-model`）而非記憶複雜的 Python 指令
- ✅ 獲得 AI 代理透過結構化 7 階段開發流程的引導
- ✅ 自動化常見開發任務（設置、測試、模型訓練）
- ✅ 獲得理解 Review Trust Analyzer 架構的上下文感知協助
- ✅ 透過標準化、文件化的工作流程自動化減少認知負擔

**所有現有的手動命令仍然可用**，新技能系統作為增強層與現有工作流程並存。

---

## 疑難排解

### 技能無法觸發

**原因：** Claude Code 可能不支援插件系統

**解決方案：**
1. 確認 `.claude/skills/` 目錄存在
2. 檢查 SKILL.md 檔案格式是否正確
3. 手動執行對應的命令

### 技能執行失敗

**常見問題：**
- **相依套件未安裝**：執行 `pip install -r requirements.txt`
- **模型檔案遺失**：執行 `python ml/train.py`
- **工作目錄錯誤**：確保在專案根目錄執行命令
- **連接埠被佔用**：變更為其他連接埠或終止現有處理程序

### 需要更多協助？

- 📖 查看個別技能的詳細說明（點擊上方連結）
- 🔗 訪問 [Superpowers 官方文檔](https://github.com/obra/superpowers)
- 💬 詢問 Claude 代理以獲得上下文感知的協助

---

## 版本歷史

- **v1.0.0** (2025-01-20) - 初始整合
  - 建立 6 個核心技能（train-model, dev-setup, run-tests, batch-analyze, evaluate-model, docker-dev）
  - 繁體中文文件
  - 針對 Review Trust Analyzer 工作流程優化

---

## 貢獻

歡迎貢獻新技能或改善現有技能！請遵循：

1. 建立新的技能目錄於 `.claude/skills/`
2. 遵循 SKILL.md 格式規範
3. 使用繁體中文撰寫文件（或雙語）
4. 測試技能是否正常運作
5. 更新本 README.md

---

## 授權

本技能系統基於 [Superpowers](https://github.com/obra/superpowers) 框架，專為 Review Trust Analyzer 專案客製化。

---

**快速開始：**

```bash
# 1. 安裝相依套件
pip install -r requirements.txt

# 2. 訓練模型
python ml/train.py

# 3. 啟動伺服器
python -m uvicorn app.main:app --reload

# 4. 執行測試
python -m pytest -v

# 5. 批次分析（可選）
curl -X POST "http://localhost:8000/reviews/batch" \
  -F "file=@data/sample_reviews.csv"
```

祝開發愉快！🚀
