"""2-3-11 左側填寫建議 共用輔助。"""
from __future__ import annotations
from playwright.sync_api import Page
from lib.selectors import EVEventEditPage


def open_event_edit(page: Page, base_url: str) -> None:
    EVEventEditPage.open_from_event_list(page, base_url)
