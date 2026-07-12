# POC_for_autotest

> 黑箱自動化測試 POC for 某活動報名管理系統（多環境：`config/config.<env>.yaml`；env 預設 local）

## 技術棧
- **測試**：Python 3.x + Playwright + pytest
- **受測前端**（read-only 參考）：Vue 3 + TypeScript + Vite + TailwindCSS + PrimeVue

## 語言規則
- 所有對話、commit、文件、程式碼註解一律**繁體中文**

## 行為約束（重要 — Agent 必讀）
1. **selector 工作流程（依序四步）**：
   0. **先查 DOM 事實庫**：`docs/dom_facts/<頁面>.md` 有已驗證事實就直接用，跳過探勘。
   1. **解碼 src**：targeted 讀對應 view + entity model + 共用 wrapper（如 `STFilter.vue`）→ 確認渲染樣態（aria-label / label / id / class 是否存在）。**不全域掃描、不讀 node_modules**。
   2. **寫 selector**：依步驟 0/1 的證據寫，依第 3 條策略下手。
   3. **pytest 跑**：紅綠是審查機制；**禁止對 live DOM 試錯猜 selector**（4-30 token 教訓：盲試 = 燒額度）。
   4. **紅了二修**：用 `tools/dom_probe.py`（宣告式 steps）對真實 DOM 確認，或使用者 dump 一頁 HTML；最多 3 輪。**禁止寫一次性 `_diag_*.py`**；探勘結論回填 `docs/dom_facts/`。
   黑箱原則：測試不引入前端內部型別，`src/sc_event_frontend/` 僅 read-only 參考。
2. **不掃 node_modules、不讀 package-lock.json**（637KB）。
3. **selector 策略**：優先 `get_by_role` / `get_by_label` / `get_by_text`；不使用 DevTools「複製 selector」的動態 ID（Vue UUID、`pv_id_*`）；不使用 Tailwind utility class。**DOM 是唯一事實**，文字 selector 不從 i18n 推斷。
4. **不 commit secrets**（`config/config.local.yaml`、`config/config.*.yaml`、`.auth/`、`credentials.json`）。多環境設定檔（`.dev`/`.test`/`.prod`）全部 gitignored；只有 `config.example.yaml` 入版控。
5. **不執行破壞性 git**（`reset --hard`、`push --force`）除非使用者明示。
6. **修改超過 5 個檔案前**，先更新 `plan.md` 並徵詢同意。
7. **session 結束前**若有實作或決議異動：
   - 更新 `STATUS.md`（純 read-only Q&A 不更新）
   - 若 `tests/` 或 `specs/` 有新增或修改 → **明確提醒使用者執行 sync**：
     ```
     .\scripts\sync_to_company.ps1
     # 然後到 aiautotest 執行 git add / commit / push
     ```
8. **不過度建構**：不主動擴充工項、不新增 P8+ 階段、不引入新依賴 / 新工具 / 新 hook，**除非使用者明示授權**。範圍排除（如 2-2-2-A 權限工項）一律以 `memory/poc_autotest_decisions.md` 為準。

## 子文件地圖

| 需求                       | 路徑                                                                         |
| ------------------------ | -------------------------------------------------------------------------- |
| **當前進度錨點**               | `STATUS.md` ← session 開場先讀這份                                               |
| 任務階段化計畫                  | `plan.md`                                                                  |
| 工項階層（驅動索引）               | `input/WBS.md`                                                             |
| **擴充需求（多環境/夜間排程）**       | `input/需求_多環境與夜間排程.md`                                                     |
| **工項測試適性標籤**             | `input/wbs_test_labels.md` ← MANUAL/INTEGRATION/SKIP/NOT-IMPL/BLOCKED 工項標注 |
| 規格來源                     | `specs/`（AI 產出）、`input/需求規格.pdf`（人類放置，不入 git）                              |
| **Agent 經驗檔（learnings）** | `prompts/99_重點經驗.md` ← 等同 `learnings.md`                                   |
| **DOM 事實庫（selector 先查表）**  | `docs/dom_facts/` ← 寫 selector 前先查；查不到用 `tools/dom_probe.py` 探勘後回填      |
| 每週協作 SOP（人類視角）           | `docs/使用手冊.md` Part A                                                      |
| AI 動工提示詞                 | `prompts/README.md` + `prompts/00_…40_…`                                   |
| 系統技術架構                   | `docs/技術架構.md`                                                             |
| **夜間排程 SOP**             | `docs/夜間排程.md`                                                             |
| CLI 速查                   | `docs/使用手冊.md` Part B                                                      |
| 簡報素材庫 + 流程圖規則            | `notes/`                                                                   |
| 測試與規格                    | `tests/`、`specs/`（依工項分目錄）                                                  |
| 報告                       | `reports/<run_id>/`（每次執行一目錄）                                               |
| 夜間最新摘要                   | `reports/nightly_latest.txt`                                               |
| Hook 範本（未啟用）             | `.claude/hooks/README.md`                                                  |

## Session 啟動 SOP

1. 讀 `STATUS.md` 接上次進度（這是進度真相源）
2. 必要時掃 `prompts/99_重點經驗.md` 的最新條目
3. 確認 `plan.md` 當前 Phase
4. 開工

## 環境需求備註
- Windows 11 + PowerShell（中文輸出需 `$env:PYTHONUTF8=1`）
- Playwright 1.48 不抓 sessionStorage，本專案用 `add_init_script` 還原（見 `prompts/99_重點經驗.md`）
- 多環境切替：`$env:TEST_ENV = "test"` 或 pytest `--env test`；設定檔 `config/config.<env>.yaml`（均 gitignored）
- QA 環境（TEST）：`https://qa-khcg-ai.foxconn.com/entry/login`
