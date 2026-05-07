"""2-2-5-A 操作功能 共用測試輔助。"""
from __future__ import annotations
from playwright.sync_api import Page, Locator

from lib.selectors import EventListPage


def open_event_list(page: Page, base_url: str) -> None:
    page.goto(base_url + EventListPage.PATH, wait_until="domcontentloaded")
    EventListPage.reset_button(page).wait_for(state="visible", timeout=15000)
    page.wait_for_timeout(1500)


def first_row(page: Page) -> Locator:
    """取列表第一筆活動 row。"""
    return EventListPage.list_rows(page).nth(0)


def open_activity_data_menu(page: Page) -> None:
    """點操作欄第 1 個 icon（活動數據 group）展開 menu。"""
    icon = EventListPage.action_icon(first_row(page), 1)
    icon.click()
    page.wait_for_timeout(500)
