# -*- coding: utf-8 -*-
"""刪除 A 桶（自動化測試產物）活動。使用者核准後執行。
雙重保險：只刪「蘇哲正(自動化帳號)建 + A桶命名特徵」；KEEP 三筆與其他帳號絕不刪。
結果寫入 tools/delete_result.txt。"""
import sys, io, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from playwright.sync_api import sync_playwright
from lib import ops
from lib.auth import storage_path, load_session_storage_init_script

BASE = "https://qa-khcg-ai.foxconn.com"
KEEP = {"34185325523320832", "34155861376110592", "34168368758263808"}
AUTO_ACCT = "蘇哲正"
KNOWN_DELETE = {"34174300370589696", "34174303839862784", "34185353624633344", "34185347837804544"}
AUTO_NAME = [r"^IT0?\d", r"^PROBE_", r"_copy$", r"^LoadTest_", r"^AItest_"]
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "delete_result.txt")

def is_A(pk, nm, who):
    if pk in KEEP:
        return False
    if pk in KNOWN_DELETE:
        return True
    if who != AUTO_ACCT:            # 硬保險：非自動化帳號一律不刪
        return False
    return any(re.search(x, nm) for x in AUTO_NAME) or nm == "未命名活動"

import traceback
try:
    print("start: launching browser...", flush=True)
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(storage_state=str(storage_path("admin")))
        ss = load_session_storage_init_script("admin")
        if ss:
            ctx.add_init_script(ss)
        pg = ctx.new_page()
        print("goto app (載入活動列表取得 token)...", flush=True)
        ops.goto_app(pg, BASE)
        print("querying events...", flush=True)
        data = ops.api_call(pg, "GET", "/reventmodule/Basic/EVEvent?pageRows=999")
        items = (data.get("data") if isinstance(data, dict) else data) or []
        print(f"got {len(items)} events, computing targets...", flush=True)
        targets = [(str(it.get("id")), it.get("name") or "", ((it.get("creatorEntity") or {}).get("value")) or "")
                   for it in items
                   if is_A(str(it.get("id")), it.get("name") or "", ((it.get("creatorEntity") or {}).get("value")) or "")]
        print(f"targets to delete = {len(targets)}", flush=True)
        log = io.open(LOG, "w", encoding="utf-8")
        ok = fail = 0
        for i, (pk, nm, who) in enumerate(targets, 1):
            try:
                ops.api_call(pg, "DELETE", f"/reventmodule/Entity/EVEvent/{pk}")
                ok += 1
                log.write(f"OK  {pk} | {nm}\n"); log.flush()
            except Exception as e:
                fail += 1
                log.write(f"ERR {pk} | {nm} | {str(e)[:150]}\n"); log.flush()
            if i % 20 == 0:
                print(f"  ...{i}/{len(targets)} (ok={ok} fail={fail})", flush=True)
        log.write(f"\n總計 目標={len(targets)} 成功={ok} 失敗={fail}\n")
        log.close()
        b.close()
        print(f"DELETE done target={len(targets)} ok={ok} fail={fail}", flush=True)
except Exception:
    print("FATAL ERROR:", flush=True)
    traceback.print_exc()

