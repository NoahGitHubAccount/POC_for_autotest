"""
工項：2-2-2-B 主辦單位、活動日期、活動名稱篩選
規格：specs/2-2-2 搜尋功能/2-2-2-B 主辦單位、活動日期、活動名稱篩選.md
"""
from __future__ import annotations
import pytest
from playwright.sync_api import Page, expect

from lib.selectors import EventListPage

from . import _shared

WBS_ID = "2-2-2-B"
pytestmark = [pytest.mark.wbs(WBS_ID), pytest.mark.module("2-2-2")]


def test_AC1_主辦單位篩選元件存在(page: Page, config, report_attach):
    """AC1：活動列表頁面具備「主辦單位」篩選元件。"""
    _shared.open_event_list(page, config["base_url"])
    el = EventListPage.organizer_input(page)
    report_attach(url=page.url, expected="主辦單位 MultiSelect 元件可見且未禁用")
    expect(el).to_be_visible()
    expect(el).to_be_enabled()
    report_attach(actual="主辦單位 MultiSelect 元件可見且未禁用")


def test_AC2_活動日期篩選元件存在(page: Page, config, report_attach):
    """AC2：活動列表頁面具備「活動日期」單日選擇器。"""
    _shared.open_event_list(page, config["base_url"])
    el = EventListPage.date_input(page)
    report_attach(url=page.url, expected="活動日期 DatePicker input 可見且可編輯")
    expect(el).to_be_visible()
    expect(el).to_be_editable()
    report_attach(actual="活動日期 DatePicker input 可見且可編輯")


def test_AC3_活動名稱搜尋輸入框存在(page: Page, config, report_attach):
    """AC3：活動列表頁面具備「活動名稱」搜尋輸入框，可輸入文字。"""
    _shared.open_event_list(page, config["base_url"])
    el = EventListPage.name_input(page)
    report_attach(url=page.url, expected="可輸入文字到活動名稱欄位且回顯一致")
    expect(el).to_be_visible()
    el.fill("test_input")
    expect(el).to_have_value("test_input")
    report_attach(actual="輸入後欄位顯示 'test_input'")


def test_AC6_活動名稱模糊比對(page: Page, config, report_attach):
    """AC6：輸入活動名稱關鍵字 + 查詢後，列表所有可見列的活動名稱包含該關鍵字（模糊比對）。

    使用既有測試資料中的關鍵字 'huwyang'（已觀察到至少 'huwyang_活動測試_0424' 與 'huwyang_活動測試4'）。
    """
    keyword = "huwyang"
    _shared.open_event_list(page, config["base_url"])

    EventListPage.name_input(page).fill(keyword)
    EventListPage.apply_button(page).click()
    page.wait_for_timeout(1500)

    rows = EventListPage.list_rows(page)
    count = rows.count()

    report_attach(
        url=page.url,
        expected=f"所有可見列的活動名稱皆含關鍵字「{keyword}」（模糊比對，case-insensitive）",
    )

    if count == 0:
        report_attach(actual="列表為空（無符合資料）")
        pytest.fail(f"關鍵字「{keyword}」查無資料；請確認測試資料還在或更換關鍵字")

    bad: list[str] = []
    for i in range(count):
        name = EventListPage.name_cell_text(rows.nth(i))
        if keyword.lower() not in name.lower():
            bad.append(name)

    report_attach(actual=f"共 {count} 列，其中 {len(bad)} 列名稱不含關鍵字：{bad[:3]}")
    assert not bad, f"出現名稱不含「{keyword}」的列：{bad}"


def test_AC5_活動日期過濾方向性(page: Page, config, report_attach):
    """AC5：選擇日期 + 套用後，列表依「活動日期」過濾。

    語意說明：spec 原文寫「活動時間範圍涵蓋該日期」，但 `EVEventEntity.ts`
    `getCondition()` 顯示 backend 對應 field 為 `StartTimeGe`（start_time ≥ X）。
    本測試以 src 為事實來源，驗證「方向性」而非「逐列日期解析」：

      - 遠未來日期（2099-12-31）→ 列數 ≤ 基線（多數活動 start_time 不滿足 ≥ 2099）
      - 遠過去日期（2000-01-01）→ 列數 == 基線（所有活動 start_time 都 ≥ 2000）

    避開「不知道列表 datetime 渲染格式」的盲區，同時抓「填了沒反應」的偽綠。
    """
    _shared.open_event_list(page, config["base_url"])
    rows = EventListPage.list_rows(page)
    page.wait_for_timeout(1500)
    baseline = rows.count()

    report_attach(
        url=page.url,
        expected=f"基線 {baseline} 列；遠未來日期過濾後 ≤ 基線；遠過去日期過濾後 == 基線",
    )

    if baseline == 0:
        pytest.skip("基線無資料，無法驗證日期過濾方向；請確認測試環境有測試活動")

    date_input = EventListPage.date_input(page)

    # PrimeVue DatePicker fill 完不會自動 commit v-model 也不會關 overlay；
    # press("Enter") 觸發 change 並收 overlay，apply 按鈕才會 enable 且不被遮擋
    date_input.fill("2099-12-31")
    date_input.press("Enter")
    page.wait_for_timeout(500)
    EventListPage.apply_button(page).click()
    page.wait_for_timeout(1500)
    far_future = rows.count()

    EventListPage.reset_button(page).click()
    page.wait_for_timeout(1500)

    date_input.fill("2000-01-01")
    date_input.press("Enter")
    page.wait_for_timeout(500)
    EventListPage.apply_button(page).click()
    page.wait_for_timeout(1500)
    far_past = rows.count()

    report_attach(
        actual=f"基線 {baseline} 列；遠未來 {far_future} 列；遠過去 {far_past} 列"
    )

    assert far_future <= baseline, (
        f"遠未來日期（2099-12-31）過濾後列數 {far_future} > 基線 {baseline}；"
        f"StartTimeGe 過濾失效或方向相反"
    )
    assert far_past == baseline, (
        f"遠過去日期（2000-01-01）過濾後列數 {far_past} ≠ 基線 {baseline}；"
        f"理應所有活動 start_time ≥ 2000-01-01 全部顯示"
    )


def _filter_by_date_format(page: Page, fmt_value: str) -> tuple[int, int]:
    """以 fmt_value 套遠未來日期過濾，回傳 (baseline, far_future)。
    嚴格用法：呼叫端應 assert far_future < baseline，不允許 == baseline 的「無過濾」結果。
    """
    rows = EventListPage.list_rows(page)
    page.wait_for_timeout(1500)
    baseline = rows.count()

    date_input = EventListPage.date_input(page)
    date_input.fill(fmt_value)
    date_input.press("Enter")
    page.wait_for_timeout(500)
    EventListPage.apply_button(page).click()
    page.wait_for_timeout(1500)
    far_future = rows.count()
    return baseline, far_future


def test_AC8_日期格式_slash(page: Page, config, report_attach):
    """AC8：活動日期欄位應接受 `yyyy/mm/dd` 格式（嚴格驗證有過濾發生）。

    與 AC5 差異：AC5 用 `<=` 寬鬆斷言，會把「格式被忽略 → 列數不變」誤判為 PASS。
    本案改 `<` 嚴格斷言，遠未來日期套用後列數必須 < 基線。
    """
    _shared.open_event_list(page, config["base_url"])
    baseline, far_future = _filter_by_date_format(page, "2099/12/31")
    report_attach(
        url=page.url,
        expected="基線 > far_future（slash 格式被接受並過濾掉所有 start_time < 2099 的列）",
        actual=f"基線 {baseline}；slash 遠未來 {far_future}",
    )
    if baseline == 0:
        pytest.skip("基線無資料，無法驗證日期過濾方向")
    assert far_future < baseline, (
        f"slash（yyyy/mm/dd）格式應被接受並嚴格過濾，但 {far_future} >= 基線 {baseline}；"
        f"可能格式被忽略或 v-model 未更新"
    )


@pytest.mark.xfail(
    reason="2026-05-07 確認：前端目前僅支援 yyyy/mm/dd，- 待支援；前端修完後此案 XPASS 即可解 xfail",
    strict=False,
)
def test_AC8_日期格式_dash(page: Page, config, report_attach):
    """AC8：活動日期欄位應接受 `yyyy-mm-dd` 格式（與 slash 同行為）。

    目前已知前端只接受 `/`，本案 xfail(strict=False) 預期為 XFAIL；
    若前端修完支援 `-`，本案 XPASS 即訊號告訴我們可以解 xfail。
    """
    _shared.open_event_list(page, config["base_url"])
    baseline, far_future = _filter_by_date_format(page, "2099-12-31")
    report_attach(
        url=page.url,
        expected="基線 > far_future（dash 格式被接受並過濾掉所有 start_time < 2099 的列）",
        actual=f"基線 {baseline}；dash 遠未來 {far_future}",
    )
    if baseline == 0:
        pytest.skip("基線無資料，無法驗證日期過濾方向")
    assert far_future < baseline, (
        f"dash（yyyy-mm-dd）格式應被接受並嚴格過濾，但 {far_future} >= 基線 {baseline}；"
        f"前端目前僅支援 yyyy/mm/dd（已知 xfail）"
    )
