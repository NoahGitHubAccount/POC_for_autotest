# -*- coding: utf-8 -*-
"""壓測前自我修復：確保活動「每人總報名上限」為 0（否則報名會 400）。
被各 run bat 於執行前呼叫。token 從同目錄 token.txt 讀取。

受測站與活動不寫死，改由環境變數帶入（跑 bat 前先設定）：
  set LOADTEST_BASE_URL=https://<受測站 host>
  set LOADTEST_EVENT_PKID=<壓測活動 pkid>
"""
import io, os, json, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
token = io.open(os.path.join(HERE, "token.txt"), encoding="utf-8").read().strip()
BASE = os.environ.get("LOADTEST_BASE_URL", "https://<受測站 host>")
EVENT = os.environ.get("LOADTEST_EVENT_PKID", "REPLACE_ME")
H = {"Authorization": "Bearer " + token}
HJ = {**H, "Content-Type": "application/json"}
try:
    req = urllib.request.Request(BASE + f"/reventmodule/Basic/EVEventRule?eVEventIds={EVENT}", headers=H)
    rule = (json.loads(urllib.request.urlopen(req, timeout=30).read().decode()).get("data") or [None])[0]
    if rule.get("perPersonTotalLimit") not in (0, None):
        body = json.dumps({"id": rule["id"], "perPersonTotalLimit": 0}).encode()
        urllib.request.urlopen(urllib.request.Request(BASE + "/reventmodule/Entity/EVEventRule", data=body, headers=HJ, method="PATCH"), timeout=30)
        print("[ensure] perPersonTotalLimit 1->0 (fixed)")
    else:
        print("[ensure] perPersonTotalLimit already 0/None (OK)")
except Exception as e:
    print("[ensure] WARN: could not ensure limit:", e)
