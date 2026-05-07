# POC_for_autotest

> **一句話定位**：用 AI 協作把「PDF 規格」自動轉成「pytest 測試 + Word 報告」的工程化骨架。
> **適用方法**：可複製到任何「有 PDF/Word 規格 + Web UI」的專案。
> **受測對象**：某活動報名管理系統（具體 host 在本機 `config/config.local.yaml`，不入 git）。

---

## 目錄

1. [這個工具解決什麼問題](#1-這個工具解決什麼問題)
2. [我該不該繼續讀](#2-我該不該繼續讀)
3. [先看這份：技術架構](#3-先看這份技術架構)
4. [快速開始（Win11）](#4-快速開始win11)
5. [一張圖看懂工作方式](#5-一張圖看懂工作方式)
6. [文件導讀（依角色找路）](#6-文件導讀依角色找路)
7. [目錄結構](#7-目錄結構)
8. [階段進度](#8-階段進度)

---

## 1. 這個工具解決什麼問題

QA 為新功能寫一份完整測試 + 報告，傳統流程要：

> 讀 PDF 規格 → 寫 spec md → 寫 pytest → 跑 → 紅了除錯 → 整理截圖 → 排版 docx 給業務 review

每個工項 30 分鐘起跳；十個工項就是半天，且每次重複勞動。

**本專案的解法**：把這條鏈拆成「AI 動手 + 人類 review」的循環，並把每一步沉澱成可重放的工程化骨架。

| 步驟 | 誰做 | 用什麼 |
|---|---|---|
| 規格轉化（PDF → spec md） | AI | `prompts/10_PDF轉規格_提示詞.md` |
| 案例展開（spec → pytest test） | AI | `prompts/20_生成測試案例_提示詞.md` |
| 規格 / 測試修訂 | AI（依 review 意見） | `prompts/30_審查與修訂_提示詞.md` |
| 跑 pytest + 紅了除錯 | 人類 + AI 對 src 解碼 | `prompts/40_執行測試與排錯_提示詞.md` |
| 報告交付 | 人類觸發、工具產出 | `tools/md_to_docx.py` |
| 經驗沉澱 | AI | `prompts/99_重點經驗.md` |

成果：以 `2-2-2 搜尋功能` 為試點，B/C/D 三子工項共 17 case 達成 12 PASS / 3 XFAIL / 2 SKIP，自動產出 Word 報告交付。

---

## 2. 我該不該繼續讀

**適用情境**：

- 你有 PDF / Word 形式的需求規格文件
- 你願意每週花 1–2 小時 review AI 產出（不能完全放手）
- 你需要 docx 報告給非技術同仁看
- 你會用 Python + Playwright + pytest（不需要精通，但看得懂錯誤訊息）

**不適用情境**：

- 規格只在會議白板上、沒落地成文件
- 想完全靠 AI 不想 review（會踩坑、修起來更累）
- 已經有完整 CI / 測試框架的成熟團隊（這是 POC，不是替代方案）
- 受測網站完全沒有穩定的語意 selector（PrimeVue 動態 ID、無 data-testid）— 還是可以做，但 selector 維護成本高

---

## 3. 先看這份：技術架構

如果你只想花 5 分鐘了解這個工具長怎樣，**直接讀 [`docs/技術架構.md`](docs/技術架構.md)**。

該文件含：

- **目錄樹**（含每個目錄的職責）
- **mermaid 模組分層圖**（5 層：輸入 → 工具入口 → 共用函式庫 → 知識與測試碼 → 產出）
- **mermaid 週循環資料流圖**（從 PDF 到 docx 的單次循環）
- **各目錄職責表**（誰呼叫誰、誰產出誰）
- **§6 給「下一個專案使用人」的 7 步進入路徑**
- **§7 跨專案重用 checklist**（保留什麼 / 替換什麼 / 清空什麼）

> **新人路徑**：本 README §1–§4 → `docs/技術架構.md` 全文 → 回來看本檔 §6 找你的角色路徑

---

## 4. 快速開始（Win11）

```powershell
# 1. 建虛擬環境並安裝依賴
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium

# 2. 建立本機設定（含帳密；不會被 git 追蹤）
copy config\config.example.yaml config\config.local.yaml
# 用編輯器填入 base_url、username、password 等

# 3. 把需求 PDF 放到 input/（命名 需求規格.pdf 或自訂後傳 --pdf）
copy <你的需求 PDF> input\需求規格.pdf

# 4. 第一次登入產 storage_state（手動操作瀏覽器）
python tools\warm_login.py

# 5. 冒煙測試（驗證登入態與報告器）
python tools\run.py --smoke

# 6. 跑指定工項（試點：2-2-2-B）
pytest "tests/2-2-2 搜尋功能/" -v

# 7. 產 Word 報告（最終交付）
pytest "tests/2-2-2 搜尋功能/" -v --shot=always
python tools\md_to_docx.py
# docx 在 reports/<rid>_run/docx/
```

更多 CLI 用法、SOP 細節見 [`docs/使用手冊.md`](docs/使用手冊.md)。

---

## 5. 一張圖看懂工作方式

完整 mermaid 圖在 [`docs/技術架構.md`](docs/技術架構.md)，這裡是文字版簡化：

```
┌──────────────────────┐
│ input/                │
│  ├─ WBS.md           │  ← 人類填工項階層
│  └─ 需求規格.pdf      │  ← 人類放需求 PDF
└──────────┬───────────┘
           │ AI（prompts/10）
           ▼
┌──────────────┐         ┌─────────────────┐
│ specs/<id>.md│ ←—————— │ 人類 review     │
└────┬─────────┘         └─────────────────┘
     │ AI（prompts/20）
     ▼
┌──────────────────────┐
│ tests/<wbs>/test_*.py│
└────┬─────────────────┘
     │ pytest（人類觸發）
     ▼
┌──────────────────────────────────────┐
│ reports/<rid>_run/                   │
│   ├─ <工項>.md   ← 逐工項 markdown    │
│   ├─ _summary.md ← 本次 run 彙總     │
│   └─ screenshots/ ← 截圖              │
└────┬─────────────────────────────────┘
     │ tools/md_to_docx.py
     ▼
┌──────────────────────────────┐
│ reports/<rid>_run/docx/*.docx │ ← Word 交付件
└──────────────────────────────┘
```

紅了的時候進入除錯子循環（解碼 src + dump HTML + 修 `lib/selectors.py`），最多 3 輪。詳見 `prompts/40_執行測試與排錯_提示詞.md`。

---

## 6. 文件導讀（依角色找路）

### 🎯 你的角色 → 推薦閱讀順序

| 角色 | 第 1 份 | 第 2 份 | 第 3 份 |
|---|---|---|---|
| **第一次接觸 / 想評估這套方法** | 本 README | [`docs/技術架構.md`](docs/技術架構.md) | [`docs/使用手冊.md`](docs/使用手冊.md) Part A |
| **要動手用（QA / 工程師）** | 本 README §4 | [`docs/使用手冊.md`](docs/使用手冊.md) | [`input/README.md`](input/README.md) |
| **要讓 AI 幫你產 spec / test** | [`docs/使用手冊.md`](docs/使用手冊.md) Part A | [`prompts/README.md`](prompts/README.md) | `prompts/00_…` ～ `40_…` |
| **要把這套搬到別的專案** | [`docs/技術架構.md`](docs/技術架構.md) §6–§7 | [`input/README.md`](input/README.md) | [`prompts/99_重點經驗.md`](prompts/99_重點經驗.md) |
| **接手 session（AI Agent）** | `STATUS.md` | [`CLAUDE.md`](CLAUDE.md) | [`prompts/99_重點經驗.md`](prompts/99_重點經驗.md) |

### 📚 完整文件清單

| 文件 | 用途 |
|---|---|
| **`docs/技術架構.md`** | **架構圖 + 資料流 + 跨專案重用 checklist**（第一次來看這份） |
| **`docs/使用手冊.md`** | **每週協作 SOP（Part A）+ CLI 速查（Part B）**（動手時查這份） |
| `input/README.md` | input/ 目錄角色說明（人類輸入素材） |
| `STATUS.md` | 當前進度錨點（高頻變動，gitignored；個人筆記） |
| `input/WBS.md` | 工項階層清單（驅動測試的索引） |
| `plan.md` | 階段化任務計畫（P0–P7） |
| `CLAUDE.md` | Agent 行為約束 + 子文件地圖 |
| `prompts/README.md` | 提示詞工具庫導覽（00 → 99） |
| `prompts/99_重點經驗.md` | 踩坑紀錄（learnings；持續累加） |
| `notes/流程圖生成規則.md` | 流程圖繪製慣例 |

---

## 7. 目錄結構

```
POC_for_autotest/
├── input/           人類輸入素材（WBS.md + 需求 PDF；跨專案最該替換）
├── config/          設定（example 進 git，local 不進）
├── specs/           規格 md（從 PDF 展開，依工項分目錄）
├── tests/           pytest 測試案例（依工項分目錄）
├── reports/         測試報告（每次執行一個 run 目錄；gitignored）
├── lib/             共用模組（auth / config / md_reporter / selectors）
├── tools/           CLI 入口（run / warm_login / md_to_docx / explore_page / ...）
├── prompts/         工程化提示詞庫（00→99；可跨專案重用）
├── docs/            人類向永久參考文件（README / 技術架構 / 使用手冊）
├── notes/           簡報素材庫（餵 make-pptx skill）+ 流程圖生成規則
├── .auth/           登入態儲存（gitignored）
└── .claude/         Claude Code hook 範本（未啟用）
```

各目錄完整職責、檔案層級、誰呼叫誰，請見 [`docs/技術架構.md` §5](docs/技術架構.md)。

---

## 8. 階段進度

> 詳細展開見 [`plan.md`](plan.md)；當前 WBS 級別進度見 `STATUS.md`。

- [x] **P0** 環境初始化
- [x] **P1** 登入骨架（warm-login + storageState + sessionStorage workaround）
- [x] **P2** 報告器與 Runner（`lib/md_reporter.py` + `tools/run.py`）
- [x] **P3** 規格展開試點（2-2-2 A–D 4 份 spec）
- [x] **P4** 案例試點（2-2-2-B：12 PASS / 2 XFAIL / 1 SKIP）
- [x] **P5** 補齊 2-2-2-C/D（C 4 PASS+1 XFAIL；D 3 PASS+1 XFAIL+1 SKIP）
- [x] **P5.5** 報告交付（截圖 + docx 整併版）
- [ ] **P4.5** 工項擴展（2-2-3 ✅ / 2-2-4 ✅ / 2-2-5-A ✅ / 2-2-5-B ✅ / 2-3-13 ✅；待重跑驗 xfail）
- [ ] **P5.7** 夜間排程（Windows 工作排程器；待 P4.5 全綠）
- [ ] **P6** 前端 meta 同步（待前端加 `data-testid`）
- [x] **P7** 工程化沉澱（prompts 完整化 + docs 整理 + input/ 收納 + push GitHub）

最新里程碑：2026-05-08 docs 重整 + push 到 GitHub。
