---
工項編號: 2-3-13
標題: 各時間欄位先後順序防呆（Date picker 限制）
規格頁碼: 待補
父工項: 2-3 活動編輯（推測）
最後更新: 2026-05-06
---

# 2-3-13 各時間欄位先後順序防呆

> 在活動編輯頁，DatePicker 對「先後順序」做防呆：違反規則時應禁止輸入或顯示錯誤訊息。

## 規則總覽（使用者 2026-05-06 提供，14 條規則拆 5 群組）

| 群組 | 規則 | 條數 | 範圍 |
|------|------|------|------|
| 1. 活動開始/結束時間 | 開始 < 結束 | 1 | ✅ |
| 2. 活動曝光時間 | 曝光開始 ≤ 活動開始；曝光結束 ≥ 活動結束；曝光開始 < 曝光結束 | 3 | ✅ |
| 3. 活動報名時間 | 開放 ≥ 曝光開始；開放 ≤ 活動開始；截止 ≤ 活動開始；開放 < 截止 | 4 | ✅ |
| 4. 截止修改時間 | 截止修改 ≤ 截止報名；截止修改 ≤ 活動開始 | 2 | ✅ |
| 5. 報到時間 | 開放報到 ≥ 截止報名；開放報到 ≤ 活動開始；截止報到 ≥ 開放報到；截止報到 ≤ 活動結束 | 4 | ✅ |
| 6. 場次時間 | （合併到 2-3-2 處理）| — | ❌ 不在 2-3-13 範圍 |

## 子工項

| 編號 | 規則 | 範圍 | 實作狀態（src 解碼 2026-05-06）| tests 對應檔 |
|------|------|------|--------------------------------|--------------|
| 2-3-13-G1 | 群組 1：活動開始 < 活動結束 | ✅ | ⚠️ 未實作 | `test_2_3_13_G1_*.py` |
| 2-3-13-G2 | 群組 2：曝光時間 | ✅ | ⚠️ 未實作 | `test_2_3_13_G2_*.py` |
| 2-3-13-G3 | 群組 3：報名時間 | ✅ | ⚠️ 未實作 | `test_2_3_13_G3_*.py` |
| 2-3-13-G4 | 群組 4：截止修改時間 | ✅ | ⚠️ 未實作 | `test_2_3_13_G4_*.py` |
| 2-3-13-G5 | 群組 5：報到時間 | ✅ | ⚠️ 未實作 | `test_2_3_13_G5_*.py` |

> **重大實作差異**：`composables/ActivityMgmt/EVEventEdit.controller.ts` 中所有日期欄位（`startTime`/`endTime`/`publishStartTime`/`publishEndTime`/`registrationOpenFrom`/`registrationCloseTo` 等）的 PageFormItem 都**沒有設定** `minDate` / `maxDate` / `disabledDates`，submit 時也**沒有時間順序 validate**，目前只有 fallback 的 `setErrorToast("儲存錯誤")`。
>
> **影響**：所有 G1-G5 的「反向」AC（違反規則時應有防呆）目前 test 標 `pytest.mark.skip(reason="前端未實作 DatePicker 防呆，待 controller 加 minDate/maxDate 或 submit validate")`。「正向」AC（合法值不被擋）可跑驗 selector 與表單存取。

## 規格原文（PDF）
<!-- AI-MANAGED START: spec-original -->
（規則由使用者提供，已列在「規則總覽」段。PDF 原文待補。）
<!-- AI-MANAGED END: spec-original -->

## 已釐清（src 解碼 2026-05-06）
- [x] **活動編輯頁進入路徑**：列表頁點「活動名稱」cell（`SetEvent_CellClick` 觸發），URL 變為 `/EVEventEdit/source=EVEvent&pkid=<id>`
- [x] **欄位 label 文字**：`startTime` Name='活動開始時間'、`endTime` Name='活動結束時間'、`publishStartTime` Name='活動曝光時間'、`publishEndTime` Name='活動曝光結束時間'、`registrationOpenFrom` Name='開放報名時間'、`registrationCloseTo` Name='截止報名時間'
- [x] **欄位類型**：`PageItem.DatePicker, IsShowTime: true, hourFormat: '24'`，值格式 `YYYY-MM-DD / HH:mm`

## 待釐清
- [ ] **防呆規格的優先呈現方式**（決定前端怎麼實作）：
  - 選項 A：DatePicker `minDate`/`maxDate` 限制可選範圍（防呆最強，UX 最佳）
  - 選項 B：輸入後即時錯誤訊息（inline validator）
  - 選項 C：按「儲存」時 toast 並阻止送出
- [ ] G4「截止修改時間」欄位在 src 中對應哪個 Field？目前未定位
- [ ] G5「報到時間」（cancelPeriod）欄位在 src 中對應哪個 Field？

## 使用者註記
<!-- USER-EDIT START -->

<!-- USER-EDIT END -->

## 變更紀錄
<!-- AI-CHANGELOG START -->
- 2026-05-06 初次生成（試點群組 1，使用者明示拆批策略）
<!-- AI-CHANGELOG END -->
