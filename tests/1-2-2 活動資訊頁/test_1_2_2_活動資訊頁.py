"""
工項：1-2-2 活動資訊頁（主視覺圖片載入）
src 解碼（2026-05-14，ActivityInfo.vue）：
- URL：/ActivityInfo?evMainEventId=<mainId>&evEventId=<eventId>（場次 ID）
- banner img：<img :src="bannerImageUrl" alt="" @load="imageLoaded = true">
- 載入前 opacity-0 → 載入後 opacity-100
- imageLoaded 狀態由 fileSvc.getImageByResourceId(fileResourceId) API 決定

前置條件：config["activity_info_url"] 需設定含 query params 的完整 URL。
若未設定，所有測試標記 xfail（不影響其他工項統計）。
"""
from __future__ import annotations
import pytest
from playwright.sync_api import Page, expect

from lib.selectors import ActivityInfoPage

from . import _shared

pytestmark = [pytest.mark.module("1-2-2")]

_SKIP_REASON = "config 缺少 activity_info_url（需填入含 evMainEventId/evEventId 的完整 URL）"


# ============================================================
# AC1：活動資訊頁可開啟、有 banner 圖片區
# ============================================================

@pytest.mark.wbs("1-2-2")
def test_1_2_2_AC1_頁面可開啟並有banner圖片元素(page: Page, config, report_attach):
    if not _shared.open_activity_info(page, config):
        pytest.xfail(_SKIP_REASON)
    report_attach(url=page.url, expected="頁面含 banner img 元素")
    img = ActivityInfoPage.banner_img(page)
    img.wait_for(state="attached", timeout=10000)
    report_attach(actual="banner img 元素存在於 DOM")


# ============================================================
# AC2：banner 圖片 src 非空（API 有回傳圖片 URL）
# ============================================================

@pytest.mark.wbs("1-2-2")
def test_1_2_2_AC2_banner圖片src不為空(page: Page, config, report_attach):
    if not _shared.open_activity_info(page, config):
        pytest.xfail(_SKIP_REASON)
    page.wait_for_timeout(3000)  # 等 API 回傳
    report_attach(url=page.url, expected="banner img src 非空（API 回傳圖片 blob URL）")
    img = ActivityInfoPage.banner_img(page)
    src = img.get_attribute("src") or ""
    report_attach(actual=f"img src：{src[:80]}…" if len(src) > 80 else f"img src：{src}")
    assert src, "banner img src 為空，API 未回傳圖片"


# ============================================================
# AC3：圖片載入完成（opacity-100）
# ============================================================

@pytest.mark.wbs("1-2-2")
def test_1_2_2_AC3_banner圖片載入完成(page: Page, config, report_attach):
    if not _shared.open_activity_info(page, config):
        pytest.xfail(_SKIP_REASON)
    page.wait_for_timeout(5000)  # 等圖片 @load 事件觸發
    report_attach(url=page.url, expected="banner img 有 opacity-100 class（imageLoaded=true）")
    loaded_img = ActivityInfoPage.banner_loaded(page)
    expect(loaded_img).to_be_visible(timeout=10000)
    report_attach(actual="banner img opacity-100 visible")
