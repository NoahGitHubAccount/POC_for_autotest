"""
工項：2-3-3 活動基本資訊
src 解碼（2026-05-14，EVEventEdit.controller.ts）：
- Panel header Title：'活動資訊'（getPagePanelHeader）
- 子項 A：複製活動連結 PageLinkData（Text='複製活動連結'，IsDisable=true 初始）
- 子項 B：活動數據看板 PageLinkData（Text='活動數據看板'，IsDisable=false）
前置工項：2-3-2/4/7/11/12（完整填寫後功能才完整）
→ 基本存在性測試不受前置影響；功能性測試部分 xfail
"""
from __future__ import annotations
import pytest
from playwright.sync_api import Page, expect

from lib.selectors import EVEventEditPage

from . import _shared

pytestmark = [pytest.mark.module("2-3-3")]


# ============================================================
# AC1：活動資訊 section header 可見
# ============================================================

@pytest.mark.wbs("2-3-3")
def test_2_3_3_AC1_活動資訊section_header可見(page: Page, config, report_attach):
    _shared.open_event_edit(page, config["base_url"])
    report_attach(url=page.url, expected="頁面含『活動資訊』section header")
    header = EVEventEditPage.section_header(page, "活動資訊")
    expect(header).to_be_visible(timeout=10000)
    report_attach(actual="『活動資訊』header visible")


# ============================================================
# AC2：複製活動連結按鈕可見（初始 disabled）
# ============================================================

@pytest.mark.wbs("2-3-3-A")
def test_2_3_3_A_AC1_複製活動連結按鈕可見(page: Page, config, report_attach):
    _shared.open_event_edit(page, config["base_url"])
    report_attach(url=page.url, expected="頁面含『複製活動連結』按鈕")
    btn = page.get_by_text("複製活動連結", exact=True).first
    expect(btn).to_be_visible(timeout=10000)
    report_attach(actual="『複製活動連結』visible")


@pytest.mark.wbs("2-3-3-A")
@pytest.mark.xfail(reason="複製連結功能需前置工項 2-3-2/4/7 完成後才可啟用（IsDisable=true）；前置完成後應解 xfail", strict=False)
def test_2_3_3_A_AC2_複製活動連結按鈕可點擊(page: Page, config, report_attach):
    _shared.open_event_edit(page, config["base_url"])
    report_attach(url=page.url, expected="『複製活動連結』按鈕為 enabled 狀態")
    btn = page.get_by_text("複製活動連結", exact=True).first
    expect(btn).to_be_enabled(timeout=10000)
    report_attach(actual="按鈕 enabled")


# ============================================================
# AC3：活動數據看板按鈕可見且可點
# ============================================================

@pytest.mark.wbs("2-3-3-B")
def test_2_3_3_B_AC1_活動數據看板按鈕可見(page: Page, config, report_attach):
    _shared.open_event_edit(page, config["base_url"])
    report_attach(url=page.url, expected="頁面含『活動數據看板』按鈕")
    btn = page.get_by_text("活動數據看板", exact=True).first
    expect(btn).to_be_visible(timeout=10000)
    report_attach(actual="『活動數據看板』visible")


@pytest.mark.wbs("2-3-3-B")
def test_2_3_3_B_AC2_點擊活動數據看板跳轉DashboardDetail(page: Page, config, report_attach):
    _shared.open_event_edit(page, config["base_url"])
    report_attach(url=page.url, expected="點擊後跳轉至 DashboardDetail 頁")
    page.get_by_text("活動數據看板", exact=True).first.click()
    page.wait_for_url("**/DashboardDetail/**", timeout=15000)
    report_attach(actual=f"URL：{page.url}")
    assert "DashboardDetail" in page.url
