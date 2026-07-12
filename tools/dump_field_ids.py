"""列出新增活動頁所有 data-field-id，找出 place/publicStart/publicEnd 真實 ID。

執行：
  $env:PYTHONUTF8=1
  .venv/Scripts/python.exe tools/dump_field_ids.py --base-url https://qa-khcg-ai.foxconn.com
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright
from lib.auth import prepare_authenticated_context
from lib.config_loader import load_config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=None)
    args = parser.parse_args()
    cfg = load_config()
    base_url = args.base_url or cfg["base_url"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        ctx = prepare_authenticated_context(browser)
        page = ctx.new_page()

        page.goto(f"{base_url}/entry/evevent", wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(2_000)
        page.get_by_role("button", name="新增", exact=True).click()
        page.wait_for_url("**/EVEventEdit/**", timeout=15_000)
        page.wait_for_timeout(3_000)

        field_ids = page.evaluate("""
            () => {
                const els = document.querySelectorAll('[data-field-id]');
                return Array.from(els).map(el => ({
                    id: el.getAttribute('data-field-id'),
                    label: (el.querySelector('label') || {}).textContent || ''
                }));
            }
        """)

        print(f"\n共找到 {len(field_ids)} 個 data-field-id：\n")
        for item in field_ids:
            label = item['label'].strip().replace('\n', ' ')[:40]
            print(f"  {item['id']:<55} label={label!r}")

        ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
