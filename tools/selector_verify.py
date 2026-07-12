"""
selector_verify.py -- 驗證 selector 是否在 live DOM 存在且可見。

用法：
    python tools/selector_verify.py --url <URL> --selector "text:新增場次"
    python tools/selector_verify.py --url <URL> --file selectors.txt

selector 格式（每行一個）：
    text:X           -> get_by_text(X, exact=True)
    role:button:X    -> get_by_role("button", name=X)
    label:X          -> get_by_label(X)
    testid:X         -> get_by_test_id(X)
    css:X or X       -> locator(X)
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright
from lib.auth import restore_session
from lib.config_loader import load_config


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--selector", default="")
    p.add_argument("--file", default="")
    p.add_argument("--timeout", type=int, default=5000)
    return p.parse_args()


def resolve(page, spec):
    spec = spec.strip()
    if spec.startswith("text:"):
        return page.get_by_text(spec[5:], exact=True)
    if spec.startswith("role:"):
        parts = spec[5:].split(":", 1)
        return page.get_by_role(parts[0], name=parts[1]) if len(parts) > 1 else page.get_by_role(parts[0])
    if spec.startswith("label:"):
        return page.get_by_label(spec[6:])
    if spec.startswith("testid:"):
        return page.get_by_test_id(spec[7:])
    return page.locator(spec.removeprefix("css:"))


def verify(page, spec):
    try:
        loc = resolve(page, spec)
        count = loc.count()
        if count == 0:
            return False, "count=0（找不到）"
        return True, f"count={count}  visible={loc.first.is_visible()}"
    except Exception as e:
        return False, f"例外：{e}"


def main():
    args = parse_args()
    cfg = load_config()
    specs = []
    if args.selector:
        specs.append(args.selector)
    if args.file:
        specs += [l.strip() for l in Path(args.file).read_text(encoding="utf-8").splitlines()
                  if l.strip() and not l.startswith("#")]
    if not specs:
        print("[ERROR] 請提供 --selector 或 --file")
        sys.exit(1)

    fail_count = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = restore_session(browser, cfg)
        page = ctx.new_page()
        print(f"導航至：{args.url}")
        page.goto(args.url, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        print(f"\n{'結果':<8} {'SELECTOR':<50} DETAIL")
        print("-" * 88)
        for spec in specs:
            ok, detail = verify(page, spec)
            tag = "PASS" if ok else "FAIL"
            print(f"  {tag:<6} {spec:<50} {detail}")
            if not ok:
                fail_count += 1
        browser.close()

    print(f"\n{'全部通過' if not fail_count else f'失敗 {fail_count}/{len(specs)}'}")
    sys.exit(1 if fail_count else 0)


if __name__ == "__main__":
    main()