# DOM 事實：EVEventEdit 活動編輯頁

> URL：`/entry/EVEventEdit/source=EVEvent&pkid=<pkid>`
> 完整欄位清單請跑 `tools/inventory_fields.py`（main 內）+ `tools/inventory_aside.py`（aside）後回填本檔。

## 穩定定位錨點（2026-05-17 重整驗證，跨 deploy 穩定）

| 範圍 | 錨點 | 用法 |
|---|---|---|
| 表單欄位 | `data-field-id` | `EVEventEditPage.field_container(page, fid)` |
| 區段容器 | `data-anchor` | scroll 定位各 section |
| 區段標題 | `[data-anchor] > div` + `filter(has_text=title)` | `section_header()`；**是 `<div>` 非 heading** |
| PrimeVue 元件 | `data-pc-name`（toggleswitch/select/datatable…） | 元件互動 |
| 填寫建議側欄 | `aside` + `has_text="填寫建議"` | 2-3-11 |
| 即時預覽面板 | `[data-preview-panel-root]` | 2-3-12 |
| 預覽內容元素 | `data-preview-element`（activity-banner / activity-name / activity-date / activity-location / activity-organizer / activity-intro） | 2-3-12 內容驗證 |

## 已驗證 data-field-id（節錄；完整清單跑 inventory 回填）

| field-id | 欄位 | 備註 | 驗證日期 |
|---|---|---|---|
| `ActivityInfo_Introduction_name` | 活動名稱 | 容器內 `get_by_role("textbox")` | 2026-06-07 |
| `ActivityInfo_Introduction_startTime` | 活動開始時間 | 用 `field_datepicker_input()`，**勿用 `date_input_by_label`**（label 與 input 不同父層） | 2026-05-18 |
| `ActivityInfo_RegistrationMethod_regMethod` | 報名方式 | **Quill editor**，非一般 input（POC 排除） | 2026-06-07 |
| `areaList` | 區域清單 | 有 data-field-id | 2026-05-20 |
| `sectionList` | 組別清單 | 有 data-field-id | 2026-05-20 |
| （sessionList） | 場次清單 | **無 data-field-id**，改 `get_by_text` | 2026-05-20 |

## 元素 tag 陷阱（get_by_role 會永遠 timeout 的元素）

| 元素 | 實際 tag | 正確 selector | 驗證日期 |
|---|---|---|---|
| 「新增場次」 | `<div>` | `get_by_text("新增場次", exact=True)` | 2026-05-20 |
| 「批量新增場次」 | `<div>` | `get_by_text("批量新增場次", exact=True)` | 2026-05-20 |
| 區段標題（如「活動介紹」） | `<div>` | `[data-anchor] > div` + filter | 2026-05-18 |

## Tabs（PrimeVue lazy render）

- inactive panel **不在 DOM 中**；操作 panel 內元素前必先 click tab + 等 1 秒。
- tab button 含 SVG icon，accessible name 被污染 → **用 `.filter(has_text=...)` 不用 `name=`**：
  ```python
  page.locator("[role='tab']").filter(has_text="報名欄位設定").first.click()
  page.wait_for_timeout(1000)
  ```
- 適用 tab：報名欄位設定（2-3-8）、憑證與報到管理（2-3-9）。

## Label 事實

- 必填欄位 label 完整文字是 `* label text`（含 `<span>*</span>`）→ `get_by_text(label, exact=True)` 找不到；改 `field_label(page, fid)`。
- 部分欄位（如 registrantFields）**無 `<label>` 元素**，只驗容器可見。
- 每個欄位 DOM 結構獨立，**不可跨欄位類推**。

## 表單輸入事實

- **Playwright keyboard 事件不觸發 Vue dirty tracking** → 「儲存變更」dirty set 為空、不送 PATCH。資料寫入走 `PATCH /reventmodule/Entity/EVEvent`（`page.evaluate(fetch)` + `credentials:'include'`，見 `tests/integration/_shared_create.py::patch_event_info()`）。驗證日期：2026-06-07。
- **但 blur autosave 不受 dirty set 影響**（2026-07-10 IT-07 實測）：`fill()` + Tab 觸發 blur 後約 2 秒內自動 PATCH 草稿，重開值保留——單欄位資料前置可用「fill+Tab+等 2 秒」取代 `patch_event_info`。
- **autosave 機制全貌（2026-07-11 src 解碼，IT-07 8 案實測）**：blur→`dispatchSectionAutoSave`→依 section 分派到 **4 個 1500ms debounce** 存檔器，橫跨全部 4 tab（活動資訊全部；活動規則僅 OpenRegistrationTime/ApplicantsLimit/RegisrationBtnNote；報名欄位 RegistrationFieldSetting_*；憑證報到 CertificateManagement_Setting）。**僅草稿有效**（status==='2' 已啟用完全不 autosave）。**不走 debounce 而即時 PATCH**：圖片上傳、分組子表單 area/session/section（300ms row CRUD）、白黑名單匯入——故子表單「新增列即持久化」與 autosave 是不同路徑。
- checkbox 操作前先 `is_checked()` 檢查，避免長跑環境誤 uncheck（2026-05-20）。
- PrimeVue Checkbox：label text click 無效（input 隱藏），用 `input[value='X'].click(force=True)`。

## 導航事實

- `open_direct()`（直接 goto）前先 goto 活動列表一次，否則 `router.back()`（儲存並離開）會跳 `about:blank`（2026-05-18）。
- 分組管理 `groupingBasis` 可能已預選（如場次），enable 前先檢查狀態再決定是否 click（2026-05-20）。

## aside 事實

- 填寫建議（2-3-11）與即時預覽（2-3-12）在 `<aside>`，`inventory_fields.py` 只掃 `main` 掃不到，需 `inventory_aside.py`。
- 填寫建議清單項：`aside ul li a`，tick icon 是 `img[src^="data:image/svg"]` 且 `alt=""`（**src 寫 alt="completed" 不可信**）。
- `filter()` 後 chained `count()` 在含 data:svg img 的結構不穩定 → 改驗各已知文字 visible（2026-05-14）。

## 必填驗證錯誤提示事實（2026-07-09 IT-02 實測驗證）

- 送出 gate 純前端：「儲存變更」→ `runSaveAll()` → `validateAllRequired()`，有空必填即擋下不送 PATCH；後端 `WMAEVEvent` 無 `[Required]`。
- **紅框**：欄位元件加 class `p-invalid`（PrimeVue `:invalid`）。
- **欄位下方紅字**：`.errorText`（`STErrorText.vue`），文字格式 `<欄位中文名>：必填`（硬編碼非 i18n）。
- **滾動**：`[data-field="<field>"]`（與 `data-field-id` 同一 div）`scrollIntoView({block:'center'})` 到第一個錯誤欄位。
- **草稿預設值陷阱**：`create_draft()` 自動帶預設「活動名稱」→ 驗名稱必填前需先清空（`fill("")` 會更新 v-model；dirty tracking 只影響 PATCH 持久化，不影響前端驗證）。
- 「活動類型」永鎖（IsDisabled）且預設有值，不會觸發必填。
- FileList/PickTable/GroupManage/PickLocation 類必填不出欄位紅字，走**區段 well**（`_setSectionWell`）— well DOM 樣態未探明。
- 報名者/陪伴者/參與人欄位由另一 validator 負責，訊息為「至少需選擇一個欄位」。
- **跨 tab 紅字保留**（2026-07-09 IT-02 實測）：Tab1 點儲存觸發全域驗證後，切到 Tab2/Tab4（lazy render），該 tab 必填欄位的 `.errorText` 由 state 補渲、正常顯示——跨 tab 必填可用「先儲存再切 tab」驗。

## 字數上限（Maxlength）事實（2026-07-09 IT-03 實測驗證）

- 前端上限屬性 = PageFormItem 的 `Maxlength`（src：`PageFormItem.ts` L62）；InputText 落地為原生 `maxlength`（輸入截斷）+ counter `<n> / <上限>`。
- 生效欄位（實測截斷）：活動名稱 100、活動時間描述 60、憑證備註文字 100、陪伴者顯示名稱 10。
- **Editor（Quill）的 Maxlength 設定不生效**：consentContent/checkinNotice 設 300——**鍵盤實打**可輸入第 301 字（排除 fill 繞過事件的疑慮）、Editor 無 counter 顯示、送出也無字數紅字（潛在缺陷，截圖佐證 `reports/20260709_IT03_v7_run/`）。
- Editor 類欄位驗證注意：contenteditable 用 `fill()` 會繞過鍵盤事件；驗「輸入端攔截」須 `press_sequentially()` 實打。截圖證據須在測試結束前把目標欄位 `scroll_into_view`（點儲存後畫面會滾回 Tab1 第一個錯誤欄位）。
- 無 Maxlength 的文字欄（活動地點/相應網址文字/相應網址/活動介紹等）超量輸入送出無任何字數提示（後端有 MaxLength 但前端無防呆）。

## 條件欄位事實（2026-07-10 使用者實操側錄驗證）

- **分組子表單（GroupManage）欄位 id 帶動態時間戳尾碼**：實際 `data-field-id` 是 `areaNodeName_1783672074039` 這種格式（`<Id>_<ms timestamp>`），每次新增列都不同 → 定位用前綴 `[data-field-id^='areaNodeName']`，不可寫死。
- **CheckinTimeRow 自訂模式**：`checkinStartRow`/`checkinEndRow` 選「自訂」後長出獨立欄位 `CertificateManagement_Setting_checkinStartRow-custom` / `…checkinEndRow-custom`（DatePicker）。
- **PickTable「新增自訂欄位」彈窗**：陪伴者欄位/參與人欄位/憑證顯示資訊/報名者欄位皆有；彈窗內（欄位名稱 InputText、欄位類型 Select、檢核設定 Select、確認鈕）**無 data-field-id**，需文字/角色定位。⚠ **彈窗標題依 PickTable prop 客製**（報名者欄位處實測為「新增報名欄位」而非「新增自訂欄位」）→ 不可用標題定位 dialog；按鈕（label=新增自訂欄位）要鎖定所屬欄位容器內再點，dialog 取 `.p-dialog` 最後開啟者（2026-07-11 IT-03 AC4 教訓）。欄位名稱輸入無 maxlength（後端 200）＝ISS-002 第 8 欄。
- **憑證備註文字（credentialNote）有預設文案**（「請於報到時出示此憑證…」）→ 同活動名稱，必填空值情境不存在。
- **同意條款（evPrivacyPolicyEntity）開啟 isPrivacyPolicy 後自動帶預設值「個資使用聲明」**（2026-07-10 AC5a 實測）→ 必填空值情境不存在。
- **子表單無驗證提示（2026-07-10 dom 探勘更正，推翻先前「卸載說」）**：全域儲存後子表單**仍在 DOM、新增列保留**（切 tab 往返也保留）；但列內必填欄位空值**完全沒有任何提示**——areaList 容器 HTML 零 `p-invalid`/零 `.errorText`/零「必填」字樣，同次儲存他欄有 15 條紅字。前端儲存驗證未涵蓋分組子表單＝產品缺陷 [ISS-004]。
- 條件展開鏈全數實測確認：isPrivacyPolicy→evPrivacyPolicyEntity；registrationCloseTo=自訂→custom；allowModify→modifyDeadline(+custom)；備註 type=自訂→regButtonRemarkCustom；isGroupingRequired→groupSelectionTiming/groupingBasis；勾 Area/Session/Section→對應 List+子表單；whitelistEnabled→下載/上傳；hasCompanion→companionDisplayName+companionFields；isParticipantDataRequired→participantFields；isConsentRequired→consentContent；needCheckinNotice→checkinNotice；dispatchMode 三選（市民碼/單一/多組）。
- 側錄原始 log：session scratchpad `record_log.jsonl`（243 事件）；全開欄位的測試活動 pkid=34168368758263808（已儲存）。

## 待確認（探勘後回填）

- 2-2-5-D AC5/6：管理工作人員名單 modal selector；下載範本按鈕文字。
- 2-3-3-B AC2：活動數據看板跳轉按鈕 DOM / click 行為。
- 區段 well（`_setSectionWell`）DOM 樣態（IT-02 AC4、FileList 類必填提示）。
