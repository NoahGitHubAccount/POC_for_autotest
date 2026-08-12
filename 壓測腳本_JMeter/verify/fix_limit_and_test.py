# -*- coding: utf-8 -*-
"""診斷+修復 T3 報名 400：查活動規則 -> 若每人總上限>0 改成0 -> 試報一筆確認。
結果寫入本目錄 diag.txt（不含 token）。token 從 ..\\shared\\token.txt 讀取。

受測站、活動、表單欄位與場次皆由環境變數帶入（避免真實 ID 進版控）：
  LOADTEST_BASE_URL / LOADTEST_EVENT_PKID / LOADTEST_FORM_FIELD_PKID / LOADTEST_SESSION_PKID
"""
import io, os, json, urllib.request, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
token = io.open(os.path.join(HERE, "..", "shared", "token.txt"), encoding="utf-8").read().strip()
H = {"Authorization": "Bearer " + token}
HJ = {**H, "Content-Type": "application/json"}
BASE = os.environ.get("LOADTEST_BASE_URL", "https://<受測站 host>")
EVENT = os.environ.get("LOADTEST_EVENT_PKID", "REPLACE_ME")
FORM_FIELD = os.environ.get("LOADTEST_FORM_FIELD_PKID", "REPLACE_ME")
SESSION_ID = os.environ.get("LOADTEST_SESSION_PKID", "REPLACE_ME")
out = io.open(os.path.join(HERE, "diag.txt"), "w", encoding="utf-8")
def w(s): out.write(s + "\n"); print(s)

def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=HJ if body is not None else H, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

w("診斷時間: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
try:
    st, body = call("GET", f"/reventmodule/Basic/EVEventRule?eVEventIds={EVENT}")
    rule = (json.loads(body).get("data") or [None])[0]
    rid = rule["id"]
    w(f"1. 規則 id={rid}")
    w(f"   perPersonTotalLimit(每人總上限) = {rule.get('perPersonTotalLimit')}")
    w(f"   perPersonDailyLimit(每人每日上限) = {rule.get('perPersonDailyLimit')}")

    if rule.get("perPersonTotalLimit") not in (0, None):
        st, body = call("PATCH", "/reventmodule/Entity/EVEventRule",
                        {"id": rid, "perPersonTotalLimit": 0})
        w(f"2. 上限不是0，已PATCH成0 -> HTTP {st}")
    else:
        w("2. 上限已是0/None，無需修改")

    # 試報一筆
    st, body = call("POST", "/reventmodule/Entity/EVRegistration", {
        "evEventEntity": {"key": EVENT},
        "evRegistrationDatas": [{"evFormFieldEntity": {"key": FORM_FIELD}, "value": "1"}],
        "evEventSessions": [{"key": SESSION_ID}],
        "registrationSource": "LoadTest"})
    if st == 200:
        w(f"3. 試報一筆 -> 200 成功 id={json.loads(body).get('id')}")
        w("   結論：已修復，可以重跑壓測")
    else:
        w(f"3. 試報一筆 -> {st}  訊息：{body[:300]}")
        w("   結論：400 原因如上，需進一步處理")
    w("STATUS: OK")
except urllib.error.HTTPError as e:
    w(f"STATUS: HTTP {e.code} (token 可能過期，請重取)")
out.close()
