# DOM 事實庫（dom_facts）

> **目的**：把已驗證的 DOM 事實固化成「每頁一份對照表」，寫新測試**先查表、不探勘**。
> `prompts/99_重點經驗.md` 記「原則」（為什麼），本目錄記「資料」（是什麼）。

## 使用規則

1. **寫 selector 前先查本目錄**對應頁面的事實檔；查到就直接用，不重新探勘。
2. **查不到** → 用 `tools/dom_probe.py` 探勘（宣告式 steps，不寫一次性腳本）：
   ```powershell
   $env:PYTHONUTF8=1
   .\.venv\Scripts\python.exe tools\dom_probe.py --steps probe.txt --out probe_result.txt
   ```
3. **探勘結論必須寫回事實檔**（含驗證日期），否則下次還是要重探。
4. 事實過期（deploy 後 selector 紅了）→ 重跑 probe 確認 → 更新該筆事實與日期。
5. 每筆事實標注 `驗證日期`；來源以 live DOM 為準，**不從 src / i18n 推斷**（CLAUDE.md 第 3 條）。

## 檔案清單

| 檔案 | 涵蓋頁面 |
|---|---|
| `EVEventEdit.md` | 活動編輯頁（含分組管理、報名欄位、憑證報到、填寫建議、即時預覽） |
| `EventList.md` | 活動列表頁（篩選、排序、row menu、更多功能） |

新頁面（如公民端）解鎖時新增對應檔案。
