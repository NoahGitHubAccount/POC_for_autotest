"""
dump_sections.py — 定向抓取 EVEventEdit 頁特定區塊的 HTML 與可見文字。
用途：修 selector 前取得真實 DOM，不靠 src 推測。

用法：
    python tools/dump_sections.py <full_url> [--out path] [--wait-ms 5000]

輸出：
    每個目標 section 的外層容器 outerHTML（截短至合理大小）
    + 該 section 內所有可見文字清單
"""
from __future__ import annotations
import argparse, sys, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright
from lib.auth import DEFAULT_ROLE, has_fresh_session, prepare_authenticated_context
from lib.config_loader import load_config

# 要尋找的區塊關鍵字（順序 = 輸出順序）
# (tab_to_click, keyword_to_find)
# tab_to_click=None 表示不需要切換 tab
TARGET_SECTIONS = [
    ("報名欄位設定",   "報名欄位設定"),   # 先 click tab，再找 panel 內容
    ("憑證與報到管理", "憑證與報到管理"), # tab label 不含「設定」
    (None,             "即時預覽"),        # 可能在 tab 外
]

def dump_tabpanel(page, tab_name: str) -> str | None:
    """點 tab 後透過 aria-controls 取 tabpanel outerHTML。"""
    # 1. 找 tab button
    tab = page.locator("[role='tab']").filter(has_text=tab_name).first
    controls = tab.get_attribute("aria-controls", timeout=3000)
    debug_lines = [f"  [DBG] aria-controls={controls}"]

    # 2. 先等 role=tabpanel 出現（lazy render 需要等 click 完成）
    all_panels = page.locator("[role='tabpanel']")
    panel_count = all_panels.count()
    debug_lines.append(f"  [DBG] role=tabpanel count={panel_count}")
    for i in range(panel_count):
        p = all_panels.nth(i)
        pid = p.get_attribute("id") or "(no id)"
        debug_lines.append(f"    panel[{i}] id={pid}")

    if not controls:
        return "\n".join(debug_lines) + f"\n[NOT FOUND] tab「{tab_name}」沒有 aria-controls 屬性"

    panel = page.locator(f"#{controls}")
    if panel.count() == 0:
        # 備援：取第一個可見 tabpanel
        visible = page.locator("[role='tabpanel']:visible")
        if visible.count() > 0:
            debug_lines.append(f"  [DBG] fallback to first visible tabpanel")
            try:
                return "\n".join(debug_lines) + "\n" + visible.first.evaluate(
                    "el => el.outerHTML.substring(0, 12000)")
            except Exception as e:
                return "\n".join(debug_lines) + f"\n[ERROR fallback] {e}"
        return "\n".join(debug_lines) + f"\n[NOT FOUND] tabpanel #{controls} 不存在，且無可見 tabpanel"
    try:
        return "\n".join(debug_lines) + "\n" + panel.evaluate("el => el.outerHTML.substring(0, 12000)")
    except Exception as e:
        return "\n".join(debug_lines) + f"\n[ERROR] {e}"


def find_section_ancestor(page, keyword: str, max_depth: int = 8) -> str | None:
    """找包含 keyword 文字的最近 section-level 容器，回傳 outerHTML（截短）。"""
    els = page.locator(f"text={keyword}").all()
    if not els:
        return f"[NOT FOUND] 找不到含「{keyword}」的元素"
    el = els[0]
    js = """(el, depth) => {
        let cur = el;
        for (let i = 0; i < depth; i++) {
            if (!cur.parentElement) break;
            cur = cur.parentElement;
            const h = cur.getBoundingClientRect().height;
            const tag = cur.tagName.toLowerCase();
            if (h > 300 && (tag === 'div' || tag === 'section' || tag === 'form')) {
                return cur.outerHTML.substring(0, 12000);
            }
        }
        return cur.outerHTML.substring(0, 12000);
    }"""
    try:
        html = el.evaluate(js, max_depth)
        return html
    except Exception as e:
        return f"[ERROR] {e}"


def visible_texts_near(page, keyword: str) -> list[str]:
    """收集含 keyword 元素附近（同 section）的所有可見短文字（label 候選）。"""
    els = page.locator(f"text={keyword}").all()
    if not els:
        return []
    el = els[0]
    js = """(el, depth) => {
        let cur = el;
        for (let i = 0; i < depth; i++) {
            if (!cur.parentElement) break;
            cur = cur.parentElement;
            if (cur.getBoundingClientRect().height > 300) break;
        }
        // 取所有葉節點文字（去空白）
        const walker = document.createTreeWalker(cur, NodeFilter.SHOW_TEXT);
        const texts = [];
        let node;
        while ((node = walker.nextNode())) {
            const t = node.textContent.trim();
            if (t.length > 1 && t.length < 60) texts.push(t);
        }
        return [...new Set(texts)];
    }"""
    try:
        return el.evaluate(js, 10) or []
    except Exception:
        return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url", help="目標完整 URL")
    ap.add_argument("--out", default=".tmp_dump_out.txt")
    ap.add_argument("--wait-ms", type=int, default=5000)
    args = ap.parse_args()

    cfg = load_config()
    if not has_fresh_session(DEFAULT_ROLE, cfg["captcha"]["session_max_age_min"]):
        print("session 過期，請先：python tools/run.py --warm-login", file=sys.stderr)
        return 2

    out_lines: list[str] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = prepare_authenticated_context(
            browser, role=DEFAULT_ROLE,
            viewport={"width": 1440, "height": 900},
        )
        page = ctx.new_page()
        page.goto(args.url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(args.wait_ms)

        if "/entry/login" in page.url:
            print("被導向登入頁，session 可能失效。", file=sys.stderr)
            return 2

        out_lines.append(f"URL: {page.url}")
        out_lines.append(f"TITLE: {page.title()}\n")

        # 先捲到底讓 lazy render 全部觸發
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

        # ── 診斷：列出頁面所有 data-pc-name 元素 ──
        pc_names = page.evaluate("""() => {
            const els = document.querySelectorAll('[data-pc-name]');
            const seen = new Set();
            const result = [];
            els.forEach(el => {
                const n = el.getAttribute('data-pc-name');
                if (!seen.has(n)) { seen.add(n); result.push(n); }
            });
            return result;
        }""")
        out_lines.append("[DBG] data-pc-name 元素種類：" + ", ".join(pc_names or []))

        for tab_name, kw in TARGET_SECTIONS:
            out_lines.append("=" * 60)
            out_lines.append(f"[SECTION] {kw}" + (f"  (tab: {tab_name})" if tab_name else ""))
            out_lines.append("=" * 60)

            # 若需切換 tab，點選 tab 並等待渲染
            # 用 filter(has_text=) 而非 get_by_role(name=)：tab 內含 SVG icon，
            # accessible name 計算可能含 SVG content，導致 name= 匹配失敗。
            if tab_name:
                try:
                    tab = page.locator("[role='tab']").filter(has_text=tab_name).first
                    tab.click(timeout=5000)
                    page.wait_for_timeout(1500)
                except Exception as e:
                    out_lines.append(f"[WARN] 切換 tab 失敗：{e}")

            # 捲到關鍵字元素
            els = page.locator(f"text={kw}").all()
            if els:
                try:
                    els[0].scroll_into_view_if_needed(timeout=3000)
                    page.wait_for_timeout(800)
                except Exception:
                    pass

            # 可見文字清單
            texts = visible_texts_near(page, kw)
            out_lines.append("[可見文字列表]")
            for t in texts:
                out_lines.append(f"  • {t}")

            # 區塊 HTML：tab panel 用 aria-controls 定位；其餘用祖先爬升
            out_lines.append("\n[HTML 節錄（前 12000 字元）]")
            if tab_name:
                html = dump_tabpanel(page, tab_name)
            else:
                html = find_section_ancestor(page, kw)
            out_lines.append(html or "(empty)")
            out_lines.append("")

        ctx.close()
        browser.close()

    result = "\n".join(out_lines)
    Path(args.out).write_text(result, encoding="utf-8")
    print(f"已寫入 {args.out}（{len(result)} chars）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
