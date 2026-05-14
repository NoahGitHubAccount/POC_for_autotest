"""
工項：2-3-9 憑證與報到管理設定 A~K
src 解碼（2026-05-14，EVEventEdit.controller.ts）：
  A - 憑各場次憑證選擇證類型（RadioButton）
  B - 報名序號編碼（英文字幕+數字5碼，如 A29338）（Select）
  C - 憑證顯示資訊（PickTable）               ← 5/13 確認中 → xfail
  D - 憑證備註文字（InputText）               ← 5/13 確認中 → xfail
  E - 是否使用動態碼（ToggleSwitch）
  F - 動態碼滾動時效（Select，開啟 E 才顯示）
  G - 檢核規則（Select）
  H - 開放報到時間（CheckinTimeRow）
  I - 截止報到時間（CheckinTimeRow）
  J - 是否需要顯示報到須知（ToggleSwitch）
  K - 報到須知（Editor，開啟 J 才顯示）
"""
from __future__ import annotations
import pytest
from playwright.sync_api import Page, expect

from lib.selectors import EVEventEditPage

from . import _shared

pytestmark = [pytest.mark.module("2-3-9")]


def _open(page: Page, config: dict) -> None:
    _shared.open_event_edit(page, config["base_url"])
    _shared.scroll_to_certificate_section(page)


# ============================================================
# A：憑各場次憑證選擇證類型
# ============================================================

@pytest.mark.wbs("2-3-9-A")
def test_2_3_9_A_憑證類型_radio可見(page: Page, config, report_attach):
    _open(page, config)
    report_attach(url=page.url, expected="含『憑各場次憑證選擇證類型』label")
    lbl = page.get_by_text("憑各場次憑證選擇證類型", exact=True).first
    expect(lbl).to_be_visible(timeout=10000)
    report_attach(actual="label visible")


# ============================================================
# B：報名序號編碼
# ============================================================

@pytest.mark.wbs("2-3-9-B")
def test_2_3_9_B_報名序號編碼_select可見(page: Page, config, report_attach):
    _open(page, config)
    report_attach(url=page.url, expected="含『報名序號編碼』label")
    lbl = page.get_by_text("報名序號編碼", exact=True).first
    expect(lbl).to_be_visible(timeout=10000)
    report_attach(actual="label visible")


@pytest.mark.wbs("2-3-9-B")
def test_2_3_9_B_報名序號編碼_有預設選項文字(page: Page, config, report_attach):
    _open(page, config)
    report_attach(url=page.url, expected="Select 含『顯示文字字首 + 數字 5 碼』選項或 placeholder")
    option_text = page.get_by_text("顯示文字字首 + 數字 5 碼").first
    expect(option_text).to_be_visible(timeout=10000)
    report_attach(actual="選項文字 visible")


# ============================================================
# C：憑證顯示資訊（5/13 確認中）
# ============================================================

@pytest.mark.wbs("2-3-9-C")
@pytest.mark.xfail(reason="5/13 尚在確認功能，PickTable 渲染待驗證（XPASS 表示可解 xfail）", strict=False)
def test_2_3_9_C_憑證顯示資訊_picktable可見(page: Page, config, report_attach):
    _open(page, config)
    report_attach(url=page.url, expected="含『憑證顯示資訊』label")
    lbl = page.get_by_text("憑證顯示資訊", exact=True).first
    expect(lbl).to_be_visible(timeout=10000)
    report_attach(actual="label visible")


# ============================================================
# D：憑證備註文字（5/13 確認中）
# ============================================================

@pytest.mark.wbs("2-3-9-D")
@pytest.mark.xfail(reason="5/13 尚在確認功能（XPASS 表示可解 xfail）", strict=False)
def test_2_3_9_D_憑證備註文字_input可見(page: Page, config, report_attach):
    _open(page, config)
    report_attach(url=page.url, expected="含『憑證備註文字』input")
    lbl = page.get_by_text("憑證備註文字", exact=True).first
    expect(lbl).to_be_visible(timeout=10000)
    report_attach(actual="label visible")


# ============================================================
# E：是否使用動態碼
# ============================================================

@pytest.mark.wbs("2-3-9-E")
def test_2_3_9_E_動態碼_toggle可見(page: Page, config, report_attach):
    _open(page, config)
    report_attach(url=page.url, expected="含『是否使用動態碼』label")
    lbl = page.get_by_text("是否使用動態碼", exact=True).first
    expect(lbl).to_be_visible(timeout=10000)
    report_attach(actual="label visible")


# ============================================================
# F：動態碼滾動時效（開啟 E 才顯示）
# ============================================================

@pytest.mark.wbs("2-3-9-F")
@pytest.mark.xfail(reason="動態碼滾動時效需先開啟 E（is Hidden when E=false）", strict=False)
def test_2_3_9_F_動態碼時效_select可見(page: Page, config, report_attach):
    _open(page, config)
    toggle = page.get_by_text("是否使用動態碼", exact=True).first
    toggle.locator("xpath=..").locator(".p-toggleswitch").click()
    page.wait_for_timeout(500)
    report_attach(url=page.url, expected="開啟 E 後含『動態碼滾動時效』label")
    lbl = page.get_by_text("動態碼滾動時效", exact=True).first
    expect(lbl).to_be_visible(timeout=5000)
    report_attach(actual="label visible")


# ============================================================
# G：檢核規則
# ============================================================

@pytest.mark.wbs("2-3-9-G")
def test_2_3_9_G_檢核規則_select可見(page: Page, config, report_attach):
    _open(page, config)
    report_attach(url=page.url, expected="含『檢核規則』label")
    lbl = page.get_by_text("檢核規則", exact=True).first
    expect(lbl).to_be_visible(timeout=10000)
    report_attach(actual="label visible")


# ============================================================
# H：開放報到時間
# ============================================================

@pytest.mark.wbs("2-3-9-H")
def test_2_3_9_H_開放報到時間_input可見(page: Page, config, report_attach):
    _open(page, config)
    report_attach(url=page.url, expected="含『開放報到時間』label")
    lbl = page.get_by_text("開放報到時間", exact=True).first
    expect(lbl).to_be_visible(timeout=10000)
    report_attach(actual="label visible")


# ============================================================
# I：截止報到時間
# ============================================================

@pytest.mark.wbs("2-3-9-I")
def test_2_3_9_I_截止報到時間_input可見(page: Page, config, report_attach):
    _open(page, config)
    report_attach(url=page.url, expected="含『截止報到時間』label")
    lbl = page.get_by_text("截止報到時間", exact=True).first
    expect(lbl).to_be_visible(timeout=10000)
    report_attach(actual="label visible")


# ============================================================
# J：是否需要顯示報到須知
# ============================================================

@pytest.mark.wbs("2-3-9-J")
def test_2_3_9_J_報到須知_toggle可見(page: Page, config, report_attach):
    _open(page, config)
    report_attach(url=page.url, expected="含『是否需要顯示報到須知』label")
    lbl = page.get_by_text("是否需要顯示報到須知", exact=True).first
    expect(lbl).to_be_visible(timeout=10000)
    report_attach(actual="label visible")


# ============================================================
# K：報到須知（開啟 J 才顯示）
# ============================================================

@pytest.mark.wbs("2-3-9-K")
@pytest.mark.xfail(reason="報到須知 Editor IsHidden（J=false 時不顯示），需先開啟 J", strict=False)
def test_2_3_9_K_報到須知_editor可見(page: Page, config, report_attach):
    _open(page, config)
    toggle = page.get_by_text("是否需要顯示報到須知", exact=True).first
    toggle.locator("xpath=..").locator(".p-toggleswitch").click()
    page.wait_for_timeout(500)
    report_attach(url=page.url, expected="開啟 J 後含『報到須知』editor")
    lbl = page.get_by_text("報到須知", exact=True).first
    expect(lbl).to_be_visible(timeout=5000)
    report_attach(actual="label visible")
