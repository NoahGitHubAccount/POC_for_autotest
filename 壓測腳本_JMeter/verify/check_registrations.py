# -*- coding: utf-8 -*-
"""查壓測活動的實際報名記錄，結果寫入本目錄 registrations.txt（不含 token）。
token 從 ..\\shared\\token.txt 讀取。

受測站與活動由環境變數帶入：LOADTEST_BASE_URL、LOADTEST_EVENT_PKID。
"""
import io, os, json, urllib.request, datetime
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(HERE, "..", "shared", "token.txt")
OUT_PATH = os.path.join(HERE, "registrations.txt")

token = io.open(TOKEN_PATH, encoding="utf-8").read().strip()
H = {"Authorization": "Bearer " + token}
BASE = os.environ.get("LOADTEST_BASE_URL", "https://<受測站 host>")
EVENT = os.environ.get("LOADTEST_EVENT_PKID", "REPLACE_ME")

out = io.open(OUT_PATH, "w", encoding="utf-8")
out.write("查詢時間: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
try:
    url = f"{BASE}/reventmodule/Basic/EVRegistration?eVEventIds={EVENT}&pageRows=999"
    with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=30) as r:
        data = json.loads(r.read().decode())
    items = data.get("data") or []
    out.write(f"報名總筆數: {data.get('totalRows')}\n")
    src_counter = Counter()
    for it in items:
        src_counter[it.get("registrationSource") or "(空)"] += 1
    out.write("\n依來源(registrationSource):\n")
    for k, v in src_counter.most_common():
        out.write(f"  {k}: {v} 筆\n")
    out.write("\n最近 10 筆:\n")
    for it in items[:10]:
        out.write(f"  id={it.get('id')} source={it.get('registrationSource')} created={it.get('createdDate')}\n")
    out.write("STATUS: OK\n")
    print(f"查詢完成，共 {data.get('totalRows')} 筆，已寫入 registrations.txt")
except urllib.error.HTTPError as e:
    out.write(f"STATUS: HTTP {e.code} (token 可能過期，請重取)\n")
    print(f"查詢失敗 HTTP {e.code}")
out.close()
