"""
工項：2-2-5-A 操作功能（5 子項：a/b/c/d/f；e/g 待確認跳過）
規格：specs/2-2-5-A 操作功能/

實作狀態（src 解碼 2026-05-06）：
- A-a 已實作（viewActivityData 跳轉 + title 顯示活動名）→ 完整可驗
- A-b/c/d/f：EVEvent.controller.ts L200-222 中 4 個對應 menu action 註解未啟用
  → 按鈕本體（在 actionCol 中）會渲染但 click 無效
  → AC1（按鈕存在）可驗，AC2 起標 SKIP-pending

策略：等前端解註後，去掉相應 SKIP 標記就能跑下載驗證。
"""
from __future__ import annotations
import pytest
from playwright.sync_api import Page

from lib.selectors import EventListPage, DashboardDetailPage

from . import _shared

pytestmark = [pytest.mark.module("2-2-5-A")]


# ============================================================
# 2-2-5-A-a 查看活動數據（已實作，完整驗證）
# ============================================================

@pytest.mark.wbs("2-2-5-A-a")
def test_2_2_5_A_a_AC1_第一個icon可點(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    icon = EventListPage.action_icon(_shared.first_row(page), 1)
    report_attach(url=page.url, expected="操作欄第 1 個 icon 可見")
    icon.wait_for(state="visible", timeout=10000)
    report_attach(actual="第 1 個 icon visible")


@pytest.mark.wbs("2-2-5-A-a")
def test_2_2_5_A_a_AC2_展開後可看到查看活動數據(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_activity_data_menu(page)
    item = EventListPage.menu_item_by_text(page, "查看活動數據")
    report_attach(url=page.url, expected="menu 中含『查看活動數據』")
    item.wait_for(state="visible", timeout=5000)
    report_attach(actual="menu 命中『查看活動數據』")


@pytest.mark.wbs("2-2-5-A-a")
def test_2_2_5_A_a_AC3_點擊後跳轉URL正確(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_activity_data_menu(page)
    EventListPage.menu_item_by_text(page, "查看活動數據").click()
    page.wait_for_url("**/DashboardDetail/**", timeout=15000)
    report_attach(url=page.url, expected="URL 含 DashboardDetail + source=EVEvent + pkid=")
    assert DashboardDetailPage.url_pattern_match(page.url), f"URL pattern 不符：{page.url}"
    report_attach(actual=f"URL 命中：{page.url}")


@pytest.mark.wbs("2-2-5-A-a")
def test_2_2_5_A_a_AC4_跳轉後title顯示活動名(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    page.wait_for_timeout(1500)
    name_before = EventListPage.cell_text(_shared.first_row(page), "活動名稱")
    _shared.open_activity_data_menu(page)
    EventListPage.menu_item_by_text(page, "查看活動數據").click()
    page.wait_for_url("**/DashboardDetail/**", timeout=15000)
    page.wait_for_timeout(2000)
    title = DashboardDetailPage.page_title_text(page)
    report_attach(url=page.url, expected=f"title 區包含『{name_before}』")
    report_attach(actual=f"title 區文字：『{title}』")
    assert name_before and name_before in title, f"title『{title}』未含列表活動名『{name_before}』"


# ============================================================
# 2-2-5-A-b 匯出報名筆數/人數統計 Excel（前端 menu action 未啟用）
# ============================================================

_BUTTON_TEXT_A_B = "匯出報名筆數/人數統計 Excel"  # spec 文字；實際待確認


@pytest.mark.wbs("2-2-5-A-b")
@pytest.mark.xfail(reason="依舊版 src 推測 menu action 註解未啟用；新版測試機可能已啟用（XPASS 表示可解 xfail）；spec 文字也待與 src 對齊", strict=False)
def test_2_2_5_A_b_AC1_按鈕存在(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_activity_data_menu(page)
    EventListPage.menu_item_by_text(page, _BUTTON_TEXT_A_B).wait_for(state="visible", timeout=5000)


@pytest.mark.wbs("2-2-5-A-b")
@pytest.mark.skip(reason="前端 menu action 註解未啟用；click 無實際 download")
def test_2_2_5_A_b_AC2_點擊觸發下載_xlsx(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_activity_data_menu(page)
    with page.expect_download(timeout=15000) as dl_info:
        EventListPage.menu_item_by_text(page, _BUTTON_TEXT_A_B).click()
    download = dl_info.value
    report_attach(url=page.url, actual=f"下載檔名：{download.suggested_filename}")
    assert download.suggested_filename.endswith(".xlsx"), f"非 xlsx：{download.suggested_filename}"


# ============================================================
# 2-2-5-A-c 匯出報到筆數/人數統計 Excel（同上）
# ============================================================

_BUTTON_TEXT_A_C = "匯出報到筆數/人數統計 Excel"


@pytest.mark.wbs("2-2-5-A-c")
@pytest.mark.xfail(reason="依舊版 src 推測 menu action 註解未啟用；新版測試機可能已啟用（XPASS 表示可解 xfail）", strict=False)
def test_2_2_5_A_c_AC1_按鈕存在(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_activity_data_menu(page)
    EventListPage.menu_item_by_text(page, _BUTTON_TEXT_A_C).wait_for(state="visible", timeout=5000)


@pytest.mark.wbs("2-2-5-A-c")
@pytest.mark.xfail(reason="依舊版 src 推測 menu action 註解未啟用；新版測試機可能已啟用（XPASS 表示可解 xfail）", strict=False)
def test_2_2_5_A_c_AC2_點擊觸發下載_xlsx(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_activity_data_menu(page)
    with page.expect_download(timeout=15000) as dl_info:
        EventListPage.menu_item_by_text(page, _BUTTON_TEXT_A_C).click()
    assert dl_info.value.suggested_filename.endswith(".xlsx")


# ============================================================
# 2-2-5-A-d 匯出報名者性別/年齡/行政區統計 Excel（同上）
# ============================================================

_BUTTON_TEXT_A_D = "匯出報名者性別/年齡/行政區統計 Excel"


@pytest.mark.wbs("2-2-5-A-d")
@pytest.mark.xfail(reason="依舊版 src 推測 menu action 註解未啟用；新版測試機可能已啟用（XPASS 表示可解 xfail）", strict=False)
def test_2_2_5_A_d_AC1_按鈕存在(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_activity_data_menu(page)
    EventListPage.menu_item_by_text(page, _BUTTON_TEXT_A_D).wait_for(state="visible", timeout=5000)


@pytest.mark.wbs("2-2-5-A-d")
@pytest.mark.xfail(reason="依舊版 src 推測 menu action 註解未啟用；新版測試機可能已啟用（XPASS 表示可解 xfail）", strict=False)
def test_2_2_5_A_d_AC2_點擊觸發下載_xlsx(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_activity_data_menu(page)
    with page.expect_download(timeout=15000) as dl_info:
        EventListPage.menu_item_by_text(page, _BUTTON_TEXT_A_D).click()
    assert dl_info.value.suggested_filename.endswith(".xlsx")


# ============================================================
# 2-2-5-A-f 匯出取消報名統計 Excel（同上）
# ============================================================

_BUTTON_TEXT_A_F = "匯出取消報名統計 Excel"


@pytest.mark.wbs("2-2-5-A-f")
@pytest.mark.xfail(reason="依舊版 src 推測 menu action 註解未啟用；新版測試機可能已啟用（XPASS 表示可解 xfail）", strict=False)
def test_2_2_5_A_f_AC1_按鈕存在(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_activity_data_menu(page)
    EventListPage.menu_item_by_text(page, _BUTTON_TEXT_A_F).wait_for(state="visible", timeout=5000)


@pytest.mark.wbs("2-2-5-A-f")
@pytest.mark.xfail(reason="依舊版 src 推測 menu action 註解未啟用；新版測試機可能已啟用（XPASS 表示可解 xfail）", strict=False)
def test_2_2_5_A_f_AC2_點擊觸發下載_xlsx(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_activity_data_menu(page)
    with page.expect_download(timeout=15000) as dl_info:
        EventListPage.menu_item_by_text(page, _BUTTON_TEXT_A_F).click()
    assert dl_info.value.suggested_filename.endswith(".xlsx")
