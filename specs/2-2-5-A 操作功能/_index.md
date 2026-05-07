---
工項編號: 2-2-5-A
標題: 操作功能（活動數據 + 多個匯出 Excel）
規格頁碼: 待補
父工項: 2-2-5 操作功能
最後更新: 2026-05-06
---

# 2-2-5-A 操作功能

活動列表頁「操作欄」（4 個 icon button）下的「活動數據」群組，含跳轉與多個 Excel 匯出。

> **入口**：`/entry/evevent` 列表頁 → 操作欄第 1 個 icon（`icon-chart`）展開 → 「查看活動數據 / 滿意度反饋 / 活動統計 Excel / 活動統計 PDF」等項目
> **跳轉目標**（A-a）：`/DashboardDetail/source=EVEvent&pkid=<id>`（與 B-a 同 URL，差別在 sessionStorage scroll 標記）

## 子工項

| 編號 | 標題 | 範圍 | 實作狀態（src 解碼 2026-05-06）| 可測深度 | tests 對應檔 |
|------|------|------|--------------------------------|---------|--------------|
| 2-2-5-A-a | 查看活動數據（跳轉） | ✅ | 已實作（`viewActivityData` action） | 完整：跳轉 + URL + title 顯示活動名 | `test_2_2_5_A_a_*.py` |
| 2-2-5-A-b | 匯出報名筆數/人數統計 Excel | ✅ | ⚠️ 前端 menu action **註解未啟用**（EVEvent.controller.ts L200-222） | 退化：驗按鈕存在 + click 不噴錯（download 暫無法觸發） | `test_2_2_5_A_b_*.py` |
| 2-2-5-A-c | 匯出報到筆數/人數統計 Excel | ✅ | ⚠️ 同 b | 同 b | `test_2_2_5_A_c_*.py` |
| 2-2-5-A-d | 匯出報名者性別/年齡/行政區統計 Excel | ✅ | ⚠️ 同 b | 同 b | `test_2_2_5_A_d_*.py` |
| 2-2-5-A-e | 匯出報名登入來源統計 Excel | ❌ 跳過 | 待確認規格 | — | — |
| 2-2-5-A-f | 匯出取消報名統計 Excel | ✅ | ⚠️ 同 b | 同 b | `test_2_2_5_A_f_*.py` |
| 2-2-5-A-g | 匯出滿意度問卷 Excel | ❌ 跳過 | 待確認規格（src 中有 `satisfactionFeedback` placeholder 但註解掉） | — | — |

> **重大實作差異**：使用者進度說明 4/29、4/30 後端完成；但前端 src `EVEvent.controller.ts L200-222` 中 `satisfactionFeedback` / `activityStatExcel` / `activityStatPdf` / `downloadEnrollList` 四個 action 仍處 **註解** 狀態（`// switch (actionId) { ... }`），按鈕點下去無反應。
>
> **影響**：A-b/c/d/f 的 AC2「點擊後觸發下載」目前無法驗證，test 標 `pytest.mark.skip(reason="前端 menu action 註解未啟用，src 解註後可解 skip")`。等前端解註，AC1（按鈕存在）即可驗。

## 規格原文（PDF）
<!-- AI-MANAGED START: spec-original -->
（PDF 原文待補。WBS 引用：4/24、4/29、4/30 各階段完成；A-b 特別註記「要排除取消報名的資料、做前景下載、畫面要有資料處理中的示意」）
<!-- AI-MANAGED END: spec-original -->

## 使用者註記
<!-- USER-EDIT START -->
- A-b 特殊規則：匯出報名筆數/人數統計時要**排除取消報名的資料**
- A-b 行為：**前景下載**（不是背景排程）+ 畫面要有「資料處理中」示意
- A-e、A-g 待確認規格，本批跳過
- 操作欄 icon 順序：1=活動數據(chart)、2=報名名單(file)、3=活動連結(link)、4=更多(more)
- A 系列下拉項在第 1 個 icon 的 menu 內（依 controller 中 `'activityData'` group 的 MenuBtns）
<!-- USER-EDIT END -->

## 變更紀錄
<!-- AI-CHANGELOG START -->
- 2026-05-06 初次生成（5 子項：a/b/c/d/f；e/g 跳過；b/c/d/f 標 SKIP-pending）
<!-- AI-CHANGELOG END -->
