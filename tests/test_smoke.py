"""冒煙測試：驗證 session 有效並能進到登入後首頁。

執行前請先：python tools/run.py --warm-login
"""
import pytest
from playwright.sync_api import Page

pytestmark = [pytest.mark.smoke]


def test_session_active_can_reach_post_login(page: Page, config, authenticated):
    """有 session 時應能直接進到登入後首頁，且不被踢回登入頁。

    等 SPA 完成 auth check 後再驗證 URL，避免時序假陽性。
    """
    target = config["base_url"] + "/entry/evevent"
    page.goto(target, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    assert "/entry/login" not in page.url, (
        f"session 失效，被踢回登入頁：{page.url}\n"
        f"請檢查 .auth/admin.session.json 是否包含 auth token，"
        f"且 conftest 的 _restore_session_storage 有正常注入。"
    )
