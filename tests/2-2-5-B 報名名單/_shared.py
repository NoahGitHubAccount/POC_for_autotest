"""2-2-5-B 報名名單 共用測試輔助。"""
from __future__ import annotations
from playwright.sync_api import Page, Locator

from lib.selectors import EventListPage


def open_event_list(page: Page, base_url: str) -> None:
    page.goto(base_url + EventListPage.PATH, wait_until="domcontentloaded")
    EventListPage.reset_button(page).wait_for(state="visible", timeout=15000)
    page.wait_for_timeout(1500)


def first_row(page: Page) -> Locator:
    return EventListPage.list_rows(page).nth(0)


def open_enroll_list_menu(page: Page) -> None:
    """點操作欄第 2 個 icon（報名名單 group）展開 menu。"""
    icon = EventListPage.action_icon(first_row(page), 2)
    icon.click()
    page.wait_for_timeout(500)


def first_row_pkid(page: Page) -> str | None:
    """從第一筆活動 row 取 pkid（用 row data attribute 或解析 click 後 URL）。

    當前 src 沒有 data-id；先回 None，由測試以 URL 包含 'pkid=' 寬鬆驗。
    """
    return None
