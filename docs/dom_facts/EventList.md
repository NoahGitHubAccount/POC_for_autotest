# DOM 事實：EventList 活動列表頁

> URL：`/entry/evevent`（`EventListPage.PATH`，見 `lib/selectors.py`）

## 已驗證事實

| 元素 | Selector | 備註 | 驗證日期 |
|---|---|---|---|
| 新增活動按鈕 | `aria-label="新增"`（`EventListPage.create_button()`） | | 2026-05-20 |
| 篩選套用按鈕 | 文字「**套用**」 | i18n 檔寫「查詢」但 prop 覆蓋為「套用」——**勿從 i18n 推斷** | 2026-04-30 |
| 篩選日期欄 | `date_input_by_label` 可用 | 此頁 label 與 input 同父層（EVEventEdit 不適用） | 2026-05-18 |
| 資料列 | `tbody tr`（⚠ `[data-pc-name='row']` 2026-07-12 起不再出現，勿用）；儲存格 `[data-pc-name='bodycell']` 仍在 | PrimeVue DataTable；**列操作按鈕晚生成**：等 `tbody tr button` attached（40s）再操作 | 2026-07-12 |
| row menu（2-2-5-B） | 列表列的**第 2 個 icon menu**（非 DashboardDetail toolbar） | 匯出按鈕文字：`匯出報名名單 Excel` / `匯出取消報名名單 Excel` / `匯出報到名單 Excel` | 2026-05-14 |
| 更多 menu（icon 4） | `action_icon(row, 4)` → overlay 選項：`管理工作人員名單`／`複製此活動`／`刪除此活動` | 工作人員名單開**右側 drawer**（非 .p-dialog），按鈕：`列印`／`下載excel模板`／`上傳名單`（全頁唯一文字可 get_by_text）；模板下載走標準 download 事件；toast 同一訊息會出現在 3 個容器（計數勿當 3 則）；**規格的「編輯彈窗文字」項不存在＝ISS-014** | 2026-07-12 |
| 導覽選單 | 文字：`數據總覽`(→/entry/Dashboard 所有活動總覽)／`活動列表`(→/entry/evevent)／`管理後台`(→/entry/usr 帳號管理) | 帳號管理頁：查詢/新增帳號/下載＋帳號表（角色/狀態欄） | 2026-07-12 |

## DatePicker 格式

- 接受 **slash** 格式（`YYYY/MM/DD`）。
- dash（`YYYY-MM-DD`）：2-3-13 G1-AC4 實測已支援（PASS，2026-05-17）；**本頁 DatePicker 是不同組件**，dash 支援需單獨驗證（2-2-2-B AC8 XPASS 待解 xfail）。

## 已知 flaky / 待確認

- 2-2-2-B AC5：DatePicker click timeout（disabled 狀態？）待查。
- 2-2-3 AC4：重整後排序驗證 timing 不穩。
- 2-2-5-A-a AC4：DashboardDetail `page_title_text` selector 30s timeout，需 probe 確認後回填。
- 2-2-5-A b/c/f：前景下載不觸發 download event，實際機制（blob / window.open / API）待確認。
