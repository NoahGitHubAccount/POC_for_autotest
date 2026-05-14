"""
工項：2-3-12 右側即時預覽
src 解碼（2026-05-14，PreviewPanel.vue）：
  - Container：.preview-panel
  - 標題：'即時預覽'（<h3>）+ 紫色手機圖示
  - Mobile frame：.border-gray-800.bg-gray-800.rounded-[2.5rem]（模擬手機邊框）
  - 內部：覆蓋圖、活動名稱、主辦單位、時間等即時渲染

  Joan 5/7：
  - 報名表單為 form 樣式（報名人資訊 / 手機號碼 / 報名人姓名）
  - 圖片問題等 Ricky/Max 確認
  - 報名表單需等報名欄位設定完成後才渲染 → xfail
"""
from __future__ import annotations
import pytest
from playwright.sync_api import Page, expect

from . import _shared

pytestmark = [pytest.mark.module("2-3-12")]


def _open(page: Page, config: dict) -> None:
    _shared.open_event_edit(page, config["base_url"])


# ============================================================
# AC1：「即時預覽」panel 可見
# ============================================================

@pytest.mark.wbs("2-3-12")
def test_2_3_12_AC1_即時預覽panel可見(page: Page, config, report_attach):
    _open(page, config)
    report_attach(url=page.url, expected="頁面含 .preview-panel 容器與『即時預覽』標題")
    panel = page.locator(".preview-panel").first
    expect(panel).to_be_visible(timeout=10000)
    title = panel.get_by_text("即時預覽", exact=True).first
    expect(title).to_be_visible(timeout=5000)
    report_attach(actual="panel + title visible")


# ============================================================
# AC2：手機框架（mobile frame）可見
# ============================================================

@pytest.mark.wbs("2-3-12")
def test_2_3_12_AC2_手機框架可見(page: Page, config, report_attach):
    _open(page, config)
    panel = page.locator(".preview-panel").first
    report_attach(url=page.url, expected="預覽 panel 內有模擬手機邊框元素（rounded-[2.5rem]）")
    frame = panel.locator(".rounded-\\[2\\.5rem\\]").first
    expect(frame).to_be_visible(timeout=10000)
    report_attach(actual="手機框架 visible")


# ============================================================
# AC3：預覽內容即時反映填寫（需動態欄位完成，xfail）
# ============================================================

@pytest.mark.wbs("2-3-12-B")
@pytest.mark.xfail(reason="即時反映需報名欄位設定 + 憑證設定完成後才可完整驗證（Joan 5/7）", strict=False)
def test_2_3_12_B_AC1_填寫後預覽即時更新(page: Page, config, report_attach):
    _open(page, config)
    panel = page.locator(".preview-panel").first
    # 找活動名稱欄位，填入測試文字，驗預覽更新
    name_input = page.get_by_label("活動名稱").first
    test_name = "預覽測試活動名稱"
    name_input.fill(test_name)
    page.wait_for_timeout(500)
    report_attach(url=page.url, expected=f"預覽 panel 中出現『{test_name}』")
    preview_text = panel.get_by_text(test_name, exact=True).first
    expect(preview_text).to_be_visible(timeout=5000)
    report_attach(actual="預覽 panel 文字更新")
