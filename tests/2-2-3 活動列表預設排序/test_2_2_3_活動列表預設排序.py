"""
工項：2-2-3 活動列表預設排序
規格：specs/2-2-3 活動列表預設排序/2-2-3 活動列表預設排序.md

策略：
- 推測預設依「最近更新時間 DESC」（與 2-2-4-G 呼應）
- AC3 用字串 lexical compare 驗 DESC：對 ISO-like 格式有效；若實際格式不適用會紅，依 4 步流程修
- AC4 用 reload 後第一筆編號比對驗順序穩定
"""
from __future__ import annotations
import pytest
from playwright.sync_api import Page

from lib.selectors import EventListPage

from . import _shared

WBS_ID = "2-2-3"
pytestmark = [pytest.mark.wbs(WBS_ID), pytest.mark.module("2-2-3")]


def test_AC1_列表非空(page: Page, config, report_attach):
    """AC1：進入頁面後列表至少有一列資料（非隨機順序的前提是有資料）。"""
    _shared.open_event_list(page, config["base_url"])
    rows = EventListPage.list_rows(page)
    page.wait_for_timeout(1500)
    count = rows.count()
    report_attach(url=page.url, expected="列表至少 1 列")
    report_attach(actual=f"共 {count} 列")
    assert count > 0, "列表為空，無法驗證排序行為"


def test_AC2_具備最近更新時間欄(page: Page, config, report_attach):
    """AC2：表頭具備「最近更新時間」欄（關鍵字 fallback：更新時間 / 最近更新）。"""
    _shared.open_event_list(page, config["base_url"])
    headers = EventListPage.table_headers(page)
    report_attach(url=page.url, expected="表頭含『更新時間』或『最近更新』")
    idx = EventListPage.column_index_by_header(page, "最近更新", "更新時間")
    report_attach(actual=f"表頭：{headers}；命中 index={idx}")


def test_AC3_預設依更新時間DESC(page: Page, config, report_attach):
    """AC3：列表預設依「最近更新時間」DESC 排序（lexical compare）。

    若實際時間格式 lexical compare 不適用 DESC（例如帶「上午/下午」），此 case 紅了再進修 parser。
    """
    _shared.open_event_list(page, config["base_url"])
    page.wait_for_timeout(1500)

    values = EventListPage.column_values(page, "最近更新", "更新時間")
    report_attach(
        url=page.url,
        expected=f"取出 {len(values)} 筆「更新時間」值，每筆 ≥ 下一筆（DESC）",
    )

    if len(values) < 2:
        report_attach(actual=f"資料不足比對：{values}")
        pytest.skip("列表少於 2 列，無法驗證排序方向")

    bad = []
    for i in range(len(values) - 1):
        if values[i] < values[i + 1]:
            bad.append((i, values[i], values[i + 1]))

    report_attach(actual=f"共 {len(values)} 筆；違反 DESC 處 {len(bad)} 個（前 3：{bad[:3]}）")
    assert not bad, f"預設排序非 DESC，違反處：{bad[:3]}"


def test_AC4_重整後順序穩定(page: Page, config, report_attach):
    """AC4：reload 後第一筆活動的識別欄（活動名稱或編號）應與前一致，代表排序穩定。"""
    _shared.open_event_list(page, config["base_url"])
    rows = EventListPage.list_rows(page)
    page.wait_for_timeout(1500)

    if rows.count() == 0:
        pytest.skip("列表為空，無法驗證")

    name_before = EventListPage.cell_text(rows.nth(0), "活動名稱")
    report_attach(url=page.url, expected=f"reload 後第一筆活動名稱仍為「{name_before}」")

    page.reload(wait_until="domcontentloaded")
    EventListPage.reset_button(page).wait_for(state="visible", timeout=15000)
    page.wait_for_timeout(1500)

    name_after = EventListPage.cell_text(rows.nth(0), "活動名稱")
    report_attach(actual=f"reload 前「{name_before}」；reload 後「{name_after}」")
    assert name_before == name_after, "reload 後第一筆活動變了，預設排序非穩定"
