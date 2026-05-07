---
工項編號: 2-2-5-B
標題: 報名名單
規格頁碼: 待補
父工項: 2-2-5 操作功能
最後更新: 2026-05-06
---

# 2-2-5-B 報名名單

活動列表頁「操作欄」（點 icon 才展開）下的報名名單群組，含查看 + 3 個 Excel 匯出。

> **入口**：`/entry/evevent` 列表頁 → 操作欄 icon（點開） → 該活動 row 的下拉選項 → 「查看報名名單 / 匯出報名紀錄 / 匯出取消報名 / 匯出報到名單」
> **跳轉目標**（B-a）：`/entry/DashboardDetail/source=EVEvent&pkid=<id>` → 滑動到「報名名單」section

## 子工項

| 編號 | 標題 | 範圍 | 實作狀態（src 解碼 2026-05-06）| 可測深度 | tests 對應檔 |
|------|------|------|------|---------|--------------|
| 2-2-5-B-a | 查看報名名單（跳轉 + 滾動） | ✅ | 已實作（`viewEnrollList` action 寫 sessionStorage 觸發 scrollIntoView） | 完整：跳轉 + URL + 報名名單元素 in viewport | `test_2_2_5_B_a_*.py` |
| 2-2-5-B-b | 匯出報名紀錄 Excel | ✅ | ⚠️ Dashboard 內報名名單 toolbar 有「下載報名資料」按鈕，但 `handleToolbarAction` 是 `console.log` | 退化：驗按鈕存在 + click 不噴錯（download 暫無法觸發） | `test_2_2_5_B_b_*.py` |
| 2-2-5-B-c | 匯出取消報名紀錄 Excel | ✅ | ⚠️ src 中**沒有獨立按鈕**（只有 1 個下載按鈕），疑為 spec 與 impl 期望不一致 | 退化：只能在「按鈕存在」這層之下 SKIP-pending | `test_2_2_5_B_c_*.py` |
| 2-2-5-B-d | 匯出報到名單 Excel | ✅ | ⚠️ 同 c | 同 c | `test_2_2_5_B_d_*.py` |

> **驗證深度說明**：使用者 2026-05-06 確認三個 Excel 全部降階為 (b)：「驗 sheet 欄名」即可，不驗資料內容。理由：黑箱無 ground truth 來源、ROI 偏低、進度緊。
>
> **重大實作差異**：使用者進度說明「5/5 前端完成 B-b/c/d」，但 src `composables/pageCustom/PageSectionADActivityRegistrationList.ts` 中只有「下載報名資料」**單一按鈕**，且 `handleToolbarAction` 是 `console.log` placeholder。需要與前端確認：(1) 三個分開按鈕的位置 (2) download API 接線時程。在那之前，B-b/c/d test 標 SKIP-pending。

## 規格原文（PDF）
<!-- AI-MANAGED START: spec-original -->
（待補。WBS 引用：4/29 後端完成、5/5 前端完成。）
<!-- AI-MANAGED END: spec-original -->

## 使用者註記
<!-- USER-EDIT START -->
- 操作欄需點 icon 才展開
- B-a 跳轉路徑：`/entry/DashboardDetail/source=EVEvent&pkid=<id>`
- B-a 入口位置 DOM：列表 td:nth-child(10) > div > div:nth-child(2)
- A-a「查看活動數據」是 div:nth-child(1)，B-a 是 div:nth-child(2)；B-b/c/d 推測為後續 nth-child（待 src 解碼確認）
<!-- USER-EDIT END -->

## 變更紀錄
<!-- AI-CHANGELOG START -->
- 2026-05-06 初次生成（Excel 全降階 (b)、入口位置依使用者 DOM 提示推測）
<!-- AI-CHANGELOG END -->
