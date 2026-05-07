"""探索頁面結構，列出可見的 input placeholders、button texts、role 標記。

使用情境：寫測試前先了解頁面元素，避免盲猜選擇器。

用法：
    python tools/explore_page.py /entry/evevent
    python tools/explore_page.py /entry/evevent --headless
    python tools/explore_page.py /entry/evevent --shot snap.png
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright

from lib.auth import (
    DEFAULT_ROLE,
    has_fresh_session,
    prepare_authenticated_context,
)
from lib.config_loader import load_config


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("path", help="要探索的 path（會接在 base_url 後）")
    p.add_argument("--headless", action="store_true")
    p.add_argument("--shot", help="截圖儲存路徑")
    p.add_argument("--wait-ms", type=int, default=2000, help="等待頁面渲染的時間")
    args = p.parse_args()

    cfg = load_config()
    if not has_fresh_session(DEFAULT_ROLE, cfg["captcha"]["session_max_age_min"]):
        print("無有效 session，請先：python tools/run.py --warm-login", file=sys.stderr)
        return 2

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=args.headless)
        ctx = prepare_authenticated_context(
            browser,
            role=DEFAULT_ROLE,
            viewport=cfg.get("browser", {}).get("viewport", {"width": 1440, "height": 900}),
        )
        page = ctx.new_page()
        url = cfg["base_url"] + args.path
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(args.wait_ms)
        # 若被踢回登入頁，提示但繼續 dump（可協助診斷）
        if "/entry/login" in page.url:
            print(f"[警告] 被導向登入頁，可能是 session 失效或目標 URL 需要更深層的權限。url={page.url}", file=sys.stderr)

        print(f"\n[URL] {page.url}")
        print(f"[標題] {page.title()}\n")

        # placeholders
        print("=== 所有 placeholder ===")
        phs = page.locator("[placeholder]").all()
        seen = set()
        for el in phs:
            try:
                ph = el.get_attribute("placeholder")
            except Exception:
                ph = None
            if ph and ph not in seen:
                seen.add(ph)
                print(f"  '{ph}'")

        # buttons
        print("\n=== 所有 button 文字 ===")
        btns = page.get_by_role("button").all()
        seen = set()
        for el in btns:
            try:
                t = (el.text_content() or "").strip()
            except Exception:
                t = ""
            if t and t not in seen:
                seen.add(t)
                print(f"  '{t}'")

        # data-testid
        print("\n=== 含 data-testid 的元素 ===")
        tids = page.locator("[data-testid]").all()
        seen = set()
        for el in tids:
            try:
                tid = el.get_attribute("data-testid")
            except Exception:
                tid = None
            if tid and tid not in seen:
                seen.add(tid)
                print(f"  '{tid}'")

        # 主要 heading
        print("\n=== heading（h1/h2/h3）===")
        for tag in ("h1", "h2", "h3"):
            for el in page.locator(tag).all():
                try:
                    t = (el.text_content() or "").strip()
                except Exception:
                    t = ""
                if t:
                    print(f"  [{tag}] {t}")

        if args.shot:
            page.screenshot(path=args.shot, full_page=True)
            print(f"\n截圖已存：{args.shot}")

        ctx.close()
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
