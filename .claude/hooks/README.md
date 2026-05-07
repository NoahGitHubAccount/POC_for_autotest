# Hook 範本（未啟用）

本目錄保留給未來 Hook 設定使用。**目前無啟用 hook**，由 `CLAUDE.md` 的「行為約束」+ `STATUS.md` 維護規則以「人類約定」方式達成同等效果。

## 何時考慮啟用

當下列任一情境發生時，將相應 hook 寫入 `~/.claude/settings.json` 或本專案 `.claude/settings.json`：

| 痛點 | 對應 hook | 內容草案 |
|---|---|---|
| 我（AI）忘記 session 結束更新 STATUS.md | `Stop` | 結束前提示「請檢查 STATUS.md 是否需要更新」 |
| 新 session 沒主動讀 STATUS.md / CLAUDE.md | `SessionStart` | 自動載入 STATUS.md 摘要進 context |
| AI 嘗試 commit 含 secrets 的檔案 | `PreToolUse`（Bash matcher: `git commit`）| 掃 staged diff，發現 `password` / `token` 阻擋 |
| AI 想跑 `git reset --hard` / `git push --force` | `PreToolUse`（Bash） | 阻擋並要求改用安全替代 |
| pytest 結束自動寫進 `STATUS.md` 的「最近一次動作」 | `PostToolUse`（Bash matcher: `pytest`） | 把退出碼與報告連結附加到 STATUS.md |

## 為何先不啟用

- 目前 POC 階段，Claude session 互動次數少、人類在迴圈中，約定夠用
- Hook 寫進 `settings.json` 是全域影響，誤啟用會卡所有專案
- 等「同樣問題重犯 ≥ 2 次」再考慮機械化

## 啟用步驟（未來參考）

1. 在本目錄建立對應 `.ps1` / `.sh` 腳本
2. 透過 `update-config` skill 把 hook 寫入 `settings.json`，**範圍限定本專案路徑**
3. 在本檔記錄啟用日期與條目

## 參考

- 全域 settings：`C:\Users\張捷\.claude\settings.json`
- Skill 文件：`~/.claude/skills/update-config/`、`~/.claude/skills/harness-engineer/references/03-mechanical-enforcement.md`
