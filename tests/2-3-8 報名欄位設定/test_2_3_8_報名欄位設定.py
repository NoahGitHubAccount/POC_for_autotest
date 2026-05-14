"""
工項：2-3-8 報名欄位設定 A~L
src 解碼（2026-05-14，EVEventEdit.controller.ts）：

報名者 Panel（A~D）：
  A - 報名者是否預設帶入數位市民個資（ToggleSwitch，預設 true）
  B - 報名者需完成數位市民身分註記驗證（Select，disabled 初始值「不需要」）
  C - 報名者欄位（PickTable）
  D - 報名者參與狀態（RadioButton）

陪伴者 Panel（E~G）：
  E - 是否需要陪伴者（ToggleSwitch，預設 false）
  F - 陪伴者顯示名稱（InputText，開啟 E 才顯示）
  G - 陪伴者欄位（PickTable，開啟 E 才顯示）

參與人 Panel（H~L）：
  H - 參與人數限制（InputNumber）
  I - 是否需要填寫參與人資料（ToggleSwitch）
  J - 參與者欄位（PickTable，開啟 I 才顯示）
  L - 是否需要同意條款（ToggleSwitch）
  M - 同意條款說明（Editor，開啟 L 才顯示）
"""
from __future__ import annotations
import pytest
from playwright.sync_api import Page, expect

from lib.selectors import EVEventEditPage

from . import _shared

pytestmark = [pytest.mark.module("2-3-8")]


def _open(page: Page, config: dict) -> None:
    _shared.open_event_edit(page, config["base_url"])
    # 滾動到報名欄位設定區段
    section = page.get_by_text("報名欄位設定", exact=True).first
    section.scroll_into_view_if_needed(timeout=10000)
    page.wait_for_timeout(500)


# ============================================================
# 報名者 Panel
# ============================================================

@pytest.mark.wbs("2-3-8-A")
def test_2_3_8_A_預設帶入個資_toggle可見(page: Page, config, report_attach):
    _open(page, config)
    report_attach(url=page.url, expected="含『報名者是否預設帶入數位市民個資』label")
    lbl = page.get_by_text("報名者是否預設帶入數位市民個資", exact=True).first
    expect(lbl).to_be_visible(timeout=10000)
    report_attach(actual="label visible")


@pytest.mark.wbs("2-3-8-B")
def test_2_3_8_B_身分註記驗證_select可見(page: Page, config, report_attach):
    _open(page, config)
    report_attach(url=page.url, expected="含『報名者需完成數位市民身分註記驗證』label")
    lbl = page.get_by_text("報名者需完成數位市民身分註記驗證", exact=True).first
    expect(lbl).to_be_visible(timeout=10000)
    report_attach(actual="label visible")


@pytest.mark.wbs("2-3-8-C")
def test_2_3_8_C_報名者欄位_picktable可見(page: Page, config, report_attach):
    _open(page, config)
    report_attach(url=page.url, expected="含『報名者欄位』label")
    lbl = page.get_by_text("報名者欄位", exact=True).first
    expect(lbl).to_be_visible(timeout=10000)
    report_attach(actual="label visible")


@pytest.mark.wbs("2-3-8-D")
def test_2_3_8_D_報名者參與狀態_radio可見(page: Page, config, report_attach):
    _open(page, config)
    report_attach(url=page.url, expected="含『報名者參與狀態』label")
    lbl = page.get_by_text("報名者參與狀態", exact=True).first
    expect(lbl).to_be_visible(timeout=10000)
    report_attach(actual="label visible")


# ============================================================
# 陪伴者 Panel
# ============================================================

@pytest.mark.wbs("2-3-8-E")
def test_2_3_8_E_是否需要陪伴者_toggle可見(page: Page, config, report_attach):
    _open(page, config)
    report_attach(url=page.url, expected="含『是否需要陪伴者』label")
    lbl = page.get_by_text("是否需要陪伴者", exact=True).first
    expect(lbl).to_be_visible(timeout=10000)
    report_attach(actual="label visible")


@pytest.mark.wbs("2-3-8-F")
@pytest.mark.xfail(reason="陪伴者顯示名稱 IsHidden 預設（E=false 時不顯示），需先開啟 E", strict=False)
def test_2_3_8_F_陪伴者顯示名稱_input可見(page: Page, config, report_attach):
    _open(page, config)
    # 先開啟「是否需要陪伴者」toggle
    toggle = page.get_by_text("是否需要陪伴者", exact=True).first
    toggle.locator("xpath=..").locator(".p-toggleswitch").click()
    page.wait_for_timeout(500)
    report_attach(url=page.url, expected="開啟 E 後含『陪伴者顯示名稱』input")
    lbl = page.get_by_text("陪伴者顯示名稱", exact=True).first
    expect(lbl).to_be_visible(timeout=5000)
    report_attach(actual="label visible")


@pytest.mark.wbs("2-3-8-G")
@pytest.mark.xfail(reason="陪伴者欄位 PickTable IsHidden 預設（E=false 時不顯示）", strict=False)
def test_2_3_8_G_陪伴者欄位_picktable可見(page: Page, config, report_attach):
    _open(page, config)
    toggle = page.get_by_text("是否需要陪伴者", exact=True).first
    toggle.locator("xpath=..").locator(".p-toggleswitch").click()
    page.wait_for_timeout(500)
    report_attach(url=page.url, expected="開啟 E 後含『陪伴者欄位』label")
    lbl = page.get_by_text("陪伴者欄位", exact=True).first
    expect(lbl).to_be_visible(timeout=5000)
    report_attach(actual="label visible")


# ============================================================
# 參與人 Panel
# ============================================================

@pytest.mark.wbs("2-3-8-H")
def test_2_3_8_H_參與人數限制_input可見(page: Page, config, report_attach):
    _open(page, config)
    report_attach(url=page.url, expected="含『參與人數限制』label")
    lbl = page.get_by_text("參與人數限制", exact=True).first
    expect(lbl).to_be_visible(timeout=10000)
    report_attach(actual="label visible")


@pytest.mark.wbs("2-3-8-I")
def test_2_3_8_I_是否填寫參與人資料_toggle可見(page: Page, config, report_attach):
    _open(page, config)
    report_attach(url=page.url, expected="含『是否需要填寫參與人資料』label")
    lbl = page.get_by_text("是否需要填寫參與人資料", exact=True).first
    expect(lbl).to_be_visible(timeout=10000)
    report_attach(actual="label visible")


@pytest.mark.wbs("2-3-8-J")
@pytest.mark.xfail(reason="參與者欄位 PickTable IsHidden（I=false 時不顯示），需先開啟 I", strict=False)
def test_2_3_8_J_參與者欄位_picktable可見(page: Page, config, report_attach):
    _open(page, config)
    toggle = page.get_by_text("是否需要填寫參與人資料", exact=True).first
    toggle.locator("xpath=..").locator(".p-toggleswitch").click()
    page.wait_for_timeout(500)
    report_attach(url=page.url, expected="開啟 I 後含『參與者欄位』label")
    lbl = page.get_by_text("參與者欄位", exact=True).first
    expect(lbl).to_be_visible(timeout=5000)
    report_attach(actual="label visible")


@pytest.mark.wbs("2-3-8-L")
def test_2_3_8_L_是否需要同意條款_toggle可見(page: Page, config, report_attach):
    _open(page, config)
    report_attach(url=page.url, expected="含『是否需要同意條款』label")
    lbl = page.get_by_text("是否需要同意條款", exact=True).first
    expect(lbl).to_be_visible(timeout=10000)
    report_attach(actual="label visible")


@pytest.mark.wbs("2-3-8-M")
@pytest.mark.xfail(reason="同意條款說明 Editor IsHidden（L=false 時不顯示），需先開啟 L", strict=False)
def test_2_3_8_M_同意條款說明_editor可見(page: Page, config, report_attach):
    _open(page, config)
    toggle = page.get_by_text("是否需要同意條款", exact=True).first
    toggle.locator("xpath=..").locator(".p-toggleswitch").click()
    page.wait_for_timeout(500)
    report_attach(url=page.url, expected="開啟 L 後含『同意條款說明』editor")
    lbl = page.get_by_text("同意條款說明", exact=True).first
    expect(lbl).to_be_visible(timeout=5000)
    report_attach(actual="label visible")
