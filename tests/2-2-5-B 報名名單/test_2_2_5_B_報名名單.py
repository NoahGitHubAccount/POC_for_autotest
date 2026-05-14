"""
工項：2-2-5-B 報名名單（a/b/c/d）
規格：specs/2-2-5-B 報名名單/

src 解碼（2026-05-14 更新）：
- B-a：viewEnrollList 跳轉 DashboardDetail + sessionStorage scroll → 完整驗
- B-b/c/d：EVEventEntity.ts 行操作第 2 個 icon（報名名單 group）menu 中已有獨立按鈕
  - B-b: 匯出報名名單 Excel（exportRegistrations，5/5 前端完成）
  - B-c: 匯出取消報名名單 Excel（exportCancelledRegistrations，5/5 前端完成）
  - B-d: 匯出報到名單 Excel（exportCheckedInRegistrations，5/5 前端完成）
  注意：DashboardDetail 頁面的 toolbar 仍只有「下載報名資料」單一按鈕（console.log），
  三個獨立匯出入口在「列表頁第 2 個 icon menu」，非 DashboardDetail 內。
"""
from __future__ import annotations
import pytest
from playwright.sync_api import Page, expect

from lib.selectors import EventListPage, DashboardDetailPage

from . import _shared

pytestmark = [pytest.mark.module("2-2-5-B")]


# ============================================================
# 2-2-5-B-a 查看報名名單（已實作，完整驗證）
# ============================================================

@pytest.mark.wbs("2-2-5-B-a")
def test_2_2_5_B_a_AC1_第二個icon可點(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    icon = EventListPage.action_icon(_shared.first_row(page), 2)
    report_attach(url=page.url, expected="操作欄第 2 個 icon 可見")
    icon.wait_for(state="visible", timeout=10000)
    report_attach(actual="第 2 個 icon visible")


@pytest.mark.wbs("2-2-5-B-a")
def test_2_2_5_B_a_AC2_展開後可看到查看報名名單(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_enroll_list_menu(page)
    item = EventListPage.menu_item_by_text(page, "查看報名名單")
    report_attach(url=page.url, expected="menu 中含『查看報名名單』")
    item.wait_for(state="visible", timeout=5000)
    report_attach(actual="menu 命中『查看報名名單』")


@pytest.mark.wbs("2-2-5-B-a")
def test_2_2_5_B_a_AC3_點擊後跳轉URL正確(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_enroll_list_menu(page)
    EventListPage.menu_item_by_text(page, "查看報名名單").click()
    page.wait_for_url("**/DashboardDetail/**", timeout=15000)
    report_attach(url=page.url, expected="URL 含 DashboardDetail + source=EVEvent + pkid=")
    assert DashboardDetailPage.url_pattern_match(page.url), f"URL pattern 不符：{page.url}"
    report_attach(actual=f"URL 命中：{page.url}")


@pytest.mark.wbs("2-2-5-B-a")
def test_2_2_5_B_a_AC4_跳轉後可見報名名單錨點(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_enroll_list_menu(page)
    EventListPage.menu_item_by_text(page, "查看報名名單").click()
    page.wait_for_url("**/DashboardDetail/**", timeout=15000)
    page.wait_for_timeout(3000)
    title = DashboardDetailPage.registration_title(page)
    report_attach(url=page.url, expected="頁面內含『報名名單』section title")
    expect(title).to_be_visible(timeout=10000)
    report_attach(actual="『報名名單』title visible")


# ============================================================
# 2-2-5-B-b 匯出報名名單 Excel（5/5 前端完成；入口在列表頁第 2 個 icon menu）
# ============================================================

_BUTTON_TEXT_B_B = "匯出報名名單 Excel"


@pytest.mark.wbs("2-2-5-B-b")
def test_2_2_5_B_b_AC1_按鈕存在於menu(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_enroll_list_menu(page)
    report_attach(url=page.url, expected=f"menu 含『{_BUTTON_TEXT_B_B}』")
    EventListPage.menu_item_by_text(page, _BUTTON_TEXT_B_B).wait_for(state="visible", timeout=5000)
    report_attach(actual="按鈕 visible")


@pytest.mark.wbs("2-2-5-B-b")
def test_2_2_5_B_b_AC2_點擊觸發下載_xlsx(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_enroll_list_menu(page)
    report_attach(url=page.url, expected="點擊後觸發 xlsx 下載")
    with page.expect_download(timeout=30000) as dl_info:
        EventListPage.menu_item_by_text(page, _BUTTON_TEXT_B_B).click()
    download = dl_info.value
    report_attach(actual=f"下載檔名：{download.suggested_filename}")
    assert download.suggested_filename.endswith(".xlsx"), f"非 xlsx：{download.suggested_filename}"


# ============================================================
# 2-2-5-B-c 匯出取消報名名單 Excel（5/5 前端完成；入口在列表頁第 2 個 icon menu）
# ============================================================

_BUTTON_TEXT_B_C = "匯出取消報名名單 Excel"


@pytest.mark.wbs("2-2-5-B-c")
def test_2_2_5_B_c_AC1_按鈕存在於menu(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_enroll_list_menu(page)
    report_attach(url=page.url, expected=f"menu 含『{_BUTTON_TEXT_B_C}』")
    EventListPage.menu_item_by_text(page, _BUTTON_TEXT_B_C).wait_for(state="visible", timeout=5000)
    report_attach(actual="按鈕 visible")


@pytest.mark.wbs("2-2-5-B-c")
def test_2_2_5_B_c_AC2_點擊觸發下載_xlsx(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_enroll_list_menu(page)
    report_attach(url=page.url, expected="點擊後觸發 xlsx 下載")
    with page.expect_download(timeout=30000) as dl_info:
        EventListPage.menu_item_by_text(page, _BUTTON_TEXT_B_C).click()
    download = dl_info.value
    report_attach(actual=f"下載檔名：{download.suggested_filename}")
    assert download.suggested_filename.endswith(".xlsx"), f"非 xlsx：{download.suggested_filename}"


# ============================================================
# 2-2-5-B-d 匯出報到名單 Excel（5/5 前端完成；入口在列表頁第 2 個 icon menu）
# ============================================================

_BUTTON_TEXT_B_D = "匯出報到名單 Excel"


@pytest.mark.wbs("2-2-5-B-d")
def test_2_2_5_B_d_AC1_按鈕存在於menu(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_enroll_list_menu(page)
    report_attach(url=page.url, expected=f"menu 含『{_BUTTON_TEXT_B_D}』")
    EventListPage.menu_item_by_text(page, _BUTTON_TEXT_B_D).wait_for(state="visible", timeout=5000)
    report_attach(actual="按鈕 visible")


@pytest.mark.wbs("2-2-5-B-d")
def test_2_2_5_B_d_AC2_點擊觸發下載_xlsx(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_enroll_list_menu(page)
    report_attach(url=page.url, expected="點擊後觸發 xlsx 下載")
    with page.expect_download(timeout=30000) as dl_info:
        EventListPage.menu_item_by_text(page, _BUTTON_TEXT_B_D).click()
    download = dl_info.value
    report_attach(actual=f"下載檔名：{download.suggested_filename}")
    assert download.suggested_filename.endswith(".xlsx"), f"非 xlsx：{download.suggested_filename}"
