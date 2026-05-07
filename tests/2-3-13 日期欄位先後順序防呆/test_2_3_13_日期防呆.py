"""
工項：2-3-13 各時間欄位先後順序防呆（5 群組 14 條規則；group 6 場次 → 2-3-2）
規格：specs/2-3-13 日期欄位先後順序防呆/

實作狀態（src 解碼 2026-05-06）：
- EVEventEdit.controller.ts 中所有日期 PageFormItem **沒設** minDate/maxDate/disabledDates
- submit 也無時間順序 validate（只有 fallback 的 `setErrorToast("儲存錯誤")`）
- → 防呆機制**前端未實作**

測試策略：
- 「正向 AC」（合法值不被擋 + DatePicker 存在）→ 可跑
- 「反向 AC」（違反規則時應有防呆）→ 全 SKIP-pending，等前端實作後解 skip
- 等前端決定用哪種防呆機制（minDate/maxDate vs inline error vs save toast），
  反向 AC 的 assert 寫法需依機制調整（目前 assert 預留為「儲存按鈕被擋 / 出現錯誤訊息」二擇一）
"""
from __future__ import annotations
import pytest
from playwright.sync_api import Page, expect

from lib.selectors import EVEventEditPage

from . import _shared

pytestmark = [pytest.mark.module("2-3-13")]


# ============================================================
# G1 活動開始/結束時間
# ============================================================

@pytest.mark.wbs("2-3-13-G1")
def test_2_3_13_G1_AC1_DatePicker存在(page: Page, config, report_attach):
    _shared.open_first_event_edit(page, config["base_url"])
    expect(EVEventEditPage.start_time_input(page)).to_be_visible(timeout=10000)
    expect(EVEventEditPage.end_time_input(page)).to_be_visible(timeout=10000)
    report_attach(url=page.url, actual="活動開始 / 結束時間 DatePicker 皆 visible")


@pytest.mark.wbs("2-3-13-G1")
def test_2_3_13_G1_AC2_合法值被接受(page: Page, config, report_attach):
    """正向：開始 < 結束。應接受。"""
    _shared.open_first_event_edit(page, config["base_url"])
    _shared.fill_datepicker(page, "活動開始時間", "2026-06-01 / 09:00")
    _shared.fill_datepicker(page, "活動結束時間", "2026-06-02 / 18:00")
    page.wait_for_timeout(500)
    # 簡易斷言：填完後沒有彈出錯誤訊息（toast）
    err = page.locator(".p-toast-message-error, .p-message-error")
    report_attach(url=page.url, expected="無錯誤訊息出現")
    assert err.count() == 0, "出現非預期錯誤訊息"


@pytest.mark.wbs("2-3-13-G1")
def test_2_3_13_G1_AC4_日期格式_slash_接受(page: Page, config, report_attach):
    """AC4 (slash)：DatePicker 應接受 `yyyy/mm/dd / HH:mm` 格式。

    驗法：fill 後 press Enter，讀回 input value。若 v-model parse 成功，
    input value 會顯示已 parse 後的日期（含 2026 年份）；若 parse 失敗，
    PrimeVue 會把 input 清空或 revert，斷言則會抓到。
    """
    _shared.open_first_event_edit(page, config["base_url"])
    inp = EVEventEditPage.start_time_input(page)
    inp.fill("2026/06/01 / 09:00")
    inp.press("Enter")
    page.wait_for_timeout(500)
    val = inp.input_value()
    report_attach(url=page.url, expected="input value 含 '2026'", actual=f"input value={val!r}")
    assert "2026" in val, f"slash 格式應被接受，但 input value={val!r}（可能被清空 / parse 失敗）"


@pytest.mark.wbs("2-3-13-G1")
@pytest.mark.xfail(
    reason="2026-05-07 確認：前端目前僅支援 yyyy/mm/dd，- 待支援；前端修完後 XPASS 即可解 xfail",
    strict=False,
)
def test_2_3_13_G1_AC4_日期格式_dash_接受(page: Page, config, report_attach):
    """AC4 (dash)：DatePicker 應接受 `yyyy-mm-dd / HH:mm` 格式。

    目前已知 dash 不支援，本案 xfail(strict=False)。前端修完支援 `-` 後 XPASS 即解 xfail。
    """
    _shared.open_first_event_edit(page, config["base_url"])
    inp = EVEventEditPage.start_time_input(page)
    inp.fill("2026-06-01 / 09:00")
    inp.press("Enter")
    page.wait_for_timeout(500)
    val = inp.input_value()
    report_attach(url=page.url, expected="input value 含 '2026'", actual=f"input value={val!r}")
    assert "2026" in val, f"dash 格式應被接受，但 input value={val!r}（前端目前僅支援 /）"


@pytest.mark.wbs("2-3-13-G1")
@pytest.mark.xfail(reason="依舊版 src 推測前端未實作防呆；新版測試機可能已實作（XPASS 表示可解 xfail）", strict=False)
def test_2_3_13_G1_AC3_反向_開始大於結束應被擋(page: Page, config, report_attach):
    _shared.open_first_event_edit(page, config["base_url"])
    _shared.fill_datepicker(page, "活動開始時間", "2026-06-02 / 09:00")
    _shared.fill_datepicker(page, "活動結束時間", "2026-06-01 / 18:00")
    EVEventEditPage.save_button(page).click()
    page.wait_for_timeout(1000)
    err = page.locator(".p-toast-message-error, .p-message-error, .p-invalid")
    assert err.count() > 0, "違反先後順序但無防呆"


# ============================================================
# G2 活動曝光時間（3 條規則）
# ============================================================

@pytest.mark.wbs("2-3-13-G2")
def test_2_3_13_G2_AC1_DatePicker存在(page: Page, config, report_attach):
    _shared.open_first_event_edit(page, config["base_url"])
    expect(EVEventEditPage.date_input_by_label(page, "活動曝光時間")).to_be_visible(timeout=10000)
    expect(EVEventEditPage.date_input_by_label(page, "活動曝光結束時間")).to_be_visible(timeout=10000)


@pytest.mark.wbs("2-3-13-G2")
@pytest.mark.xfail(reason="依舊版 src 推測前端未實作防呆；新版測試機可能已實作（XPASS 表示可解 xfail）", strict=False)
def test_2_3_13_G2_AC3_反向a_曝光開始晚於活動開始(page: Page, config, report_attach):
    _shared.open_first_event_edit(page, config["base_url"])
    _shared.fill_datepicker(page, "活動開始時間", "2026-06-01 / 09:00")
    _shared.fill_datepicker(page, "活動曝光時間", "2026-06-05 / 09:00")
    EVEventEditPage.save_button(page).click()
    page.wait_for_timeout(1000)
    assert page.locator(".p-toast-message-error, .p-message-error, .p-invalid").count() > 0


@pytest.mark.wbs("2-3-13-G2")
@pytest.mark.xfail(reason="依舊版 src 推測前端未實作防呆；新版測試機可能已實作（XPASS 表示可解 xfail）", strict=False)
def test_2_3_13_G2_AC4_反向b_曝光結束早於活動結束(page: Page, config, report_attach):
    _shared.open_first_event_edit(page, config["base_url"])
    _shared.fill_datepicker(page, "活動結束時間", "2026-06-15 / 18:00")
    _shared.fill_datepicker(page, "活動曝光結束時間", "2026-06-10 / 18:00")
    EVEventEditPage.save_button(page).click()
    page.wait_for_timeout(1000)
    assert page.locator(".p-toast-message-error, .p-message-error, .p-invalid").count() > 0


@pytest.mark.wbs("2-3-13-G2")
@pytest.mark.xfail(reason="依舊版 src 推測前端未實作防呆；新版測試機可能已實作（XPASS 表示可解 xfail）", strict=False)
def test_2_3_13_G2_AC5_反向c_曝光開始晚於曝光結束(page: Page, config, report_attach):
    _shared.open_first_event_edit(page, config["base_url"])
    _shared.fill_datepicker(page, "活動曝光時間", "2026-06-10 / 09:00")
    _shared.fill_datepicker(page, "活動曝光結束時間", "2026-06-05 / 18:00")
    EVEventEditPage.save_button(page).click()
    page.wait_for_timeout(1000)
    assert page.locator(".p-toast-message-error, .p-message-error, .p-invalid").count() > 0


# ============================================================
# G3 活動報名時間（4 條規則）
# ============================================================

@pytest.mark.wbs("2-3-13-G3")
def test_2_3_13_G3_AC1_DatePicker存在(page: Page, config, report_attach):
    _shared.open_first_event_edit(page, config["base_url"])
    expect(EVEventEditPage.date_input_by_label(page, "開放報名時間")).to_be_visible(timeout=10000)
    expect(EVEventEditPage.date_input_by_label(page, "截止報名時間")).to_be_visible(timeout=10000)


@pytest.mark.wbs("2-3-13-G3")
@pytest.mark.xfail(reason="依舊版 src 推測前端未實作防呆；新版測試機可能已實作（XPASS 表示可解 xfail）", strict=False)
def test_2_3_13_G3_AC3_反向a_開放早於曝光開始(page: Page, config, report_attach):
    _shared.open_first_event_edit(page, config["base_url"])
    _shared.fill_datepicker(page, "活動曝光時間", "2026-05-25 / 00:00")
    _shared.fill_datepicker(page, "開放報名時間", "2026-05-20 / 00:00")
    EVEventEditPage.save_button(page).click()
    page.wait_for_timeout(1000)
    assert page.locator(".p-toast-message-error, .p-message-error, .p-invalid").count() > 0


@pytest.mark.wbs("2-3-13-G3")
@pytest.mark.xfail(reason="依舊版 src 推測前端未實作防呆；新版測試機可能已實作（XPASS 表示可解 xfail）", strict=False)
def test_2_3_13_G3_AC4_反向b_開放晚於活動開始(page: Page, config, report_attach):
    _shared.open_first_event_edit(page, config["base_url"])
    _shared.fill_datepicker(page, "活動開始時間", "2026-06-01 / 09:00")
    _shared.fill_datepicker(page, "開放報名時間", "2026-06-05 / 09:00")
    EVEventEditPage.save_button(page).click()
    page.wait_for_timeout(1000)
    assert page.locator(".p-toast-message-error, .p-message-error, .p-invalid").count() > 0


@pytest.mark.wbs("2-3-13-G3")
@pytest.mark.xfail(reason="依舊版 src 推測前端未實作防呆；新版測試機可能已實作（XPASS 表示可解 xfail）", strict=False)
def test_2_3_13_G3_AC5_反向c_截止晚於活動開始(page: Page, config, report_attach):
    _shared.open_first_event_edit(page, config["base_url"])
    _shared.fill_datepicker(page, "活動開始時間", "2026-06-01 / 09:00")
    _shared.fill_datepicker(page, "截止報名時間", "2026-06-05 / 09:00")
    EVEventEditPage.save_button(page).click()
    page.wait_for_timeout(1000)
    assert page.locator(".p-toast-message-error, .p-message-error, .p-invalid").count() > 0


@pytest.mark.wbs("2-3-13-G3")
@pytest.mark.xfail(reason="依舊版 src 推測前端未實作防呆；新版測試機可能已實作（XPASS 表示可解 xfail）", strict=False)
def test_2_3_13_G3_AC6_反向d_開放晚於截止(page: Page, config, report_attach):
    _shared.open_first_event_edit(page, config["base_url"])
    _shared.fill_datepicker(page, "開放報名時間", "2026-06-01 / 09:00")
    _shared.fill_datepicker(page, "截止報名時間", "2026-05-30 / 09:00")
    EVEventEditPage.save_button(page).click()
    page.wait_for_timeout(1000)
    assert page.locator(".p-toast-message-error, .p-message-error, .p-invalid").count() > 0


# ============================================================
# G4 截止修改時間（2 條規則）
# ============================================================

@pytest.mark.wbs("2-3-13-G4")
@pytest.mark.xfail(reason="舊版 src 中 Field label 待釐清且未實作防呆；新版測試機可能已調整（XPASS 表示可解 xfail）", strict=False)
def test_2_3_13_G4_AC1_DatePicker存在(page: Page, config, report_attach):
    _shared.open_first_event_edit(page, config["base_url"])
    expect(EVEventEditPage.date_input_by_label(page, "截止修改時間")).to_be_visible(timeout=10000)


@pytest.mark.wbs("2-3-13-G4")
@pytest.mark.xfail(reason="舊版 src 中 Field label 待釐清且未實作防呆；新版測試機可能已調整（XPASS 表示可解 xfail）", strict=False)
def test_2_3_13_G4_AC3_反向a_截止修改晚於截止報名(page: Page, config, report_attach):
    _shared.open_first_event_edit(page, config["base_url"])
    _shared.fill_datepicker(page, "截止報名時間", "2026-05-30 / 09:00")
    _shared.fill_datepicker(page, "截止修改時間", "2026-06-01 / 09:00")
    EVEventEditPage.save_button(page).click()
    page.wait_for_timeout(1000)
    assert page.locator(".p-toast-message-error, .p-message-error, .p-invalid").count() > 0


@pytest.mark.wbs("2-3-13-G4")
@pytest.mark.xfail(reason="舊版 src 中 Field label 待釐清且未實作防呆；新版測試機可能已調整（XPASS 表示可解 xfail）", strict=False)
def test_2_3_13_G4_AC4_反向b_截止修改晚於活動開始(page: Page, config, report_attach):
    _shared.open_first_event_edit(page, config["base_url"])
    _shared.fill_datepicker(page, "活動開始時間", "2026-06-01 / 09:00")
    _shared.fill_datepicker(page, "截止修改時間", "2026-06-05 / 09:00")
    EVEventEditPage.save_button(page).click()
    page.wait_for_timeout(1000)
    assert page.locator(".p-toast-message-error, .p-message-error, .p-invalid").count() > 0


# ============================================================
# G5 報到時間（4 條規則）
# ============================================================

@pytest.mark.wbs("2-3-13-G5")
@pytest.mark.xfail(reason="舊版 src 中 Field label 待釐清且未實作防呆；新版測試機可能已調整（XPASS 表示可解 xfail）", strict=False)
def test_2_3_13_G5_AC1_DatePicker存在(page: Page, config, report_attach):
    _shared.open_first_event_edit(page, config["base_url"])
    expect(EVEventEditPage.date_input_by_label(page, "開放報到時間")).to_be_visible(timeout=10000)
    expect(EVEventEditPage.date_input_by_label(page, "截止報到時間")).to_be_visible(timeout=10000)


@pytest.mark.wbs("2-3-13-G5")
@pytest.mark.xfail(reason="舊版 src 中 Field label 待釐清且未實作防呆；新版測試機可能已調整（XPASS 表示可解 xfail）", strict=False)
def test_2_3_13_G5_AC3_反向a_開放報到早於截止報名(page: Page, config, report_attach):
    _shared.open_first_event_edit(page, config["base_url"])
    _shared.fill_datepicker(page, "截止報名時間", "2026-05-30 / 09:00")
    _shared.fill_datepicker(page, "開放報到時間", "2026-05-25 / 09:00")
    EVEventEditPage.save_button(page).click()
    page.wait_for_timeout(1000)
    assert page.locator(".p-toast-message-error, .p-message-error, .p-invalid").count() > 0


@pytest.mark.wbs("2-3-13-G5")
@pytest.mark.xfail(reason="舊版 src 中 Field label 待釐清且未實作防呆；新版測試機可能已調整（XPASS 表示可解 xfail）", strict=False)
def test_2_3_13_G5_AC4_反向b_開放報到晚於活動開始(page: Page, config, report_attach):
    _shared.open_first_event_edit(page, config["base_url"])
    _shared.fill_datepicker(page, "活動開始時間", "2026-06-01 / 09:00")
    _shared.fill_datepicker(page, "開放報到時間", "2026-06-05 / 09:00")
    EVEventEditPage.save_button(page).click()
    page.wait_for_timeout(1000)
    assert page.locator(".p-toast-message-error, .p-message-error, .p-invalid").count() > 0


@pytest.mark.wbs("2-3-13-G5")
@pytest.mark.xfail(reason="舊版 src 中 Field label 待釐清且未實作防呆；新版測試機可能已調整（XPASS 表示可解 xfail）", strict=False)
def test_2_3_13_G5_AC5_反向c_截止報到早於開放報到(page: Page, config, report_attach):
    _shared.open_first_event_edit(page, config["base_url"])
    _shared.fill_datepicker(page, "開放報到時間", "2026-06-01 / 09:00")
    _shared.fill_datepicker(page, "截止報到時間", "2026-05-30 / 09:00")
    EVEventEditPage.save_button(page).click()
    page.wait_for_timeout(1000)
    assert page.locator(".p-toast-message-error, .p-message-error, .p-invalid").count() > 0


@pytest.mark.wbs("2-3-13-G5")
@pytest.mark.xfail(reason="舊版 src 中 Field label 待釐清且未實作防呆；新版測試機可能已調整（XPASS 表示可解 xfail）", strict=False)
def test_2_3_13_G5_AC6_反向d_截止報到晚於活動結束(page: Page, config, report_attach):
    _shared.open_first_event_edit(page, config["base_url"])
    _shared.fill_datepicker(page, "活動結束時間", "2026-06-15 / 18:00")
    _shared.fill_datepicker(page, "截止報到時間", "2026-06-20 / 18:00")
    EVEventEditPage.save_button(page).click()
    page.wait_for_timeout(1000)
    assert page.locator(".p-toast-message-error, .p-message-error, .p-invalid").count() > 0
