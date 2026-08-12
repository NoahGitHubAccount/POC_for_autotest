# -*- coding: utf-8 -*-
"""「下載範本 → 原封不動上傳」探測腳本（一次性探測，不改既有測試）。

流程：管理工作人員名單 drawer → 下載 excel 模板 → **原封不動**上傳同一檔案 → 收集回饋。
用途：當開發端回報「無法重現匯入錯誤」時，用最乾淨的輸入（官方模板本身）隔離變因，
判定問題是出在測試資料還是程式邏輯。可作為同類「匯入功能爭議」的探測範本。
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from playwright.sync_api import sync_playwright

from lib import auth
from lib.config_loader import load_config
from lib.selectors import EventListPage

ASSETS = PROJECT_ROOT / "reports" / "_assets_it06"
RAW_TPL = ASSETS / "staff_template_raw.xlsx"


def dump_xlsx(path: Path) -> None:
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb.active
    print(f"[檔案] {path.name}（{path.stat().st_size} bytes）sheet={ws.title!r}")
    for r_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
        print(f"  第{r_idx}列: {row!r}")
        if r_idx >= 10:
            print("  ...（僅列前 10 列）")
            break
    wb.close()


def main() -> None:
    config = load_config()
    base_url = config["base_url"]
    role = "admin"

    sp = auth.storage_path(role)
    if not sp.exists():
        raise SystemExit(f"找不到 {sp}，請先 warm-login")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = auth.prepare_authenticated_context(browser, role)
        page = ctx.new_page()

        print("[1] 開啟活動列表頁")
        page.goto(base_url + EventListPage.PATH, wait_until="domcontentloaded")
        EventListPage.reset_button(page).wait_for(state="visible", timeout=15_000)
        page.wait_for_timeout(1_500)

        row = EventListPage.list_rows(page).nth(0)
        print("[2] 點第一列「更多」→ 管理工作人員名單")
        EventListPage.action_icon(row, 4).click()
        page.wait_for_timeout(800)
        page.get_by_text("管理工作人員名單", exact=True).first.click()
        page.wait_for_timeout(1_500)

        empty_before = page.get_by_text("尚未建立工作人員名單", exact=False).count()
        print(f"[3] drawer 開啟，上傳前「尚未建立工作人員名單」出現次數={empty_before}")

        print("[4] 下載 excel 模板（不做任何修改）")
        with page.expect_download(timeout=15_000) as dl:
            page.get_by_text("下載excel模板", exact=True).first.click()
        RAW_TPL.parent.mkdir(parents=True, exist_ok=True)
        dl.value.save_as(str(RAW_TPL))
        dump_xlsx(RAW_TPL)

        print("[5] 原封不動上傳同一檔案")
        with page.expect_file_chooser(timeout=15_000) as fc:
            page.get_by_text("上傳名單", exact=True).first.click()
        fc.value.set_files(str(RAW_TPL))
        page.wait_for_timeout(3_000)

        print("[6] 收集回饋")
        toasts = [t.strip() for t in page.locator("[class*='toast']").all_inner_texts()
                  if t and t.strip()]
        # 去重（同訊息出現在 3 個容器，見 docs/dom_facts/EventList.md）
        uniq_toasts = list(dict.fromkeys(toasts))
        try:
            drawer_text = " ".join(
                page.get_by_text("工作人員名單管理").first
                .locator("xpath=ancestor::*[3]").inner_text().split())
        except Exception as e:
            drawer_text = f"（讀取 drawer 文字失敗：{e}）"
        empty_after = page.get_by_text("尚未建立工作人員名單", exact=False).count()

        print(f"toast 訊息（去重，共 {len(uniq_toasts)} 種 / 原始 {len(toasts)} 個容器）:")
        for t in uniq_toasts:
            print(f"  - {t!r}")
        print(f"上傳後「尚未建立工作人員名單」出現次數={empty_after}"
              f"（空狀態消失={empty_after == 0}）")
        print(f"drawer 內文（前 500 字）: {drawer_text[:500]!r}")

        page.screenshot(path=str(ASSETS / "probe_raw_upload_result.png"), full_page=False)
        print(f"[7] 截圖存於 {ASSETS / 'probe_raw_upload_result.png'}")

        browser.close()


if __name__ == "__main__":
    main()
