"""2-2-3 活動列表預設排序 共用測試輔助（與 2-2-2 同款）。"""
from __future__ import annotations
from playwright.sync_api import Page

from lib.selectors import EventListPage


def open_event_list(page: Page, base_url: str) -> None:
    """進到活動列表頁並等到搜尋區可用。"""
    page.goto(base_url + EventListPage.PATH, wait_until="domcontentloaded")
    EventListPage.reset_button(page).wait_for(state="visible", timeout=15000)
