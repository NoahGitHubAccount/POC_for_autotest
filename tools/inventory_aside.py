"""
inventory_aside.py — 列出 EVEventEdit 頁 aside 元素的完整結構。
用途：確認 2-3-11（填寫建議）與 2-3-12（即時預覽）的真實 DOM，一次取對 selector。

用法：
    python tools/inventory_aside.py [--pkid <pkid>] [--out aside_out.txt]
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright
from lib.auth import DEFAULT_ROLE, has_fresh_session, prepare_authenticated_context
from lib.config_loader import load_config


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkid", default=None)
    ap.add_argument("--out", default="aside_out.txt")
    args = ap.parse_args()

    cfg = load_config()
    if not has_fresh_session(DEFAULT_ROLE, cfg["captcha"]["session_max_age_min"]):
        print("session 過期，請先執行 warm_login.py", file=sys.stderr)
        return 2

    pkid = args.pkid or cfg.get("event_edit_pkid", "")
    if not pkid:
        print("請在 config 設定 event_edit_pkid 或用 --pkid 指定", file=sys.stderr)
        return 1

    url = f"{cfg['base_url']}/entry/EVEventEdit/source=EVEvent&pkid={pkid}"

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = prepare_authenticated_context(browser, role=DEFAULT_ROLE,
                                            viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        print(f"前往 {url} ...")
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

        lines: list[str] = [f"URL: {page.url}", ""]

        # ── 所有 aside 的概要 ──────────────────────────────────────
        asides = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('aside')).map((aside, i) => {
                const rect = aside.getBoundingClientRect();
                const style = window.getComputedStyle(aside);
                const visible = style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0;
                // 取前 200 字可見文字
                const walker = document.createTreeWalker(aside, NodeFilter.SHOW_TEXT);
                const texts = [];
                let node;
                while ((node = walker.nextNode())) {
                    const t = node.textContent.trim();
                    if (t.length > 1) texts.push(t);
                }
                const textPreview = texts.slice(0, 15).join(' | ');
                // 找關鍵屬性
                const attrs = [];
                for (const attr of aside.attributes) attrs.push(`${attr.name}="${attr.value}"`);
                // 找直接子元素摘要
                const children = Array.from(aside.children).map(c => {
                    const ca = [];
                    for (const a of c.attributes) ca.push(`${a.name}="${a.value}"`);
                    return `<${c.tagName.toLowerCase()} ${ca.join(' ')}>`;
                });
                return { i, visible, attrs, children, textPreview,
                         width: Math.round(rect.width), height: Math.round(rect.height) };
            });
        }""")

        lines.append(f"=== aside 元素（共 {len(asides)} 個）===")
        for a in asides:
            vis = "V" if a["visible"] else "H"
            lines.append(f"\n[{a['i']}] [{vis}] {a['width']}×{a['height']}px")
            lines.append(f"  attrs   : {' '.join(a['attrs']) or '(none)'}")
            lines.append(f"  children: {chr(10)+'  '.join(a['children']) if a['children'] else '(none)'}")
            lines.append(f"  text    : {a['textPreview']}")

        # ── 詳細：找含「填寫建議」的 aside ────────────────────────
        sidebar_html = page.evaluate("""() => {
            const asides = Array.from(document.querySelectorAll('aside'));
            for (const a of asides) {
                if (a.textContent.includes('填寫建議')) {
                    return a.outerHTML.substring(0, 8000);
                }
            }
            return null;
        }""")

        lines.append("\n\n=== 含「填寫建議」的 aside outerHTML（前 8000 字）===")
        lines.append(sidebar_html or "(找不到)")

        # ── 詳細：找含「data-preview-panel-root」或「活動預覽」的 aside ──
        preview_html = page.evaluate("""() => {
            // 先找 data-preview-panel-root
            const root = document.querySelector('[data-preview-panel-root]');
            if (root) {
                // 往上找到最近的 aside
                let cur = root;
                while (cur && cur.tagName !== 'ASIDE') cur = cur.parentElement;
                if (cur) return { from: 'aside', html: cur.outerHTML.substring(0, 8000) };
                return { from: 'data-preview-panel-root', html: root.outerHTML.substring(0, 8000) };
            }
            // fallback: 找含「活動預覽」的 aside
            const asides = Array.from(document.querySelectorAll('aside'));
            for (const a of asides) {
                if (a.textContent.includes('活動預覽')) {
                    return { from: 'aside text', html: a.outerHTML.substring(0, 8000) };
                }
            }
            return null;
        }""")

        lines.append("\n\n=== 即時預覽 aside outerHTML（前 8000 字）===")
        if preview_html:
            lines.append(f"(找到方式: {preview_html['from']})")
            lines.append(preview_html["html"])
        else:
            lines.append("(找不到)")

        # ── 填寫建議清單項目詳細 ──────────────────────────────────
        items = page.evaluate("""() => {
            const asides = Array.from(document.querySelectorAll('aside'));
            for (const a of asides) {
                if (!a.textContent.includes('填寫建議')) continue;
                // 找清單項目
                const lis = a.querySelectorAll('li');
                return Array.from(lis).map(li => {
                    const img = li.querySelector('img');
                    const imgSrc = img ? img.getAttribute('src') : null;
                    // img src 中有顏色 hex 判斷完成狀態
                    const done = imgSrc ? imgSrc.includes('1FC97B') : null;
                    const text = li.textContent.trim().substring(0, 100);
                    // li 本身的 class
                    return { text, done, liClass: li.className, imgSrc: imgSrc ? imgSrc.substring(0, 80) : null };
                });
            }
            return [];
        }""")

        lines.append("\n\n=== 填寫建議清單項目 ===")
        if items:
            for it in items:
                status = "✅" if it["done"] else ("⬜" if it["done"] is False else "?")
                lines.append(f"  {status} {it['text']}")
                lines.append(f"     li class : {it['liClass']}")
                lines.append(f"     img src  : {it['imgSrc']}")
        else:
            lines.append("(找不到 li 項目)")

        # ── 即時預覽 sub-tabs ─────────────────────────────────────
        preview_tabs = page.evaluate("""() => {
            const root = document.querySelector('[data-preview-panel-root]');
            if (!root) return null;
            // 找 button（sub-tabs）
            const btns = root.querySelectorAll('button');
            return Array.from(btns).map(b => ({
                text: b.textContent.trim(),
                classes: b.className.substring(0, 100),
                dataAttrs: Array.from(b.attributes)
                    .filter(a => a.name.startsWith('data-') || a.name === 'aria-selected')
                    .map(a => `${a.name}="${a.value}"`).join(' ')
            }));
        }""")

        lines.append("\n\n=== 即時預覽 sub-tab buttons ===")
        if preview_tabs is None:
            lines.append("(找不到 [data-preview-panel-root])")
        elif preview_tabs:
            for bt in preview_tabs:
                lines.append(f"  [{bt['text']}]  class={bt['classes']}  {bt['dataAttrs']}")
        else:
            lines.append("(無 button)")

        ctx.close()
        browser.close()

    result = "\n".join(lines)
    Path(args.out).write_text(result, encoding="utf-8")
    print(f"已寫入 {args.out}（{len(result)} chars）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
