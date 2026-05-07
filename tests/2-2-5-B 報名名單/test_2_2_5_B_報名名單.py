"""
工項：2-2-5-B 報名名單（4 子項：a/b/c/d）
規格：specs/2-2-5-B 報名名單/

實作狀態（src 解碼 2026-05-06）：
- B-a 已實作（viewEnrollList 寫 sessionStorage 觸發 scrollIntoView 到 #registrationListTitle）→ 完整可驗
- B-b/c/d：DashboardDetail 內報名名單 toolbar 只有「下載報名資料」**單一按鈕**，
  src `PageSectionADActivityRegistrationList.handleToolbarAction` 是 console.log；
  spec 預期的三個分開按鈕 src 中**沒有**。AC 全標 SKIP-pending。
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
    """src 中：DashboardDetail 載入後若 sessionStorage 有 dashboardDetailScrollTo='registrationList'
    會 retry 找 #registrationListTitle 並 scrollIntoView。
    這裡只驗錨點 element 存在 + 可見（不嚴格驗 scroll 已完成）。"""
    _shared.open_event_list(page, config["base_url"])
    _shared.open_enroll_list_menu(page)
    EventListPage.menu_item_by_text(page, "查看報名名單").click()
    page.wait_for_url("**/DashboardDetail/**", timeout=15000)
    page.wait_for_timeout(3000)  # 等 retry scroll
    title = DashboardDetailPage.registration_title(page)
    report_attach(url=page.url, expected="頁面內含『報名名單』section title")
    expect(title).to_be_visible(timeout=10000)
    report_attach(actual="『報名名單』title visible")


# ============================================================
# 2-2-5-B-b 匯出報名紀錄 Excel（前端只有 console.log）
# ============================================================

@pytest.mark.wbs("2-2-5-B-b")
@pytest.mark.xfail(reason="依舊版 src 推測 toolbar handler 為 console.log；新版測試機可能已接真實 download（XPASS 表示可解 xfail）", strict=False)
def test_2_2_5_B_b_AC1_按鈕存在於報名名單section(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_enroll_list_menu(page)
    EventListPage.menu_item_by_text(page, "查看報名名單").click()
    page.wait_for_url("**/DashboardDetail/**", timeout=15000)
    page.wait_for_timeout(3000)
    btn = DashboardDetailPage.download_registration_button(page)
    btn.wait_for(state="visible", timeout=10000)


@pytest.mark.wbs("2-2-5-B-b")
@pytest.mark.xfail(reason="依舊版 src 推測 toolbar handler 為 console.log；新版測試機可能已接 download（XPASS 表示可解 xfail）", strict=False)
def test_2_2_5_B_b_AC2_點擊觸發下載_xlsx(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_enroll_list_menu(page)
    EventListPage.menu_item_by_text(page, "查看報名名單").click()
    page.wait_for_url("**/DashboardDetail/**", timeout=15000)
    page.wait_for_timeout(3000)
    with page.expect_download(timeout=15000) as dl_info:
        DashboardDetailPage.download_registration_button(page).click()
    assert dl_info.value.suggested_filename.endswith(".xlsx")


# ============================================================
# 2-2-5-B-c 匯出取消報名紀錄 Excel（前端無獨立按鈕）
# ============================================================

@pytest.mark.wbs("2-2-5-B-c")
@pytest.mark.xfail(reason="舊版 src 沒有獨立『匯出取消報名』按鈕；新版可能已加（XPASS 表示可解 xfail）", strict=False)
def test_2_2_5_B_c_AC1_按鈕存在(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_enroll_list_menu(page)
    page.get_by_role("menuitem", name="匯出取消報名紀錄").wait_for(state="visible", timeout=5000)


# ============================================================
# 2-2-5-B-d 匯出報到名單 Excel（前端無獨立按鈕）
# ============================================================

@pytest.mark.wbs("2-2-5-B-d")
@pytest.mark.xfail(reason="舊版 src 沒有獨立『匯出報到名單』按鈕；新版可能已加（XPASS 表示可解 xfail）", strict=False)
def test_2_2_5_B_d_AC1_按鈕存在(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_enroll_list_menu(page)
    page.get_by_role("menuitem", name="匯出報到名單").wait_for(state="visible", timeout=5000)
