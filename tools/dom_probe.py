"""
dom_probe.py -- 宣告式 DOM 探測器：一次 browser session 回答多個 DOM 問題。

取代一次性 `_diag_*.py` 腳本：改問題只改 steps 檔，不重寫腳本、不重新登入。
（21 支歷史 diag 腳本已歸檔至 tools/_archive/，其驗證過的招式均已內建於此。）

用法：
    python tools/dom_probe.py --steps probe.txt [--headed] [--out result.txt]
    python tools/dom_probe.py --step "goto /entry/evevent" --step "verify text:新增場次"

steps 檔格式（每行一個指令；# 開頭為註解）：
    goto <path或完整URL>         # path 以 / 開頭時自動接 config base_url
    wait <ms>                    # page.wait_for_timeout（勿用 time.sleep，見 99 經驗 2026-05-20）
    tab <文字>                   # click [role='tab'].filter(has_text=...) 後等 1 秒（SVG 干擾 accessible name）
    click <selector>             # 點擊
    fill <selector> = <值>       # fill 後按 Tab
    verify <selector>            # count + visible 檢查（原 selector_verify 功能）
    fields                       # 列出所有 data-field-id（原 _diag_fields / inventory 精簡版）
    textscan <關鍵字>            # TreeWalker 掃文字節點：tag / display / visibility（原 _diag_session_text3）
    html <selector>              # 該元素 outerHTML 前 800 字元
    attrs <selector> <屬性名>    # 列出所有匹配元素的該屬性值（如 attrs css:img src）
    buttons                      # 列出可見 button 與 [role='button'] 的文字

selector 格式（與 selector_verify.py 相同）：
    text:X           -> get_by_text(X, exact=True)
    role:button:X    -> get_by_role("button", name=X)
    label:X          -> get_by_label(X)
    testid:X         -> get_by_test_id(X)
    css:X 或 X       -> locator(X)
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright
from lib.auth import prepare_authenticated_context
from lib.config_loader import load_config

TEXTSCAN_JS = """(kw) => {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const found = [];
    let node;
    while (node = walker.nextNode()) {
        const t = node.textContent.trim();
        if (t && t.includes(kw)) {
            const p = node.parentElement;
            const st = p ? window.getComputedStyle(p) : null;
            found.push({
                text: t.substring(0, 80),
                tag: p ? p.tagName : '?',
                display: st ? st.display : '?',
                visibility: st ? st.visibility : '?',
            });
        }
    }
    return found.slice(0, 40);
}"""


def resolve(page, spec: str):
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


def run_step(page, cfg, line: str, out) -> bool:
    """執行一個指令；回傳 False 代表該步失敗（繼續跑後續步驟）。"""
    cmd, _, arg = line.partition(" ")
    cmd, arg = cmd.lower(), arg.strip()
    ok = True
    try:
        if cmd == "goto":
            url = cfg["base_url"] + arg if arg.startswith("/") else arg
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            out(f"  url   = {page.url}")
            out(f"  title = {page.title()}")
        elif cmd == "wait":
            page.wait_for_timeout(int(arg))
        elif cmd == "tab":
            page.locator("[role='tab']").filter(has_text=arg).first.click()
            page.wait_for_timeout(1000)  # PrimeVue lazy render，等 panel 進 DOM
        elif cmd == "click":
            resolve(page, arg).first.click()
            page.wait_for_timeout(500)
        elif cmd == "fill":
            spec, _, value = arg.partition(" = ")
            loc = resolve(page, spec.strip()).first
            loc.fill(value)
            page.keyboard.press("Tab")
            page.wait_for_timeout(300)
        elif cmd == "verify":
            loc = resolve(page, arg)
            n = loc.count()
            if n == 0:
                out("  FAIL  count=0（找不到）")
                ok = False
            else:
                out(f"  PASS  count={n}  visible={loc.first.is_visible()}")
        elif cmd == "fields":
            ids = page.evaluate(
                "() => Array.from(document.querySelectorAll('[data-field-id]'))"
                ".map(e => e.getAttribute('data-field-id'))"
            )
            out(f"  data-field-id 共 {len(ids)} 個：")
            for fid in ids:
                out(f"    {fid}")
        elif cmd == "textscan":
            results = page.evaluate(TEXTSCAN_JS, arg)
            out(f"  含「{arg}」的文字節點共 {len(results)} 個：")
            for r in results:
                mark = "★" if r["text"] == arg else " "
                out(f"  {mark} {r['text']!r:<44} tag={r['tag']:<8} display={r['display']:<12} vis={r['visibility']}")
        elif cmd == "html":
            loc = resolve(page, arg).first
            out("  " + loc.evaluate("e => e.outerHTML")[:800])
        elif cmd == "attrs":
            spec, _, attr = arg.rpartition(" ")
            loc = resolve(page, spec.strip())
            n = loc.count()
            out(f"  {spec} 共 {n} 個，屬性 {attr}：")
            for i in range(min(n, 30)):
                val = loc.nth(i).get_attribute(attr) or "(無)"
                out(f"    [{i}] {val[:120]}")
        elif cmd == "buttons":
            btns = page.locator("button:visible, [role='button']:visible")
            out(f"  可見 button 共 {btns.count()} 個：")
            for i in range(min(btns.count(), 30)):
                txt = btns.nth(i).inner_text(timeout=1000).strip().replace("\n", " ")
                out(f"    [{i}] {txt[:60]!r}")
        else:
            out(f"  未知指令：{cmd}")
            ok = False
    except Exception as e:
        out(f"  例外：{type(e).__name__}: {str(e)[:200]}")
        ok = False
    return ok


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--steps", default="", help="steps 檔路徑")
    p.add_argument("--step", action="append", default=[], help="單行指令（可重複）")
    p.add_argument("--headed", action="store_true")
    p.add_argument("--out", default="", help="同步寫入輸出檔（UTF-8）")
    args = p.parse_args()

    lines = []
    if args.steps:
        lines += [l.strip() for l in Path(args.steps).read_text(encoding="utf-8").splitlines()
                  if l.strip() and not l.strip().startswith("#")]
    lines += args.step
    if not lines:
        print("[ERROR] 請提供 --steps 或 --step")
        sys.exit(1)

    buf = []

    def out(msg):
        print(msg)
        buf.append(msg)

    cfg = load_config()
    fail = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed)
        ctx = prepare_authenticated_context(browser, viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        for i, line in enumerate(lines, 1):
            out(f"\n[{i}/{len(lines)}] {line}")
            if not run_step(page, cfg, line, out):
                fail += 1
        browser.close()

    out(f"\n{'全部完成' if not fail else f'{fail}/{len(lines)} 步驟有問題'}")
    if args.out:
        Path(args.out).write_text("\n".join(buf), encoding="utf-8")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
