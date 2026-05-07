# POC_for_autotest 文件

人類可閱讀的延伸文件目錄。目前 stub — 隨專案需要再展開。

## 文件索引

| 文件 | 狀態 | 說明 |
|---|---|---|
| **工具指令集.md** | ✅ | **CLI 速查表**（產 word 報告 / 跑 pytest / warm-login / explore_page 等） |
| **技術架構.md** | ✅ | **架構圖 + 資料流 + 跨專案重用 checklist**（下一個專案使用人從這裡入門） |
| 合作SOP_QA.md | ✅ | 跨 session 合作流程 Q&A |
| install.md | 未建立 | 詳細安裝步驟（目前在根 README.md 已足） |
| troubleshooting.md | 未建立 | 疑難排解（目前都記在 `prompts/99_重點經驗.md`） |
| adr/ | 未建立 | 架構決策記錄 |

> 短期內若內容量不大，內容繼續放在 `prompts/99_重點經驗.md` + 根 `README.md` 即可，等真正膨脹再外推到此處。

## 撰寫慣例（沿用根 CLAUDE.md）

- 所有文件使用**繁體中文**
- 每份文件頂部加**最後更新日期**
- 截圖放 `docs/assets/`
- 超過 200 行考慮拆分

## 與根目錄文件的關係

| 根目錄 | docs/ |
|---|---|
| `README.md` | 入口 + quickstart |
| `CLAUDE.md` | Agent 地圖 |
| `plan.md` | 階段化任務計畫（短期） |
| `STATUS.md` | 當前進度（高頻變動） |
| `WBS.md` | 工項階層 |
| `prompts/99_重點經驗.md` | learnings（累加） |
| `docs/`（此處） | 永久性參考文件（目前空） |
