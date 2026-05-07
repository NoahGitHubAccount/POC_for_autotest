# POC_for_autotest

> 黑箱自動化測試 POC for 高雄數位市民活動模組（dev-maas.foxconn.com）

## 技術棧
- **測試**：Python 3.x + Playwright + pytest
- **受測前端**（read-only 參考）：Vue 3 + TypeScript + Vite + TailwindCSS + PrimeVue

## 語言規則
- 所有對話、commit、文件、程式碼註解一律**繁體中文**

## 行為約束（重要 — Agent 必讀）
1. **selector 工作流程（依序四步）**：
   1. **解碼 src**：targeted 讀對應 view + entity model + 共用 wrapper（如 `STFilter.vue`）→ 確認渲染樣態（aria-label / label / id / class 是否存在）。**不全域掃描、不讀 node_modules**。
   2. **寫 selector**：依步驟 1 的 src 證據寫，依第 3 條策略下手。
   3. **pytest 跑**：紅綠是審查機制；**禁止對 live DOM 試錯猜 selector**（4-30 token 教訓：盲試 = 燒額度）。
   4. **紅了二修**：使用者 dump 一頁 HTML，AI 對著真實 DOM 改；最多 3 輪。
   黑箱原則：測試不引入前端內部型別，`src/sc_event_frontend/` 僅 read-only 參考。
2. **不掃 node_modules、不讀 package-lock.json**（637KB）。
3. **selector 策略**：優先 `get_by_role` / `get_by_label` / `get_by_text`；不使用 DevTools「複製 selector」的動態 ID（Vue UUID、`pv_id_*`）；不使用 Tailwind utility class。**DOM 是唯一事實**，文字 selector 不從 i18n 推斷。
4. **不 commit secrets**（`config/config.local.yaml`、`.auth/`、`credentials.json`）。
5. **不執行破壞性 git**（`reset --hard`、`push --force`）除非使用者明示。
6. **修改超過 5 個檔案前**，先更新 `plan.md` 並徵詢同意。
7. **session 結束前**若有實作或決議異動 → 更新 `STATUS.md`；純 read-only Q&A 不更新。
8. **不過度建構**：不主動擴充工項、不新增 P8+ 階段、不引入新依賴 / 新工具 / 新 hook，**除非使用者明示授權**。範圍排除（如 2-2-2-A 權限工項）一律以 `memory/poc_autotest_decisions.md` 為準。

## 子文件地圖

| 需求 | 路徑 |
|---|---|
| **當前進度錨點** | `STATUS.md` ← session 開場先讀這份 |
| 任務階段化計畫 | `plan.md` |
| 工項階層（驅動索引） | `WBS.md` |
| 規格來源 | `specs/`、`高雄數位市民活動模組需求.pdf` |
| **Agent 經驗檔（learnings）** | `prompts/99_重點經驗.md` ← 等同 `learnings.md` |
| 每週協作流程 SOP | `prompts/README.md` |
| 提示詞庫 | `prompts/00_…`、`prompts/10_…`（編號 00–99） |
| 人類向延伸文件 | `docs/`（永久性參考；目前 stub） |
| 簡報素材庫 | `notes/`（餵 `make-pptx` skill；目前 stub） |
| 測試與規格 | `tests/`、`specs/`（依工項分目錄） |
| 報告 | `reports/<run_id>/`（每次執行一目錄） |
| Hook 範本（未啟用） | `.claude/hooks/README.md` |

## Session 啟動 SOP

1. 讀 `STATUS.md` 接上次進度（這是進度真相源）
2. 必要時掃 `prompts/99_重點經驗.md` 的最新條目
3. 確認 `plan.md` 當前 Phase
4. 開工

## 環境需求備註
- Windows 11 + PowerShell（中文輸出需 `$env:PYTHONUTF8=1`）
- Playwright 1.48 不抓 sessionStorage，本專案用 `add_init_script` 還原（見 `prompts/99_重點經驗.md`）
