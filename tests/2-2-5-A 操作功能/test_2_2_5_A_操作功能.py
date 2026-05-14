"""
工項：2-2-5-A 操作功能（a/b/c/d/f 後端/前端皆完成；e/g 後端完成但前端 menu 尚未接）
規格：specs/2-2-5-A 操作功能/

src 解碼（2026-05-14 更新）：
- A-a：viewActivityData 跳轉 DashboardDetail → 完整驗
- A-b：exportRegistrationStats handler 已啟用，menu text「匯出報名筆數/人數統計 Excel」
- A-c：exportCheckInStats handler 已啟用，menu text「匯出報到筆數/人數統計 Excel」
- A-d：exportBasicStats handler 已啟用，menu text「匯出報名者性別/年齡/行政區統計 Excel」
- A-f：exportCancelRegistrationStats handler 已啟用，menu text「匯出取消報名統計 Excel」
- A-e：loginSource — 後端 5/12 完成，前端 menu 尚無此項 → xfail
- A-g：satisfactionFeedback — 後端 5/6 完成，前端 case 仍為註解 → xfail
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
# 2-2-5-A-b 匯出報名筆數/人數統計 Excel（後端4/29完成，前端handler已啟用）
# ============================================================

_BUTTON_TEXT_A_B = "匯出報名筆數/人數統計 Excel"


@pytest.mark.wbs("2-2-5-A-b")
def test_2_2_5_A_b_AC1_按鈕存在於menu(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_activity_data_menu(page)
    report_attach(url=page.url, expected=f"menu 含『{_BUTTON_TEXT_A_B}』")
    EventListPage.menu_item_by_text(page, _BUTTON_TEXT_A_B).wait_for(state="visible", timeout=5000)
    report_attach(actual="按鈕 visible")


@pytest.mark.wbs("2-2-5-A-b")
@pytest.mark.xfail(reason="規格指定『前景下載 + 處理中示意』，不走 browser download event；需改用 wait_for_response 或驗 loading indicator（待確認 API 路徑）", strict=False)
def test_2_2_5_A_b_AC2_點擊觸發下載_xlsx(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_activity_data_menu(page)
    report_attach(url=page.url, expected="點擊後觸發 xlsx 下載")
    with page.expect_download(timeout=30000) as dl_info:
        EventListPage.menu_item_by_text(page, _BUTTON_TEXT_A_B).click()
    download = dl_info.value
    report_attach(actual=f"下載檔名：{download.suggested_filename}")
    assert download.suggested_filename.endswith(".xlsx"), f"非 xlsx：{download.suggested_filename}"


# ============================================================
# 2-2-5-A-c 匯出報到筆數/人數統計 Excel（後端4/30完成，前端handler已啟用）
# ============================================================

_BUTTON_TEXT_A_C = "匯出報到筆數/人數統計 Excel"


@pytest.mark.wbs("2-2-5-A-c")
def test_2_2_5_A_c_AC1_按鈕存在於menu(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_activity_data_menu(page)
    report_attach(url=page.url, expected=f"menu 含『{_BUTTON_TEXT_A_C}』")
    EventListPage.menu_item_by_text(page, _BUTTON_TEXT_A_C).wait_for(state="visible", timeout=5000)
    report_attach(actual="按鈕 visible")


@pytest.mark.wbs("2-2-5-A-c")
@pytest.mark.xfail(reason="前景下載機制，不走 browser download event（同 A-b）", strict=False)
def test_2_2_5_A_c_AC2_點擊觸發下載_xlsx(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_activity_data_menu(page)
    report_attach(url=page.url, expected="點擊後觸發 xlsx 下載")
    with page.expect_download(timeout=30000) as dl_info:
        EventListPage.menu_item_by_text(page, _BUTTON_TEXT_A_C).click()
    download = dl_info.value
    report_attach(actual=f"下載檔名：{download.suggested_filename}")
    assert download.suggested_filename.endswith(".xlsx"), f"非 xlsx：{download.suggested_filename}"


# ============================================================
# 2-2-5-A-d 匯出報名者性別/年齡/行政區統計 Excel（後端5/1完成，前端handler已啟用）
# ============================================================

_BUTTON_TEXT_A_D = "匯出報名者性別/年齡/行政區統計 Excel"


@pytest.mark.wbs("2-2-5-A-d")
def test_2_2_5_A_d_AC1_按鈕存在於menu(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_activity_data_menu(page)
    report_attach(url=page.url, expected=f"menu 含『{_BUTTON_TEXT_A_D}』")
    EventListPage.menu_item_by_text(page, _BUTTON_TEXT_A_D).wait_for(state="visible", timeout=5000)
    report_attach(actual="按鈕 visible")


@pytest.mark.wbs("2-2-5-A-d")
def test_2_2_5_A_d_AC2_點擊觸發下載_xlsx(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_activity_data_menu(page)
    report_attach(url=page.url, expected="點擊後觸發 xlsx 下載")
    with page.expect_download(timeout=30000) as dl_info:
        EventListPage.menu_item_by_text(page, _BUTTON_TEXT_A_D).click()
    download = dl_info.value
    report_attach(actual=f"下載檔名：{download.suggested_filename}")
    assert download.suggested_filename.endswith(".xlsx"), f"非 xlsx：{download.suggested_filename}"


# ============================================================
# 2-2-5-A-f 匯出取消報名統計 Excel（後端4/29完成，前端handler已啟用）
# ============================================================

_BUTTON_TEXT_A_F = "匯出取消報名統計 Excel"


@pytest.mark.wbs("2-2-5-A-f")
def test_2_2_5_A_f_AC1_按鈕存在於menu(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_activity_data_menu(page)
    report_attach(url=page.url, expected=f"menu 含『{_BUTTON_TEXT_A_F}』")
    EventListPage.menu_item_by_text(page, _BUTTON_TEXT_A_F).wait_for(state="visible", timeout=5000)
    report_attach(actual="按鈕 visible")


@pytest.mark.wbs("2-2-5-A-f")
@pytest.mark.xfail(reason="前景下載機制，不走 browser download event（同 A-b）", strict=False)
def test_2_2_5_A_f_AC2_點擊觸發下載_xlsx(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_activity_data_menu(page)
    report_attach(url=page.url, expected="點擊後觸發 xlsx 下載")
    with page.expect_download(timeout=30000) as dl_info:
        EventListPage.menu_item_by_text(page, _BUTTON_TEXT_A_F).click()
    download = dl_info.value
    report_attach(actual=f"下載檔名：{download.suggested_filename}")
    assert download.suggested_filename.endswith(".xlsx"), f"非 xlsx：{download.suggested_filename}"


# ============================================================
# 2-2-5-A-e 匯出報名登入來源統計 Excel（後端5/12完成；前端 menu 尚無此項）
# ============================================================

_BUTTON_TEXT_A_E = "匯出報名登入來源統計 Excel"


@pytest.mark.wbs("2-2-5-A-e")
@pytest.mark.xfail(reason="後端5/12完成；前端 EVEventEntity menu 尚未新增此 action item（XPASS 表示前端已接入，可解 xfail）", strict=False)
def test_2_2_5_A_e_AC1_按鈕存在於menu(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_activity_data_menu(page)
    report_attach(url=page.url, expected=f"menu 含『{_BUTTON_TEXT_A_E}』")
    EventListPage.menu_item_by_text(page, _BUTTON_TEXT_A_E).wait_for(state="visible", timeout=5000)
    report_attach(actual="按鈕 visible")


@pytest.mark.wbs("2-2-5-A-e")
@pytest.mark.xfail(reason="前端 menu item 尚未存在，下載無法觸發", strict=False)
def test_2_2_5_A_e_AC2_點擊觸發下載_xlsx(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_activity_data_menu(page)
    with page.expect_download(timeout=30000) as dl_info:
        EventListPage.menu_item_by_text(page, _BUTTON_TEXT_A_E).click()
    download = dl_info.value
    report_attach(actual=f"下載檔名：{download.suggested_filename}")
    assert download.suggested_filename.endswith(".xlsx"), f"非 xlsx：{download.suggested_filename}"


# ============================================================
# 2-2-5-A-g 匯出滿意度問卷 Excel（後端5/6完成；前端 case 仍為註解）
# ============================================================

_BUTTON_TEXT_A_G = "匯出滿意度問卷 Excel"


@pytest.mark.wbs("2-2-5-A-g")
@pytest.mark.xfail(reason="後端5/6完成；前端 EVEvent.controller.ts satisfactionFeedback case 仍為註解（XPASS 表示前端已解註，可解 xfail）", strict=False)
def test_2_2_5_A_g_AC1_按鈕存在於menu(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_activity_data_menu(page)
    report_attach(url=page.url, expected=f"menu 含『{_BUTTON_TEXT_A_G}』")
    EventListPage.menu_item_by_text(page, _BUTTON_TEXT_A_G).wait_for(state="visible", timeout=5000)
    report_attach(actual="按鈕 visible")


@pytest.mark.wbs("2-2-5-A-g")
@pytest.mark.xfail(reason="前端 case 仍為註解，下載無法觸發", strict=False)
def test_2_2_5_A_g_AC2_點擊觸發下載_xlsx(page: Page, config, report_attach):
    _shared.open_event_list(page, config["base_url"])
    _shared.open_activity_data_menu(page)
    with page.expect_download(timeout=30000) as dl_info:
        EventListPage.menu_item_by_text(page, _BUTTON_TEXT_A_G).click()
    download = dl_info.value
    report_attach(actual=f"下載檔名：{download.suggested_filename}")
    assert download.suggested_filename.endswith(".xlsx"), f"非 xlsx：{download.suggested_filename}"
