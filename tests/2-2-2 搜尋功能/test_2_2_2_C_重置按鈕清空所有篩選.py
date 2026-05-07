"""
工項：2-2-2-C 重置按鈕清空所有篩選
規格：specs/2-2-2 搜尋功能/2-2-2-C 重置按鈕清空所有篩選.md
"""
from __future__ import annotations
import pytest
from playwright.sync_api import Page, expect

from lib.selectors import EventListPage

from . import _shared

WBS_ID = "2-2-2-C"
pytestmark = [pytest.mark.wbs(WBS_ID), pytest.mark.module("2-2-2")]


def test_AC1_重置按鈕存在可點(page: Page, config, report_attach):
    """AC1：搜尋區具備「重置」按鈕，可點擊。"""
    _shared.open_event_list(page, config["base_url"])
    btn = EventListPage.reset_button(page)
    report_attach(url=page.url, expected="重置按鈕可見且未禁用")
    expect(btn).to_be_visible()
    expect(btn).to_be_enabled()
    report_attach(actual="重置按鈕可見且未禁用")


@pytest.mark.xfail(
    reason="主辦單位 MultiSelect 互動 selector 尚未解碼（點開/驗已選/驗清空），"
    "待 src 二次解碼或 pytest 紅了用 HTML dump 補；見 plan.md P5"
)
def test_AC2_重置後主辦單位回未選(page: Page, config, report_attach):
    """AC2：點擊重置後，主辦單位篩選回到未選擇狀態。"""
    _shared.open_event_list(page, config["base_url"])
    report_attach(
        url=page.url,
        expected="先選擇任一主辦 → 點擊重置 → 主辦單位欄位顯示 placeholder（未選擇）",
    )
    pytest.fail("multiselect 互動 selector 待解；此 case 暫時 xfail")


def test_AC3_重置後活動日期清空(page: Page, config, report_attach):
    """AC3：點擊重置後，活動日期清空（無日期值）。"""
    _shared.open_event_list(page, config["base_url"])
    date_input = EventListPage.date_input(page)
    report_attach(
        url=page.url,
        expected="填入日期 → 點擊重置 → 日期 input 的 value 為空",
    )

    date_input.fill("2025-01-01")
    expect(date_input).not_to_have_value("")

    EventListPage.reset_button(page).click()
    page.wait_for_timeout(1000)

    expect(date_input).to_have_value("")
    report_attach(actual="日期 input 重置後 value 為空")


def test_AC4_重置後活動名稱清空(page: Page, config, report_attach):
    """AC4：點擊重置後，活動名稱輸入框清空。"""
    _shared.open_event_list(page, config["base_url"])
    name_input = EventListPage.name_input(page)
    report_attach(
        url=page.url,
        expected="填入活動名稱 → 點擊重置 → 名稱 input 的 value 為空",
    )

    name_input.fill("any_keyword")
    expect(name_input).to_have_value("any_keyword")

    EventListPage.reset_button(page).click()
    page.wait_for_timeout(1000)

    expect(name_input).to_have_value("")
    report_attach(actual="名稱 input 重置後 value 為空")


def test_AC5_重置自動觸發查詢(page: Page, config, report_attach):
    """AC5：點擊重置會自動觸發查詢，列表回到無篩選狀態。

    驗證策略：
    1. 撈基線列數（page load 後預設應有資料）
    2. 填一個極不可能命中的關鍵字 → 套用 → 預期列數變化（通常變 0 或極少）
    3. 重置 → 等列表更新 → 列數應回到 ≥ 基線（重置後無篩選 = 全顯示）
    """
    _shared.open_event_list(page, config["base_url"])
    rows = EventListPage.list_rows(page)
    page.wait_for_timeout(1500)
    baseline = rows.count()
    report_attach(
        url=page.url,
        expected=f"重置後列數應 ≥ 基線（{baseline}），代表重置自動觸發了無篩選查詢",
    )

    if baseline == 0:
        pytest.skip("基線無資料，無法驗證重置後恢復；請確認測試環境有測試活動")

    EventListPage.name_input(page).fill("__should_not_match_xyz__")
    EventListPage.apply_button(page).click()
    page.wait_for_timeout(1500)
    filtered = rows.count()

    EventListPage.reset_button(page).click()
    page.wait_for_timeout(1500)
    after_reset = rows.count()

    report_attach(
        actual=f"基線 {baseline} 列；過濾後 {filtered} 列；重置後 {after_reset} 列"
    )
    assert after_reset >= baseline, (
        f"重置後列數 {after_reset} 未恢復到基線 {baseline}；"
        f"可能重置未自動觸發查詢，或仍套用前一個篩選"
    )
