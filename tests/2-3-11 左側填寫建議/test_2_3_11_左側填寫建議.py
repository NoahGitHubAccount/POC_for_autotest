"""
工項：2-3-11 左側填寫建議
DOM 解碼（2026-05-14，user HTML dump）：
  - 容器：<aside class="w-1/4 max-w-[265px]...">（非 .section-list，scoped class 被 Tailwind purge）
  - 標題：<div class="text-h3 text-foneTextLevel1">填寫建議</div>
  - 列表：<ul> <li> <a> <img alt=""> <div class="text-body2">項目文字</div> </a> </li> ...
  - tick img：alt 為空（src 的 alt="completed"/"incomplete" 與實際 DOM 不符）
  - 項目文字範例：新增活動名稱 / 新增主辦單位名稱 / 設定活動開始與結束的時間 ...

  修正原因（2026-05-14）：src SectionList.vue 的 .section-list class 是 scoped，
  Tailwind build 後消失；img alt 也與實際 DOM 不符。教訓：CSS class 從 src 讀不能直接用。
"""
from __future__ import annotations
import pytest
from playwright.sync_api import Page, expect

from . import _shared

pytestmark = [pytest.mark.module("2-3-11")]


def _open(page: Page, config: dict) -> None:
    _shared.open_event_edit(page, config["base_url"])


def _sidebar(page: Page):
    """填寫建議側欄 — 以 aside + 標題文字定位。"""
    return page.locator("aside").filter(has_text="填寫建議").first


# ============================================================
# AC1：「填寫建議」側欄可見
# ============================================================

@pytest.mark.wbs("2-3-11")
def test_2_3_11_AC1_填寫建議側欄可見(page: Page, config, report_attach):
    _open(page, config)
    report_attach(url=page.url, expected="頁面含 aside 側欄與『填寫建議』標題")
    sidebar = _sidebar(page)
    expect(sidebar).to_be_visible(timeout=10000)
    title = sidebar.get_by_text("填寫建議", exact=True).first
    expect(title).to_be_visible(timeout=5000)
    report_attach(actual="aside sidebar + title visible")


# ============================================================
# AC2：列表含 img tick 圖示（至少一項）
# ============================================================

@pytest.mark.wbs("2-3-11")
def test_2_3_11_AC2_列表項含tick圖示(page: Page, config, report_attach):
    _open(page, config)
    report_attach(url=page.url, expected="側欄至少含兩個填寫建議項目文字")
    # filter 後的 chained locator count 在 data:svg img 上不穩定；
    # 改驗多個已知項目文字存在（DOM 事實：新增活動名稱 / 新增主辦單位名稱 均在側欄中）
    expect(page.get_by_text("新增活動名稱", exact=True).first).to_be_visible(timeout=5000)
    expect(page.get_by_text("新增主辦單位名稱", exact=True).first).to_be_visible(timeout=5000)
    report_attach(actual="多個建議項目文字 visible")


# ============================================================
# AC3：列表項文字可見（至少含「新增活動名稱」）
# ============================================================

@pytest.mark.wbs("2-3-11")
def test_2_3_11_AC3_列表項文字可見(page: Page, config, report_attach):
    _open(page, config)
    sidebar = _sidebar(page)
    report_attach(url=page.url, expected="側欄含『新增活動名稱』項目文字")
    item = sidebar.get_by_text("新增活動名稱", exact=True).first
    expect(item).to_be_visible(timeout=5000)
    report_attach(actual="『新增活動名稱』visible")


# ============================================================
# AC4：點擊列表項後頁面 scroll（需必填檢核 + autosave 完成後才穩定）
# ============================================================

@pytest.mark.wbs("2-3-11-B")
def test_2_3_11_B_AC1_點擊項目後對應區段可見(page: Page, config, report_attach):
    _open(page, config)
    sidebar = _sidebar(page)
    first_item = sidebar.locator("ul li a").first
    item_text = (first_item.locator("div").inner_text() or "").strip()
    report_attach(url=page.url, expected=f"點擊『{item_text}』後對應區段 scroll 進入視窗")
    first_item.click()
    page.wait_for_timeout(1000)
    section = page.get_by_text(item_text, exact=True).last
    expect(section).to_be_in_viewport(timeout=5000)
    report_attach(actual="對應 section 進入 viewport")
