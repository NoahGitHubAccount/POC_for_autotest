---
工項編號: 2-2-5-B-b
父工項: 2-2-5-B 報名名單
規格頁碼: 待補
測試範圍: true
驗證深度: (b)
最後更新: 2026-05-06
---

# 2-2-5-B-b 匯出報名紀錄 Excel

## 規格原文（PDF）
<!-- AI-MANAGED START: spec-original -->
匯出報名紀錄 Excel（4/29 後端完成、5/5 前端完成）
<!-- AI-MANAGED END: spec-original -->

## 驗收條件 (AC)
<!-- AI-MANAGED START: acceptance-criteria -->
- **AC1**：列表第一筆活動的操作欄展開後可看到「匯出報名紀錄」項
- **AC2**：點擊後觸發檔案下載（Playwright `page.expect_download`）
- **AC3**：下載檔案副檔名為 `.xlsx`（非 `.csv` / `.xls`）
- **AC4**：開啟 xlsx 第一個 sheet，第一列（表頭）含核心欄名集合（待補：例「報名編號」「姓名」「報名時間」等核心欄）

> 不驗資料內容（深度 (c)，使用者 2026-05-06 已決議降階為 (b)）。
<!-- AI-MANAGED END: acceptance-criteria -->

## 待釐清
- [ ] **核心欄名集合**：規格期望的表頭欄位有哪些？（待補；此 AC4 在使用者補欄名清單前以「至少含某幾個常見欄」寬鬆驗證，後續再嚴格化）
- [ ] 是否有「資料處理中」的前景示意？（WBS 註記）若有需驗存在性？POC 不驗

## 使用者註記
<!-- USER-EDIT START -->

<!-- USER-EDIT END -->

## 變更紀錄
<!-- AI-CHANGELOG START -->
- 2026-05-06 初次生成（驗證深度 (b)，AC4 待補核心欄名）
<!-- AI-CHANGELOG END -->
