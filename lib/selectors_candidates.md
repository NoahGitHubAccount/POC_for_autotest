---
audit_date: 2026-05-05
target: 2-2-2-B 活動列表頁篩選 selector
source: src/sc_event_frontend/sc_event_frontend/src/
status: 待你審核 → OK 後我改 lib/selectors.py
---

# 2-2-2-B selector 審計報告

## 1. 從前端原始碼挖到的事實

### 1.1 篩選欄位定義來源

`src/model/entity/ActivityMgmt/EVEventEntity.ts` 第 332–346 行：

```ts
getCondition(orgCondition: Array<PageFormItem>): Array<PageFormItem> {
  let org = new PageFormItem({ Field: "evOrganizations", Name: "主辦單位", Type: PageItem.MultiSelect });
  let time = new PageFormItem({ Field: "StartTimeGe", Name: "活動日期", Type: PageItem.DatePicker });
  orgCondition.push(org);
  orgCondition.push(time);
  return orgCondition.filter(x => ['name', 'evOrganizations', 'StartTimeGe'].includes(x.Field));
}
```

→ **三個篩選欄位**（順序）：

| Field | Name（label 顯示文字） | Type |
|---|---|---|
| `name` | 活動名稱 | InputText（預設） |
| `evOrganizations` | 主辦單位 | MultiSelect |
| `StartTimeGe` | 活動日期 | DatePicker |

### 1.2 STFilter 渲染行為（每個欄位生出什麼 DOM）

`src/components/smartcityui/STFilter.vue`：

- 每個欄位外層 wrapper：`<div><div class="flex flex-col gap-[4px]"><label :for="item.Id">{{ t(item.Name) }}</label>...</div></div>`
- **InputText**（活動名稱）：`<InputText :id="item.Id" :name="item.Id" :placeholder="..." :aria-label="item.Name" ...>`
  - ✅ **有 aria-label="活動名稱"** ← 最穩定的錨點
- **MultiSelect**（主辦單位）：`<MultiSelect :id="item.Id" :name="item.Id" :placeholder="..." ...>`
  - ⚠️ **沒有 aria-label**；只有外層 `<label>主辦單位</label>` 並 for 一個空 id（PageFormItem.Id 預設 `""`）
- **DatePicker**（活動日期）：包在 `<STDatePicker>`，內部 PrimeVue DatePicker 有 `:id="..."` `:placeholder="..."`
  - ⚠️ **沒有 aria-label**；同上，外層 `<label>活動日期</label>` for 空 id

### 1.3 重置 / 套用按鈕

`STFilter.vue` 第 181–184 行：
```vue
<Button :label="t('Components.STFilter.Reset')" outlined ... @click="resetBtn"/>
<Button :label="t('Components.STFilter.Apply')" ... @click="searchBtn"/>
```
i18n 鍵 `Components.STFilter.Reset` / `.Apply` 渲染為「重置」/「套用」（CLAUDE.md 已記載 4-30 教訓）。
→ ✅ `get_by_role("button", name="重置")` / `name="套用"` 穩定。

### 1.4 `data-testid` 全 repo 掃描結果

```
0 個 match。前端目前完全沒有 testid。
```
→ 確認 P6 工項仍是「請前端加 testid」的長期解，本次走語意 selector。

### 1.5 表格欄位順序（影響 `name_cell_text`）

`EVEventEntity.ts` 第 49–57 行宣告欄位 Title：

| 欄位 (Field) | Title | 順序推測（依宣告順序）|
|---|---|---|
| `sn` | 活動編號 | 1 |
| `name` | 活動名稱 | 2 |
| `evOrganizations` | 主辦單位 | 3 |
| `unit` | 最小報到單位 | 4 |
| `startAndendTime` | 活動起迄時間 | 5 |
| `RegistStartAndEndTime` | 報名起迄時間 | 6 |
| `modifiedDate` | 最近更新時間 | 7 |
| `statusEntity` | 啟用狀態 | 8 |
| `rowActions` | 操作 | 9 |

→ 目前 `name_cell_text` 用 `td:nth(1)`（第 2 欄）合理；但若實際 DOM 表頭順序被 PageFactory 動態調整（例如先排序欄之類），可能會偏。**建議改成依表頭文字「活動名稱」找對應 column index，再取對應 td。**

---

## 2. 建議改寫對照表

| selector | 現況 | 建議 | 理由 |
|---|---|---|---|
| `name_input` | `page.get_by_label("活動名稱").first` | **不變** ✅ | aria-label 確認存在，目前最穩 |
| `organizer_input` | `page.locator(".p-multiselect").first` | `page.get_by_text("主辦單位", exact=True).locator("xpath=ancestor::div[contains(@class,'flex-col')]").locator(".p-multiselect")` | 鎖定「主辦單位」label 所屬 wrapper 內的 multiselect，避免「.first」遇到頁面其他多選元件時抓錯 |
| `date_input` | `page.locator("input.p-datepicker-input")` | `page.get_by_text("活動日期", exact=True).locator("xpath=ancestor::div[contains(@class,'flex-col')]").locator("input.p-datepicker-input")` | 同上理由，鎖定到「活動日期」wrapper 內 |
| `reset_button` | `page.get_by_role("button", name="重置")` | **不變** ✅ | 已驗證穩定 |
| `apply_button` | `page.get_by_role("button", name="套用")` | **不變** ✅ | 已驗證穩定 |
| `list_rows` | `page.locator("table tbody tr")` | **暫不變**，但加註「若 PageFactory 渲染 PrimeVue DataTable，可能要改 `[role='row']`」 | 需第一次跑紅了再決定 |
| `name_cell_text` | `row.locator("td").nth(1).inner_text()` | **改為依表頭定位**：先找到 `<th>活動名稱</th>` 的 column index，再 `td:nth(idx)` | 抗欄位順序變動 |

---

## 3. 風險 / 注意事項

1. **`organizer_input` / `date_input` 用了 xpath ancestor**：如果 wrapper class 名稱改了（`flex-col` 是 Tailwind utility，**有違 CLAUDE.md 第 3 條「不用 Tailwind utility class」**），會壞。
   - **替代方案**：用 `:has(label:text-is("主辦單位"))` CSS-like locator，但 Playwright 對 `:text-is` 有特殊語法需測。
   - 或是接受暫時違規（class 名稱本身穩定機率還行），先綠了再說。
   - **你來決定**：要我改純 CSS 派還是接受這個 xpath 折衷？

2. **`name_cell_text` 動態 column index**：實作上要 `_shared.py` 加一個 helper `column_index_by_header(page, "活動名稱")`，跑 selector 時動態算。多 1 次 DOM query 但抗變動。

3. **`PageFormItem.Id` 預設空字串**：意味著渲染出的 `id=""` 是真的空的。如果 PageFactory 之後改成自動 setIdByPath（看 PageFormItem.ts 有此方法），未來可改用 `page.locator("#evOrganizations")` 之類更乾淨的 selector。**目前先不依賴。**

---

## 4. 你需要看的事

請在下面三個地方留 ✅ 或 ❌+原因：

- [ ] §2 的 7 條建議：全收 / 部分收
- [ ] §3-1：xpath ancestor + Tailwind class（短期方案）vs 純 CSS `:has(label)` 重寫
- [ ] §3-2：`name_cell_text` 改動態 column index — 同意 / 維持 nth(1)

審完丟一句「OK」我就動 `lib/selectors.py`。如果有 ❌ 我改完再丟一份新的給你。

---

## 5. 我做不到、需要你 / 真實 DOM 確認的事

- 「活動名稱」InputText 是否真的渲染了 `<input aria-label="活動名稱">` 而非別的形式（vue-i18n missing-key fallback 行為通常是直回原字串，但保險起見要 DOM 看一眼）
- list 表格實際是 `<table>` 還是 PrimeVue DataTable 的 `[role="row"]` 結構
- 「套用 / 重置」按鈕在每個 viewport 是否都 visible（RWD 折疊）

→ 這些跑一輪 pytest 就會自動爆出來，不必先確認；紅了我們再用「Route B（你存一頁 HTML）」二修。
