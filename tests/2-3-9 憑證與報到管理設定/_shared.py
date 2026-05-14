"""2-3-9 憑證與報到管理設定 共用輔助。"""
from __future__ import annotations
from playwright.sync_api import Page
from lib.selectors import EVEventEditPage


def open_event_edit(page: Page, base_url: str) -> None:
    EVEventEditPage.open_from_event_list(page, base_url)


def scroll_to_certificate_section(page: Page) -> None:
    """滾動到憑證與報到管理設定區段。"""
    section = page.get_by_text("憑證與報到管理", exact=True).first
    section.scroll_into_view_if_needed(timeout=10000)
    page.wait_for_timeout(500)
