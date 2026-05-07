"""2-2-4 活動列表欄位 共用測試輔助。"""
from __future__ import annotations
from playwright.sync_api import Page

from lib.selectors import EventListPage


def open_event_list(page: Page, base_url: str) -> None:
    page.goto(base_url + EventListPage.PATH, wait_until="domcontentloaded")
    EventListPage.reset_button(page).wait_for(state="visible", timeout=15000)
