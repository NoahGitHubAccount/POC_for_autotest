"""1-2-2 活動資訊頁 共用輔助。

URL 規則（src ActivityInfo.controller.ts）：
    /ActivityInfo?evMainEventId=<mainId>&evEventId=<eventId>
evEventId 為場次 ID（evEvent），不是主活動 ID。
目前測試從 config["activity_info_url"] 取完整 URL（含 query params），
若無此 key 則測試 xfail。
"""
from __future__ import annotations
from playwright.sync_api import Page


def open_activity_info(page: Page, config: dict) -> bool:
    """導航到活動資訊頁。回傳 False 表示 config 缺少 activity_info_url。"""
    url = config.get("activity_info_url", "")
    if not url:
        return False
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    return True
