# -*- coding: utf-8 -*-
"""壓測前自我修復：確保活動「每人總報名上限」為 0（否則報名會 400）。
被各 run bat 於執行前呼叫。token 從同目錄 token.txt 讀取。"""
import io, os, json, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
token = io.open(os.path.join(HERE, "token.txt"), encoding="utf-8").read().strip()
BASE = "https://qa-khcg-ai.foxconn.com"
EVENT = "34185325523320832"
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
