"""2-3-13 日期欄位先後順序防呆 共用測試輔助。

進入活動編輯頁的方式（src 解碼 2026-05-06）：
- 從列表頁點「活動名稱」cell（SetEvent_CellClick 會 router push 到 EVEventEdit）
- URL pattern：`/EVEventEdit/source=EVEvent&pkid=<id>`
"""
from __future__ import annotations
from playwright.sync_api import Page, Locator

from lib.selectors import EventListPage, EVEventEditPage


def open_event_list(page: Page, base_url: str) -> None:
    page.goto(base_url + EventListPage.PATH, wait_until="domcontentloaded")
    EventListPage.reset_button(page).wait_for(state="visible", timeout=15000)
    page.wait_for_timeout(1500)


def open_first_event_edit(page: Page, base_url: str) -> None:
    """從列表頁點第一筆活動的「活動名稱」cell 進入編輯頁。"""
    open_event_list(page, base_url)
    first_row = EventListPage.list_rows(page).nth(0)
    name_idx = EventListPage.column_index_by_header(page, "活動名稱")
    name_cell = first_row.locator("td").nth(name_idx)
    name_cell.click()
    page.wait_for_url("**/EVEventEdit/**", timeout=15000)
    page.wait_for_timeout(1500)


def fill_datepicker(page: Page, label_text: str, value: str) -> None:
    """填 DatePicker 並 press Enter 觸發 v-model 更新（PrimeVue 毛病，2026-05-06 經驗）。"""
    inp = EVEventEditPage.date_input_by_label(page, label_text)
    inp.fill(value)
    inp.press("Enter")
    page.wait_for_timeout(500)
