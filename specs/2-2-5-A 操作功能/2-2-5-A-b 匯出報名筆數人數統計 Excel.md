---
工項編號: 2-2-5-A-b
父工項: 2-2-5-A 操作功能
規格頁碼: 待補
測試範圍: true
驗證深度: (b)
實作狀態: 前端 menu action 註解未啟用
最後更新: 2026-05-06
---

# 2-2-5-A-b 匯出報名筆數/人數統計 Excel

## 規格原文（PDF）
<!-- AI-MANAGED START: spec-original -->
匯出報名筆數/人數統計 Excel（4/29 後端完成）

特殊規則（使用者明示）：
- **要排除取消報名的資料**
- **做前景下載**（不是背景排程）
- **畫面要有資料處理中的示意**
<!-- AI-MANAGED END: spec-original -->

## 驗收條件 (AC)
<!-- AI-MANAGED START: acceptance-criteria -->
- **AC1**：操作欄第 1 個 icon 展開後，下拉選單可見「匯出報名筆數/人數統計 Excel」（或對應文字）項
- **AC2**：點擊該項後觸發檔案下載（Playwright `page.expect_download`）
- **AC3**：下載檔案副檔名為 `.xlsx`
- **AC4**：xlsx 第一個 sheet 第一列（表頭）含核心欄名集合（待補：例「活動編號」「活動名稱」「報名筆數」「報名人數」等）
- **AC5**（行為層）：點擊後到下載完成之間，畫面顯示「資料處理中」示意（loading spinner / mask / toast）
- **AC6**（資料層）：匯出內容**不包含已取消報名**的紀錄（需查 sheet 資料；本 POC 階段降階僅驗 AC1–AC4，AC5/AC6 標 SKIP）
<!-- AI-MANAGED END: acceptance-criteria -->

## 待釐清
- [ ] **menu 中按鈕的實際文字**：spec 說「匯出報名筆數/人數統計」、src `EVEventEntity.ts` 中是 `activityStatExcel` Text='活動統計Excel' — 文字不一致，需確認
- [ ] **核心欄名集合**：規格期望表頭欄位有哪些？
- [ ] **資料處理中示意**：是 PrimeVue ProgressSpinner / Toast / 自訂 mask？影響 AC5 selector

## 實作差異註記
**前端 src `EVEvent.controller.ts L200-222` 中 `activityStatExcel` action 註解未啟用**。AC1（按鈕存在）目前可驗（因 `EVEventEntity.actionCol` 中 placeholder 仍會渲染），AC2 起需等前端解註後才能跑。

## 使用者註記
<!-- USER-EDIT START -->
- 排除取消報名 + 前景下載 + 處理中示意 — 三個強制規則
<!-- USER-EDIT END -->

## 變更紀錄
<!-- AI-CHANGELOG START -->
- 2026-05-06 初次生成（前端未實作，AC2-6 標 SKIP-pending）
<!-- AI-CHANGELOG END -->
