"""用既有 storageState 開 context，goto /entry/evevent 後立即 dump storage。

目的：在 SPA 做 auth check 跳轉前看 storage 真實內容，確認 storageState 重用是否完整。
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright

from lib.auth import storage_path, DEFAULT_ROLE
from lib.config_loader import load_config


def main() -> int:
    cfg = load_config()
    sp = storage_path(DEFAULT_ROLE)
    if not sp.exists():
        print("無 storageState，先跑 warm-login", file=sys.stderr)
        return 2

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(storage_state=str(sp))
        page = ctx.new_page()

        # 立即 dump（goto 還沒）
        page.goto(cfg["base_url"] + "/entry/evevent", wait_until="commit")
        before = page.evaluate(
            """() => ({
                url: location.href,
                local: Object.fromEntries(Object.entries(localStorage)),
                session: Object.fromEntries(Object.entries(sessionStorage)),
            })"""
        )

        # 等 SPA 處理（可能 redirect）
        page.wait_for_timeout(3000)
        after = page.evaluate(
            """() => ({
                url: location.href,
                local: Object.fromEntries(Object.entries(localStorage)),
                session: Object.fromEntries(Object.entries(sessionStorage)),
            })"""
        )

        out = Path(".tmp_storage_diff.json")
        out.write_text(
            json.dumps({"before": before, "after": after}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"已寫 {out}")
        print(f"\n--- BEFORE (剛 goto) ---")
        print(f"  url={before['url']}")
        print(f"  local keys={list(before['local'].keys())}")
        print(f"  session keys={list(before['session'].keys())}")
        print(f"\n--- AFTER (3s 後) ---")
        print(f"  url={after['url']}")
        print(f"  local keys={list(after['local'].keys())}")
        print(f"  session keys={list(after['session'].keys())}")

        ctx.close()
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
