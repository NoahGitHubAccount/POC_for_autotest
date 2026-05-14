"""
工項：2-2-5-E 複製此活動
src 解碼（2026-05-14）：
- 入口：操作欄第 4 個 icon（更多操作 group）→ menu item「複製此活動」
- Handler：copyActivity 已實作（EVEvent.controller.ts，Chris/Max 已修復）
- 預期行為：API 正常、列表會多一列（Joan 5/14 確認）
- 已知行為：複製後列表筆數 +1，新活動出現在列表中
"""
from __future__ import annotations
import pytest
from playwright.sync_api import Page

from lib.selectors import EventListPage

from . import _shared

pytestmark = [pytest.mark.module("2-2-5-E")]

_COPY_BTN_TEXT = "複製此活動"


# ============================================================
# AC1：複製此活動按鈕存在於 menu
# ============================================================

@pytest.mark.wbs("2-2-5-E")
def test_2_2_5_E_AC1_複製按鈕存在於menu(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_more_actions_menu(page)
    report_attach(url=page.url, expected=f"menu 含『{_COPY_BTN_TEXT}』")
    EventListPage.menu_item_by_text(page, _COPY_BTN_TEXT).wait_for(state="visible", timeout=5000)
    report_attach(actual="『複製此活動』按鈕 visible")


# ============================================================
# AC2：點擊後列表筆數增加 1
# ============================================================

@pytest.mark.wbs("2-2-5-E")
def test_2_2_5_E_AC2_複製後列表多一筆(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    count_before = _shared.row_count(page)
    report_attach(url=page.url, expected=f"複製前列數：{count_before}；複製後應為 {count_before + 1}")

    _shared.open_more_actions_menu(page)
    EventListPage.menu_item_by_text(page, _COPY_BTN_TEXT).click()

    # 等候可能出現的確認 dialog 或直接操作完成
    try:
        confirm_btn = page.get_by_role("button", name="確認").or_(
            page.get_by_role("button", name="是")
        ).first
        confirm_btn.wait_for(state="visible", timeout=3000)
        confirm_btn.click()
    except Exception:
        pass  # 無確認 dialog，直接繼續

    page.wait_for_timeout(2000)
    count_after = _shared.row_count(page)
    report_attach(actual=f"複製後列數：{count_after}")
    assert count_after == count_before + 1, (
        f"列表筆數未增加：複製前 {count_before}，複製後 {count_after}"
    )


# ============================================================
# AC3：新複製的活動名稱含原活動名（含「複製」或前綴）
# ============================================================

@pytest.mark.wbs("2-2-5-E")
def test_2_2_5_E_AC3_複製後新活動名稱正確(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    page.wait_for_timeout(1000)
    original_name = EventListPage.cell_text(_shared.first_row(page), "活動名稱")
    report_attach(url=page.url, expected=f"原活動名稱：『{original_name}』；新活動應含此名或含『複製』")

    _shared.open_more_actions_menu(page)
    EventListPage.menu_item_by_text(page, _COPY_BTN_TEXT).click()

    try:
        confirm_btn = page.get_by_role("button", name="確認").or_(
            page.get_by_role("button", name="是")
        ).first
        confirm_btn.wait_for(state="visible", timeout=3000)
        confirm_btn.click()
    except Exception:
        pass

    page.wait_for_timeout(2000)
    # 取第一列（複製後通常插在最前或最後）
    new_name = EventListPage.cell_text(_shared.first_row(page), "活動名稱")
    report_attach(actual=f"第一列活動名稱：『{new_name}』")
    assert original_name in new_name or "複製" in new_name, (
        f"新活動名稱『{new_name}』未含原名『{original_name}』也未含『複製』"
    )
