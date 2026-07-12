"""
inventory_fields.py — 列出 EVEventEdit 頁所有欄位的 data-field-id、label 文字、元件型別。
用途：驗證 data-field-id 覆蓋率，作為 selector 設計依據。

用法：
    python tools/inventory_fields.py [--pkid <pkid>] [--out inventory_out.txt]
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
    ap.add_argument("--pkid", default=None, help="EVEventEdit pkid（預設讀 config event_edit_pkid）")
    ap.add_argument("--out", default="inventory_out.txt")
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

        # 捲到底讓 lazy 元素觸發，再回頂
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

        lines: list[str] = [f"URL: {page.url}", f"TITLE: {page.title()}", ""]

        # ── 1. 所有 data-field-id 欄位 ──────────────────────────────
        fields = page.evaluate("""() => {
            const rows = document.querySelectorAll('[data-field-id]');
            return Array.from(rows).map(el => {
                const fid  = el.getAttribute('data-field-id');
                const fkey = el.getAttribute('data-field') || '';
                // label 文字（去掉 * span）
                const labelEl = el.querySelector('label');
                let labelText = '';
                if (labelEl) {
                    // 只取 text node，略過 span（必填 *）
                    labelText = Array.from(labelEl.childNodes)
                        .filter(n => n.nodeType === Node.TEXT_NODE)
                        .map(n => n.textContent.trim())
                        .join('').trim();
                }
                // PrimeVue 元件型別
                const pcEls = el.querySelectorAll('[data-pc-name]');
                const pcNames = [...new Set(Array.from(pcEls).map(e => e.getAttribute('data-pc-name')))];
                // 是否可見
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                const visible = style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0;
                return { fid, fkey, labelText, pcNames, visible };
            });
        }""")

        lines.append(f"=== data-field-id 欄位（共 {len(fields)} 個）===")
        for f in fields:
            vis = "V" if f["visible"] else "H"  # V=visible H=hidden
            pc = ", ".join(f["pcNames"]) or "(none)"
            lines.append(f"  [{vis}] {f['fid']}")
            lines.append(f"       label : {f['labelText'] or '(無 label)'}")
            lines.append(f"       field : {f['fkey']}")
            lines.append(f"       pc    : {pc}")

        # ── 2. 主要區塊中無 data-field-id 的可見文字區塊 ─────────────
        orphans = page.evaluate("""() => {
            // 找主內容區（排除 header/aside/nav）
            const main = document.querySelector('main') || document.body;
            // 在 main 裡找「含可見文字、但自己沒有 data-field-id、且祖先也沒有」的葉節點文字
            const result = [];
            const walker = document.createTreeWalker(main, NodeFilter.SHOW_TEXT);
            let node;
            while ((node = walker.nextNode())) {
                const t = node.textContent.trim();
                if (t.length < 4) continue;
                let el = node.parentElement;
                // 確認祖先鏈裡沒有 data-field-id
                let hasField = false;
                let cur = el;
                while (cur && cur !== main) {
                    if (cur.hasAttribute('data-field-id')) { hasField = true; break; }
                    cur = cur.parentElement;
                }
                if (hasField) continue;
                // 確認可見
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden') continue;
                const rect = el.getBoundingClientRect();
                if (rect.width === 0) continue;
                // 標籤名 + text
                result.push({ tag: el.tagName.toLowerCase(), text: t.substring(0, 80) });
            }
            // 去重
            const seen = new Set();
            return result.filter(r => { const k = r.tag+r.text; if(seen.has(k)) return false; seen.add(k); return true; });
        }""")

        lines.append("")
        lines.append(f"=== 無 data-field-id 的可見文字（main 內，共 {len(orphans)} 個）===")
        for o in orphans:
            lines.append(f"  <{o['tag']}> {o['text']}")

        ctx.close()
        browser.close()

    result = "\n".join(lines)
    Path(args.out).write_text(result, encoding="utf-8")
    print(f"已寫入 {args.out}（{len(result)} chars）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
