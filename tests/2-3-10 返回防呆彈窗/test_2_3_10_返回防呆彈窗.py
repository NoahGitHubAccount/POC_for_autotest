"""
工項：2-3-10 返回活動列表按鈕防呆（確認離開彈窗）
src 解碼（2026-05-14，EVEventEdit.vue）：
  setLeaveConfirmHandler 已實作，所有離開行為觸發 confirm.require：
  - header：'是否要離開此頁面'
  - message：'若您選擇離開，本頁的修改內容將不會被儲存。確定要離開嗎？'
  - acceptLabel：'儲存並離開'（primary button）
  - rejectLabel：'取消'（outlined secondary）

  5/7 Golden 備註：目前已實作，但待 autosave 機制確認後可能調整
  → 基本 dialog 測試正常跑；autosave 整合測試 xfail
"""
from __future__ import annotations
import pytest
from playwright.sync_api import Page, expect

from lib.selectors import EventListPage

from . import _shared

pytestmark = [pytest.mark.module("2-3-10")]


def _open(page: Page, config: dict) -> None:
    _shared.open_event_edit(page, config["base_url"])


# ============================================================
# AC1：EVEventEdit 頁有可觸發離開的返回/導航元素
# ============================================================

@pytest.mark.wbs("2-3-10")
def test_2_3_10_AC1_有返回或導航連結(page: Page, config, report_attach):
    _open(page, config)
    report_attach(url=page.url, expected="頁面有『返回』按鈕或 breadcrumb 導航")
    back = (
        page.get_by_role("button", name="返回").or_(
            page.get_by_text("返回活動列表", exact=True)
        ).or_(
            page.get_by_text("活動管理", exact=True)  # breadcrumb
        ).first
    )
    expect(back).to_be_visible(timeout=10000)
    report_attach(actual="返回/導航元素 visible")


# ============================================================
# AC2：點擊離開觸發確認 dialog（header 正確）
# ============================================================

@pytest.mark.wbs("2-3-10")
def test_2_3_10_AC2_離開觸發確認dialog(page: Page, config, report_attach):
    _open(page, config)
    # 先做任意修改讓 dirty state 啟動（若 autosave 未完成可能不 dirty，但 handler 仍應觸發）
    back = (
        page.get_by_role("button", name="返回").or_(
            page.get_by_text("返回活動列表", exact=True)
        ).or_(
            page.get_by_text("活動管理", exact=True)
        ).first
    )
    back.click()
    report_attach(url=page.url, expected="Dialog header『是否要離開此頁面』出現")
    dialog_header = page.get_by_text("是否要離開此頁面", exact=True).first
    expect(dialog_header).to_be_visible(timeout=5000)
    report_attach(actual="Dialog header visible")


# ============================================================
# AC3：Dialog 有「儲存並離開」與「取消」兩個按鈕
# ============================================================

@pytest.mark.wbs("2-3-10")
def test_2_3_10_AC3_dialog有正確按鈕(page: Page, config, report_attach):
    _open(page, config)
    back = (
        page.get_by_role("button", name="返回").or_(
            page.get_by_text("返回活動列表", exact=True)
        ).or_(
            page.get_by_text("活動管理", exact=True)
        ).first
    )
    back.click()
    page.get_by_text("是否要離開此頁面", exact=True).first.wait_for(state="visible", timeout=5000)
    report_attach(url=page.url, expected="Dialog 有『儲存並離開』和『取消』按鈕")
    save_leave = page.get_by_role("button", name="儲存並離開")
    cancel = page.get_by_role("button", name="取消")
    expect(save_leave).to_be_visible(timeout=3000)
    expect(cancel).to_be_visible(timeout=3000)
    report_attach(actual="兩個按鈕均 visible")


# ============================================================
# AC4：點「取消」關閉 dialog 留在編輯頁
# ============================================================

@pytest.mark.wbs("2-3-10")
def test_2_3_10_AC4_點取消關閉dialog留在編輯頁(page: Page, config, report_attach):
    _open(page, config)
    url_before = page.url
    back = (
        page.get_by_role("button", name="返回").or_(
            page.get_by_text("返回活動列表", exact=True)
        ).or_(
            page.get_by_text("活動管理", exact=True)
        ).first
    )
    back.click()
    page.get_by_text("是否要離開此頁面", exact=True).first.wait_for(state="visible", timeout=5000)
    page.get_by_role("button", name="取消").click()
    page.wait_for_timeout(500)
    report_attach(url=page.url, expected=f"點取消後仍在 EVEventEdit 頁：{url_before}")
    assert "EVEventEdit" in page.url, f"點取消後 URL 離開了編輯頁：{page.url}"
    report_attach(actual=f"URL 仍在 EVEventEdit：{page.url}")


# ============================================================
# AC5：點「儲存並離開」後跳回活動列表（autosave 整合，xfail）
# ============================================================

@pytest.mark.wbs("2-3-10")
@pytest.mark.xfail(reason="儲存並離開需 autosave 機制完成後才可完整驗證（5/7 Golden：待 autosave 確認）", strict=False)
def test_2_3_10_AC5_點儲存並離開後回活動列表(page: Page, config, report_attach):
    _open(page, config)
    back = (
        page.get_by_role("button", name="返回").or_(
            page.get_by_text("返回活動列表", exact=True)
        ).or_(
            page.get_by_text("活動管理", exact=True)
        ).first
    )
    back.click()
    page.get_by_text("是否要離開此頁面", exact=True).first.wait_for(state="visible", timeout=5000)
    page.get_by_role("button", name="儲存並離開").click()
    page.wait_for_url(f"**{EventListPage.PATH}**", timeout=15000)
    report_attach(url=page.url, expected="跳回活動列表頁")
    assert EventListPage.PATH in page.url, f"未跳回列表頁：{page.url}"
    report_attach(actual=f"URL：{page.url}")
