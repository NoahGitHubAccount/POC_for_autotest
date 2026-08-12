"""擷取指定活動的欄位資料 + DOM 結構快照。

用途：
  1. 讀出現有活動的所有欄位值，計算相對日期 offset（供寫自動建立腳本用）
  2. Dump datepicker panel 的 live HTML（src 不可信，需從真實 DOM 取結構）
  3. Dump 圖片上傳欄位的 live HTML

執行方式：
  $env:PYTHONUTF8=1
  # 若 config base_url 與目標環境不同，用 --base-url 覆蓋
  .venv/Scripts/python.exe tools/capture_activity_data.py --base-url https://<受測站 host>

  # session 過期時腳本會自動開啟登入頁讓你手動輸入驗證碼

輸出：
  reports/capture/<timestamp>/capture_result.json   — 欄位值 + offset
  reports/capture/<timestamp>/dp_panel_<case>.html  — datepicker panel HTML
  reports/capture/<timestamp>/img_upload_<case>.html — 圖片上傳區 HTML
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright

from lib.auth import (
    AUTH_DIR,
    load_session_storage_init_script,
    perform_interactive_login,
    save_session_storage,
    save_storage_state,
    storage_path,
)
from lib.config_loader import load_config

# ── 待擷取活動清單 ───────────────────────────────────────────────────────────
# 使用前請把 pkid 換成受測站上實際存在的活動；name 僅作輸出檔名標籤。
CASES = [
    {"name": "case1", "pkid": "REPLACE_ME"},
    {"name": "case2", "pkid": "REPLACE_ME"},
    {"name": "case3", "pkid": "REPLACE_ME"},
]

# ── 欄位 ID（對應 data-field-id）────────────────────────────────────────────
F_NAME      = "ActivityInfo_Introduction_name"
F_LOCATION  = "ActivityInfo_Introduction_locationName"
F_START     = "ActivityInfo_Introduction_startTime"
F_END       = "ActivityInfo_Introduction_endTime"
F_PUB_START = "ActivityInfo_Introduction_publishStartTime"
F_PUB_END   = "ActivityInfo_Introduction_publishEndTime"
F_REG_OPEN  = "ActivityRules_OpenRegistrationTime_registrationOpenFrom"
F_REG_CLOSE = "ActivityRules_OpenRegistrationTime_registrationCloseTo"
F_EXT_TEXT  = "ActivityInfo_Introduction_externalLinkText"
F_EXT_URL   = "ActivityInfo_Introduction_externalLinkUrl"

F_BANNER_PC     = "ActivityInfo_Introduction_bannerPC"
F_BANNER_MOBILE = "ActivityInfo_Introduction_bannerMobile"

TEXT_FIELDS = [F_NAME, F_LOCATION, F_EXT_TEXT, F_EXT_URL]
DP_FIELDS   = [F_START, F_END, F_PUB_START, F_PUB_END, F_REG_OPEN, F_REG_CLOSE]
IMG_FIELDS  = [F_BANNER_PC, F_BANNER_MOBILE]


def _read_text(page, field_id: str) -> str:
    try:
        loc = page.locator(f"[data-field-id='{field_id}'] input, [data-field-id='{field_id}'] textarea").first
        return (loc.input_value(timeout=3_000) or "").strip()
    except Exception:
        return "__READ_ERROR__"


def _read_dp(page, field_id: str) -> str:
    try:
        loc = page.locator(f"[data-field-id='{field_id}'] input.p-datepicker-input").first
        return (loc.input_value(timeout=3_000) or "").strip()
    except Exception:
        return "__READ_ERROR__"


def _dump_dp_panel(page, field_id: str) -> str:
    """點開 datepicker，dump panel HTML，然後按 Escape 關閉。"""
    try:
        inp = page.locator(f"[data-field-id='{field_id}'] input.p-datepicker-input").first
        inp.scroll_into_view_if_needed(timeout=5_000)
        inp.click(timeout=5_000)
        page.wait_for_timeout(800)

        # 嘗試多種 panel selector（src 不可信，試多個以確保命中）
        panel_selectors = [
            "[data-pc-name='datepickerpanel']",
            ".p-datepicker-panel",
            ".p-datepicker",
            "[role='dialog'][id*='pv_id']",
        ]
        html = "__PANEL_NOT_FOUND__"
        for sel in panel_selectors:
            try:
                loc = page.locator(sel).first
                if loc.is_visible(timeout=1_000):
                    html = loc.inner_html(timeout=3_000)
                    break
            except Exception:
                continue

        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        return html
    except Exception as e:
        return f"__ERROR: {e}__"


def _dump_container(page, field_id: str) -> str:
    try:
        loc = page.locator(f"[data-field-id='{field_id}']").first
        loc.scroll_into_view_if_needed(timeout=5_000)
        return loc.inner_html(timeout=5_000)
    except Exception as e:
        return f"__ERROR: {e}__"


def _parse_dt(s: str) -> datetime | None:
    """嘗試把欄位顯示值 parse 成 datetime（兼容 YYYY/MM/DD HH:mm 和 YYYY-MM-DD HH:mm）。"""
    if not s or s.startswith("__"):
        return None
    for fmt in ("%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M", "%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            continue
    return None


def _calc_offset(base: datetime, dt: datetime | None) -> dict | None:
    if dt is None:
        return None
    delta = dt - base
    return {
        "days": delta.days,
        "hour": dt.hour,
        "minute": dt.minute,
        "raw": dt.strftime("%Y/%m/%d %H:%M"),
    }


def _ensure_login(browser, base_url: str, cfg: dict) -> object:
    """確保有有效 context；session 過期則互動式重新登入後回傳新 context。"""
    role = "admin"
    sp = storage_path(role)
    ssp = AUTH_DIR / f"{role}.session.json"

    # 判斷 session 是否過期（超過 config 設定的 max_age_min）
    max_age_min = cfg.get("captcha", {}).get("session_max_age_min", 60)
    import time
    is_fresh = sp.exists() and (time.time() - sp.stat().st_mtime) < max_age_min * 60

    if is_fresh:
        print(f"  [auth] 使用既有 session（{sp}）")
        ctx = browser.new_context(storage_state=str(sp))
        script = load_session_storage_init_script(role)
        if script:
            ctx.add_init_script(script)
        return ctx

    # session 過期 → 互動式登入（不依賴 config 的 post_login_url_glob，改等 login 頁消失）
    print("\n[auth] session 已過期，開啟 QA 登入頁...")
    print("=" * 60)
    print("請在瀏覽器視窗：帳號/密碼/驗證碼 → 點「登入」")
    print("（最長等 10 分鐘，登入成功後自動繼續）")
    print("=" * 60)
    ctx = browser.new_context()
    page = ctx.new_page()
    login_url = f"{base_url}/entry/login"
    page.goto(login_url, wait_until="domcontentloaded", timeout=30_000)

    acc = cfg.get("accounts", {}).get(role, {})
    username = acc.get("username", "")
    password = acc.get("password", "")
    if username and username != "REPLACE_ME":
        try:
            page.get_by_placeholder("請輸入帳號").fill(username, timeout=5_000)
            page.get_by_placeholder("請輸入密碼").fill(password, timeout=5_000)
        except Exception:
            pass

    # 等待 URL 跳離 login 頁（不依賴特定後台路由）
    page.wait_for_url(lambda url: "login" not in url, timeout=600_000)
    page.wait_for_timeout(2500)
    save_storage_state(ctx, role=role)
    save_session_storage(page, role=role)
    print("  [auth] 登入成功，session 已儲存")
    return ctx


def main() -> int:
    parser = argparse.ArgumentParser(description="擷取活動資料 + DOM 快照")
    parser.add_argument(
        "--base-url",
        default=None,
        help="覆蓋 config 的 base_url（不帶則讀 config/config.<env>.yaml）",
    )
    args = parser.parse_args()

    cfg = load_config()
    base_url = args.base_url or cfg["base_url"]
    print(f"目標環境：{base_url}")

    now = datetime.now()
    ts = now.strftime("%Y%m%d_%H%M%S")

    out_dir = Path("reports") / "capture" / ts
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"輸出目錄：{out_dir}")

    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        ctx = _ensure_login(browser, base_url, cfg)
        page = ctx.new_page()

        for case in CASES:
            name  = case["name"]
            pkid  = case["pkid"]
            url   = f"{base_url}/entry/EVEventEdit/source=EVEvent&pkid={pkid}"
            print(f"\n=== [{name}] pkid={pkid} ===")

            page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_timeout(3_000)

            # ── 讀文字欄位 ────────────────────────────────────────────────
            texts = {fid: _read_text(page, fid) for fid in TEXT_FIELDS}
            dps   = {fid: _read_dp(page, fid) for fid in DP_FIELDS}
            for fid, val in {**texts, **dps}.items():
                short = fid.split("_")[-1]
                print(f"  {short}: {val!r}")

            # ── 計算相對 offset ───────────────────────────────────────────
            start_dt = _parse_dt(dps.get(F_START, ""))
            offsets = {}
            for fid in DP_FIELDS:
                dt = _parse_dt(dps.get(fid, ""))
                short = fid.split("_")[-1]
                if start_dt and dt:
                    from_start = _calc_offset(start_dt, dt)
                    offsets[short] = {"from_start": from_start}
                from_now = _calc_offset(now, dt)
                offsets[short] = offsets.get(short, {})
                offsets[short]["from_now"] = from_now

            # ── Dump datepicker panel HTML（只 dump 第一個 F_START）────────
            print(f"  [dump] 點開 startTime datepicker panel...")
            dp_panel_html = _dump_dp_panel(page, F_START)
            dp_file = out_dir / f"dp_panel_{name}.html"
            dp_file.write_text(dp_panel_html, encoding="utf-8")
            print(f"  [dump] 儲存 {dp_file}")

            # ── Dump 圖片上傳容器 HTML ────────────────────────────────────
            print(f"  [dump] 擷取圖片上傳容器 HTML...")
            img_parts = {}
            for fid in IMG_FIELDS:
                short = fid.split("_")[-1]
                img_parts[short] = _dump_container(page, fid)
            img_file = out_dir / f"img_upload_{name}.html"
            img_content = "\n\n<!-- ==================== -->\n\n".join(
                f"<!-- field: {fid} -->\n{html}"
                for fid, html in img_parts.items()
            )
            img_file.write_text(img_content, encoding="utf-8")
            print(f"  [dump] 儲存 {img_file}")

            results[name] = {
                "pkid":    pkid,
                "url":     url,
                "texts":   texts,
                "dps":     dps,
                "offsets": offsets,
            }

        # ── 補充：從「新增活動」頁 dump enabled 狀態的 datepicker panel ──────
        print("\n=== [新增活動頁] dump datepicker panel（enabled 狀態）===")
        try:
            page.goto(f"{base_url}/entry/evevent", wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_timeout(2_000)

            # 找並點「新增」按鈕
            create_btn = page.get_by_role("button", name="新增", exact=True)
            create_btn.wait_for(state="visible", timeout=15_000)
            create_btn.click()
            page.wait_for_url("**/EVEventEdit/**", timeout=15_000)
            page.wait_for_timeout(2_500)

            # 也 dump 一份整個 data-field-id=F_START 容器的 outerHTML（確認欄位結構）
            fid_container_html = "__NOT_FOUND__"
            try:
                container = page.locator(f"[data-field-id='{F_START}']").first
                container.scroll_into_view_if_needed(timeout=5_000)
                fid_container_html = container.inner_html(timeout=5_000)
            except Exception as e:
                fid_container_html = f"__ERROR: {e}__"

            container_file = out_dir / "new_form_startTime_container.html"
            container_file.write_text(fid_container_html, encoding="utf-8")
            print(f"  [dump] 儲存 {container_file}")

            # dump panel
            new_dp_html = _dump_dp_panel(page, F_START)
            new_dp_file = out_dir / "dp_panel_NEW_FORM.html"
            new_dp_file.write_text(new_dp_html, encoding="utf-8")
            print(f"  [dump] 儲存 {new_dp_file}")

            # 也 dump publicStartTime 容器確認欄位 ID
            for fid in [F_PUB_START, F_PUB_END, F_LOCATION]:
                short = fid.split("_")[-1]
                try:
                    c = page.locator(f"[data-field-id='{fid}']").first
                    if c.count() > 0:
                        html = c.inner_html(timeout=3_000)
                        status = f"找到({len(html)} chars)"
                    else:
                        html = "__CONTAINER_NOT_FOUND__"
                        status = "容器不存在"
                except Exception as e:
                    html = f"__ERROR: {e}__"
                    status = f"ERROR"
                debug_file = out_dir / f"new_form_{short}_container.html"
                debug_file.write_text(html, encoding="utf-8")
                print(f"  [{short}] {status} → {debug_file}")

        except Exception as e:
            print(f"  [新增活動頁 dump 失敗] {e}")

        ctx.close()
        browser.close()

    # ── 輸出 JSON 結果 ────────────────────────────────────────────────────
    json_file = out_dir / "capture_result.json"
    json_file.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n=== 完成 ===")
    print(f"欄位值 JSON：{json_file}")
    print(f"datepicker HTML：{out_dir}/dp_panel_*.html")
    print(f"圖片上傳 HTML：{out_dir}/img_upload_*.html")
    print("\n請將 dp_panel_*.html 與 img_upload_*.html 的內容貼給我，")
    print("我依此寫出正確的 datepicker 操作 helper 與建立腳本。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
