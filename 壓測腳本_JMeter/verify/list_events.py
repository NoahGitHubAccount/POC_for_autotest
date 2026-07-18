# -*- coding: utf-8 -*-
"""列舉後台所有活動（pkid/名稱/建立者/建立時間/狀態），寫入本目錄 events.txt（不含 token）。
供人工審查哪些是自動化測試產物、該刪哪些。token 從 ..\\shared\\token.txt 讀取。"""
import io, os, json, urllib.request, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
token = io.open(os.path.join(HERE, "..", "shared", "token.txt"), encoding="utf-8").read().strip()
H = {"Authorization": "Bearer " + token}
BASE = "https://qa-khcg-ai.foxconn.com"
OUT = os.path.join(HERE, "events.txt")

# 自動化測試命名特徵（僅作標記提示，最終由人工審查）
import re
AUTO_HINTS = [r"_copy", r"^IT0?\d", r"^PROBE_", r"^LoadTest_", r"永"]
KEEP = {"34185325523320832", "34155861376110592", "34168368758263808"}

def is_auto(name):
    return any(re.search(p, name or "") for p in AUTO_HINTS)

out = io.open(OUT, "w", encoding="utf-8")
def w(s): out.write(s + "\n")

w("查詢時間: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
try:
    url = f"{BASE}/reventmodule/Basic/EVEvent?pageRows=999"
    with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60) as r:
        data = json.loads(r.read().decode())
    items = data.get("data") or []
    w(f"活動總數: {data.get('totalRows')}\n")
    # 排序：建立時間
    items.sort(key=lambda it: it.get("createdDate") or "")
    w(f"{'標記':4} | {'pkid':18} | {'建立時間':19} | {'狀態':4} | 建立者 | 名稱")
    w("-" * 100)
    for it in items:
        pkid = str(it.get("id"))
        name = it.get("name") or ""
        created = (it.get("createdDate") or "")[:19]
        status = str(it.get("statusId") or it.get("status") or "")
        creator = ((it.get("creatorEntity") or {}).get("value")) or ""
        if pkid in KEEP:
            mark = "留存"
        elif is_auto(name):
            mark = "★候選"
        else:
            mark = ""
        w(f"{mark:4} | {pkid:18} | {created:19} | {status:4} | {creator} | {name}")
    w("\nSTATUS: OK")
    print(f"完成，共 {data.get('totalRows')} 筆活動，已寫入 events.txt")
except urllib.error.HTTPError as e:
    w(f"STATUS: HTTP {e.code} (token 可能過期，請重取)")
    print(f"查詢失敗 HTTP {e.code}")
out.close()
