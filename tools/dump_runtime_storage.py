"""於登入後 dump 真實的 localStorage / sessionStorage 內容，找出 auth token 真正放在哪。

用法：
    python tools/dump_runtime_storage.py
（會跳互動登入，登入完成後 dump 至 .tmp_runtime_storage.json）
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright

from lib.auth import perform_interactive_login
from lib.config_loader import load_config


def main() -> int:
    cfg = load_config()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        perform_interactive_login(page, cfg, role="admin")

        # 登入完成（已 wait_for_url 到 /entry/evevent）
        # 等 SPA 完成所有 post-login 寫入
        page.wait_for_timeout(3000)

        runtime = page.evaluate(
            """() => ({
                url: location.href,
                local: Object.fromEntries(Object.entries(localStorage)),
                session: Object.fromEntries(Object.entries(sessionStorage)),
            })"""
        )

        out = Path(".tmp_runtime_storage.json")
        out.write_text(json.dumps(runtime, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n已寫入 {out}")
        print(f"URL：{runtime['url']}")
        print(f"localStorage keys: {list(runtime['local'].keys())}")
        print(f"sessionStorage keys: {list(runtime['session'].keys())}")

        ctx.close()
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
