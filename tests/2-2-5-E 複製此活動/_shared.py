"""2-2-5-E 複製此活動 共用測試輔助。"""
from __future__ import annotations
from playwright.sync_api import Page, Locator

from lib.selectors import EventListPage


def open_event_list(page: Page, base_url: str) -> None:
    page.goto(base_url + EventListPage.PATH, wait_until="domcontentloaded")
    EventListPage.reset_button(page).wait_for(state="visible", timeout=15000)
    page.wait_for_timeout(1500)


def first_row(page: Page) -> Locator:
    return EventListPage.list_rows(page).nth(0)


def open_more_actions_menu(page: Page) -> None:
    """點操作欄第 4 個 icon（更多操作 group）展開 menu。"""
    icon = EventListPage.action_icon(first_row(page), 4)
    icon.click()
    page.wait_for_timeout(500)


def row_count(page: Page) -> int:
    return EventListPage.list_rows(page).count()
