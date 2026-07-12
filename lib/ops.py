"""活動建立操作層（ops）— AI 操作受測系統的已驗證原語集。

目的：任何測試案例都能用這些原語組裝出「建立活動」的任意流程，
不必重新探勘 DOM。每個操作標注驗證日期；未驗證者明確標 [待驗證]。

來源整併（2026-07-08）：
  tests/integration/_shared_create.py  → datepicker / 上傳 / PATCH API / 填值
  tests/integration/_shared.py         → 儲存 / toast
  tests/2-3-2-2~4 */_shared.py         → 分組啟用（三份變體通用化）
  tests/2-3-8~9 */_shared.py           → tab 切換

DOM 事實對照表：docs/dom_facts/EVEventEdit.md、docs/dom_facts/EventList.md
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from playwright.sync_api import Page

from lib.selectors import EVEventEditPage, EventListPage

# ════════════════════════════════════════════════════════════════════════════
# 欄位 ID 常數（2026-06-06 live DOM 確認）
# ════════════════════════════════════════════════════════════════════════════

F_NAME          = "ActivityInfo_Introduction_name"
F_LOCATION      = "ActivityInfo_Introduction_locationName"
F_TYPE          = "ActivityInfo_Introduction_type"
F_START         = "ActivityInfo_Introduction_startTime"
F_END           = "ActivityInfo_Introduction_endTime"
F_PUB_START     = "ActivityInfo_Introduction_publishStartTime"
F_PUB_END       = "ActivityInfo_Introduction_publishEndTime"
F_REG_OPEN      = "ActivityRules_OpenRegistrationTime_registrationOpenFrom"
F_REG_CLOSE     = "ActivityRules_OpenRegistrationTime_registrationCloseTo"
F_INTRO         = "ActivityInfo_Introduction_intro"
F_EXT_TEXT      = "ActivityInfo_Introduction_externalLinkText"
F_EXT_URL       = "ActivityInfo_Introduction_externalLinkUrl"
F_BANNER_PC     = "ActivityInfo_Introduction_bannerPC"
F_BANNER_MOBILE = "ActivityInfo_Introduction_bannerMobile"
F_REG_METHOD    = "ActivityInfo_RegistrationMethod_regMethod"

ANCHOR_INFO  = "ActivityMgmt_ActivityInfo"
ANCHOR_RULE  = "ActivityMgmt_ActivityRule"
ANCHOR_REG_F = "ActivityMgmt_RegistrationFieldSetting"
ANCHOR_CERT  = "ActivityMgmt_CertificateManagement"

_SEC_GROUP = "ActivityRules_GroupManagement"

# 月份中文對照（datepicker 顯示「六月」等）
_MONTH_ZH = ["一月", "二月", "三月", "四月", "五月", "六月",
             "七月", "八月", "九月", "十月", "十一月", "十二月"]


# ════════════════════════════════════════════════════════════════════════════
# 導航（驗證日期：2026-06-07 CREATE 三案例）
# ════════════════════════════════════════════════════════════════════════════

def create_draft(page: Page, base_url: str) -> str:
    """從活動列表點「新增」，等 auto-save 產生草稿，回傳 pkid。"""
    page.goto(base_url + EventListPage.PATH, wait_until="domcontentloaded")
    EventListPage.reset_button(page).wait_for(state="visible", timeout=15_000)
    page.wait_for_timeout(800)
    EventListPage.create_button(page).click()
    page.wait_for_url("**/EVEventEdit/**", timeout=15_000)
    page.wait_for_timeout(2_500)
    m = re.search(r"pkid=(\d+)", page.url)
    if not m:
        raise RuntimeError(f"草稿建立後 URL 無 pkid：{page.url}")
    return m.group(1)


def open_edit(page: Page, base_url: str, pkid: str) -> None:
    """開啟活動編輯頁；先過列表頁建立瀏覽歷史（router.back 安全，見 99 經驗 2026-05-18）。"""
    page.goto(base_url + EventListPage.PATH, wait_until="domcontentloaded")
    page.wait_for_timeout(500)
    EVEventEditPage.open_direct(page, base_url, pkid)
    page.wait_for_timeout(1_000)


def scroll_to_anchor(page: Page, anchor: str) -> None:
    el = page.locator(f"[data-anchor='{anchor}']")
    try:
        el.scroll_into_view_if_needed(timeout=10_000)
    except Exception:
        pass
    page.wait_for_timeout(600)


# ════════════════════════════════════════════════════════════════════════════
# 基本資訊 — API 直寫（驗證日期：2026-07-08）
# ════════════════════════════════════════════════════════════════════════════

# 頁面 JS context 內執行 PATCH /reventmodule/Entity/EVEvent。
# 線路事實（2026-07-08 網路擷取 app 自身 autosave 請求確認）：
#   - body 是「扁平物件」，不包 wMAEVEvent（service 那層的包裝在序列化前被攤平）
#   - 不需 evMainEventEntity（草稿即可存；當初 400「必須指定子活動」是被 wMAEVEvent 包裝觸發）
#   - token 走 sessionStorage.backendtoken.access_token + Authorization: Bearer
_PATCH_EVENT_JS = """async ({pkid, fields}) => {
    let token = null;
    try {
        const raw = sessionStorage.getItem('backendtoken');
        if (raw && raw !== 'null') token = (JSON.parse(raw) || {}).access_token;
    } catch (_e) {}
    const headers = {'Content-Type': 'application/json'};
    if (token) headers['Authorization'] = 'Bearer ' + token;

    const p = await fetch('/reventmodule/Entity/EVEvent', {
        method: 'PATCH', headers, credentials: 'include',
        body: JSON.stringify(fields)   // 扁平 body，與 app autosave 一致
    });
    let pData = null;
    try { pData = await p.json(); } catch (_e) {}
    return { ok: p.ok, phase: 'PATCH', status: p.status,
             body: JSON.stringify(pData), hadToken: !!token };
}"""

def patch_event_info(
    page: Page,
    pkid: str,
    name: str,
    location: str = "",
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    publish_start: datetime | None = None,
    publish_end: datetime | None = None,
    ext_text: str = "",
    ext_url: str = "",
) -> dict:
    """直接 PATCH /reventmodule/Entity/EVEvent 儲存活動基本資訊。

    根本原因：Playwright keyboard 事件不觸發 Vue dirty tracking，
    「儲存變更」按鈕因此不送 PATCH（dirty set 為空）。改用 page.evaluate(fetch) 呼叫後端。

    驗證日期：2026-07-08（比對 app 自身 autosave 網路請求後修正）。兩個關鍵：
      1. Authorization: Bearer <sessionStorage.backendtoken.access_token>（否則 401）
      2. body 為扁平物件、不包 wMAEVEvent、不需 evMainEventEntity（否則 400）
    endpoint 來源：擷取 app 於 name 欄位 Tab blur 時的 autosave PATCH 請求。
    """

    def _iso(dt: datetime | None) -> str | None:
        return dt.isoformat() if dt else None

    fields = {
        "id": pkid,
        "name": name,
        "location": location,
        "startTime": _iso(start_time),
        "endTime": _iso(end_time),
        "publishStartTime": _iso(publish_start),
        "publishEndTime": _iso(publish_end),
        "externalLinkText": ext_text,
        "externalLinkUrl": ext_url,
    }

    result = page.evaluate(_PATCH_EVENT_JS, {"pkid": pkid, "fields": fields})

    if not result.get("ok"):
        raise RuntimeError(
            f"patch_event_info 失敗（{result.get('phase')}）: status={result.get('status')}, "
            f"hadToken={result.get('hadToken')}, body={result.get('body')}"
        )
    return result


# ════════════════════════════════════════════════════════════════════════════
# 基本資訊 — UI 操作（驗證日期：2026-06-06 live DOM）
# ════════════════════════════════════════════════════════════════════════════

def upload_image(page: Page, field_id: str, image_path: str | Path,
                 timeout_ms: int = 30_000) -> None:
    """上傳圖片到 banner 欄位（隱藏 file input 直接 set_input_files），等「上傳成功!」。

    ⚠️ 已知 blocker（2026-07-08）：新建草稿頁的 banner 區塊為懶載入，
    field container 可能不在 DOM。需先 dom_probe 一頁 HTML 確認 banner 區塊
    的展開條件（tab？accordion？活動類型？），回填 docs/dom_facts/EVEventEdit.md 後再修。
    """
    container = page.locator(f"[data-field-id='{field_id}']").first
    try:
        container.wait_for(state="attached", timeout=8_000)
        container.scroll_into_view_if_needed(timeout=5_000)
    except Exception as e:
        raise RuntimeError(
            f"upload_image: 找不到 banner 欄位容器 [data-field-id='{field_id}']。"
            f"新草稿頁圖片區塊為懶載入，需先確認展開條件（見 docs/dom_facts/EVEventEdit.md 待確認段）。"
            f"原始錯誤：{e}"
        ) from e
    container.locator("input[type='file']").first.set_input_files(str(image_path))
    container.get_by_text("上傳成功!", exact=False).first.wait_for(
        state="visible", timeout=timeout_ms
    )
    page.wait_for_timeout(300)


def click_datepicker(page: Page, field_id: str, target: datetime) -> None:
    """透過月曆 UI 選取日期和時間（QA 環境 keyboard 輸入無效）。

    DOM 事實（2026-06-06）：panel teleport 到 body，selector `.p-datepicker-panel`。
    """
    inp = page.locator(f"[data-field-id='{field_id}'] input.p-datepicker-input").first
    inp.scroll_into_view_if_needed(timeout=5_000)
    inp.click(timeout=5_000)
    page.wait_for_timeout(600)

    panel = page.locator(".p-datepicker-panel").first
    panel.wait_for(state="visible", timeout=5_000)

    _navigate_to_month(page, panel, target.year, target.month)

    panel.locator(
        f"td[aria-label='{target.day}']:not([data-p-other-month='true']) "
        f"span[data-pc-section='day']"
    ).first.click(timeout=5_000)
    page.wait_for_timeout(200)

    _set_time_unit(page, panel, target.hour,
                   "[data-pc-section='hourpicker'] button[aria-label='下一個小時']",
                   "[data-pc-section='hourpicker'] button[aria-label='上一個小時']",
                   "[data-pc-section='hourpicker'] span[data-pc-section='hour']")
    _set_time_unit(page, panel, target.minute,
                   "[data-pc-section='minutepicker'] button[aria-label='下一分鐘']",
                   "[data-pc-section='minutepicker'] button[aria-label='上一分鐘']",
                   "[data-pc-section='minutepicker'] span[data-pc-section='minute']")

    page.keyboard.press("Escape")
    page.wait_for_timeout(300)


def _navigate_to_month(page: Page, dp, target_year: int, target_month: int) -> None:
    """點 prev/next 讓月曆顯示到目標年月，最多導航 36 個月。"""
    for _ in range(36):
        year_text = dp.locator("button[data-pc-section='selectyear']").first.inner_text(timeout=3_000).strip()
        month_text = dp.locator("button[data-pc-section='selectmonth']").first.inner_text(timeout=3_000).strip()
        cur_year = int(year_text)
        cur_month = _MONTH_ZH.index(month_text) + 1 if month_text in _MONTH_ZH else -1

        if cur_year == target_year and cur_month == target_month:
            return
        if (cur_year, cur_month) < (target_year, target_month):
            dp.locator("button[aria-label='下一個月']").first.click(timeout=3_000)
        else:
            dp.locator("button[aria-label='上一個月']").first.click(timeout=3_000)
        page.wait_for_timeout(150)

    raise RuntimeError(f"導航超過 36 個月仍未到達 {target_year}/{target_month}")


def _set_time_unit(page: Page, dp, target: int,
                   inc_sel: str, dec_sel: str, val_sel: str) -> None:
    """把小時或分鐘調到 target 值（最多 60 次點擊）。"""
    for _ in range(60):
        current_text = dp.locator(val_sel).first.inner_text(timeout=3_000).strip()
        try:
            current = int(current_text)
        except ValueError:
            break
        if current == target:
            return
        if current < target:
            dp.locator(inc_sel).first.click(timeout=3_000)
        else:
            dp.locator(dec_sel).first.click(timeout=3_000)
        page.wait_for_timeout(80)


def fill_text_field(page: Page, field_id: str, value: str) -> None:
    """填 InputText 欄位（鍵盤模擬）。

    警告：不觸發 Vue dirty tracking，「儲存變更」不會送出此值；
    需持久化的欄位改用 patch_event_info()。
    """
    inp = page.locator(f"[data-field-id='{field_id}'] input").first
    inp.scroll_into_view_if_needed(timeout=5_000)
    inp.click(click_count=3, timeout=3_000)
    inp.press("Control+a")
    inp.press("Delete")
    inp.type(value)
    page.wait_for_timeout(200)


def fill_intro_field(page: Page, field_id: str, value: str) -> None:
    """填 contenteditable 活動介紹欄位（失敗靜默跳過）。"""
    try:
        editor = page.locator(f"[data-field-id='{field_id}'] [contenteditable='true']").first
        if editor.is_visible(timeout=2_000):
            editor.click()
            editor.fill(value)
            page.keyboard.press("Escape")
    except Exception:
        pass


def select_reg_method(page: Page, field_id: str, method_text: str) -> None:
    """點選報名方式選項（依文字）。注意：regMethod 實為 Quill editor（2026-06-07）。"""
    ctr = page.locator(f"[data-field-id='{field_id}']").first
    try:
        ctr.scroll_into_view_if_needed(timeout=5_000)
    except Exception:
        pass
    page.wait_for_timeout(300)
    ctr.get_by_text(method_text, exact=False).first.click()
    page.wait_for_timeout(300)


def read_field(page: Page, field_id: str) -> str:
    """讀 InputText 欄位當前值。"""
    return page.locator(f"[data-field-id='{field_id}'] input").first.input_value(timeout=5_000)


# ════════════════════════════════════════════════════════════════════════════
# 生命週期狀態活動製造（驗證日期：2026-07-11 IT-08 首跑；造法見 整合測試_前置準備.md）
# ════════════════════════════════════════════════════════════════════════════

# 頁面 context 內打任意 API（帶 token），與 _PATCH_EVENT_JS 同線路事實
_API_CALL_JS = """async ({method, url, body}) => {
    let token = null;
    try {
        const raw = sessionStorage.getItem('backendtoken');
        if (raw && raw !== 'null') token = (JSON.parse(raw) || {}).access_token;
    } catch (_e) {}
    const headers = {'Content-Type': 'application/json'};
    if (token) headers['Authorization'] = 'Bearer ' + token;
    const opt = {method, headers, credentials: 'include'};
    if (body) opt.body = JSON.stringify(body);
    const r = await fetch(url, opt);
    let data = null; try { data = await r.json(); } catch (_e) {}
    return {ok: r.ok, status: r.status, body: JSON.stringify(data)};
}"""

_STAGE_SOURCE_NAME = "大港閱冰"  # 複製來源：「2026大港閱冰冰品嘉年華」pkid=34155861376110592（保留勿刪）

# 各 stage 相對時間窗（start, end, regOpenFrom；後端 GetFieldEditRules 依時間優先序判定）
_STAGE_WINDOWS = {
    "pre_open":          (10, 12, 5),
    "registration_open": (10, 12, -1),
    "in_progress":       (-1, 2, -3),
    "ended":             (-5, -1, -7),
}


def api_call(page: Page, method: str, url: str, body: dict | None = None) -> dict:
    """在頁面 context 內帶 token 打 API；非 2xx 直接 raise。頁面須已落地 app（見 goto_app）。"""
    r = page.evaluate(_API_CALL_JS, {"method": method, "url": url, "body": body})
    if not r.get("ok"):
        raise RuntimeError(f"{method} {url} 失敗 status={r['status']} body={r['body'][:300]}")
    return json.loads(r["body"]) if r.get("body") not in (None, "null") else {}


def _api_items(data) -> list:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data") or data.get("items") or []
    return []


def goto_app(page: Page, base_url: str) -> None:
    """落地活動列表頁，讓後續 api_call 有 origin + token。"""
    page.goto(base_url + EventListPage.PATH, wait_until="domcontentloaded")
    page.wait_for_timeout(800)


def find_event_pkid(page: Page, name_substr: str, exclude: tuple[str, ...] = ("_copy",)) -> str:
    """全列表客戶端過濾找活動 pkid（List 的 name 查詢參數為精確比對，子字串查不到）。"""
    data = api_call(page, "GET", "/reventmodule/List/EVEvent?pageRows=500")
    for it in _api_items(data):
        name = str(it.get("value") or it.get("name") or "")
        if name_substr in name and not any(x in name for x in exclude):
            return str(it.get("key") or it.get("id"))
    raise RuntimeError(f"列表查無「{name_substr}」活動")


def clone_event(page: Page, src_pkid: str) -> str:
    """POST Clone 複製活動（名稱自動加 _copy 尾碼），回傳新 pkid。"""
    data = api_call(page, "POST", f"/reventmodule/Clone/EVEvent/{src_pkid}")
    pkid = (data or {}).get("id") or (_api_items(data)[0].get("id") if _api_items(data) else None)
    if not pkid:
        raise RuntimeError(f"Clone 回應無 id：{json.dumps(data, ensure_ascii=False)[:300]}")
    return str(pkid)


def set_registration_open(page: Page, pkid: str, reg_dt: datetime) -> None:
    """從活動 detail 取 rule id，PATCH registrationOpenFrom。

    ⚠ registrationOpenRule 為 VMKeyValue（送字串會 400 "view required"）。
    """
    det = api_call(page, "GET", f"/reventmodule/Entity/EVEvent/{pkid}")
    rules = (det or {}).get("evEventRules") or []
    if not rules:
        rules = _api_items(api_call(page, "GET", f"/reventmodule/Entity/EVEventRule?EVEventId={pkid}"))
    if not rules:
        raise RuntimeError(f"活動 {pkid} 無 rule（複製品應帶既有 rule）")
    rule_id = rules[0].get("id") or rules[0].get("pkid")
    api_call(page, "PATCH", "/reventmodule/Entity/EVEventRule",
             {"id": rule_id,
              "registrationOpenRule": {"key": "SpecificDateTime"},
              "registrationOpenFrom": reg_dt.astimezone().isoformat()})


def make_stage_event(page: Page, base_url: str, stage: str, name_prefix: str = "STAGE",
                     keep_source_times: bool = False) -> str:
    """複製大港閱冰並調成指定生命週期 stage（pre_open/registration_open/in_progress/ended），
    回傳新活動 pkid（已啟用）。disabled 直接用 create_draft() 即可，不走此函式。

    keep_source_times=True：不 PATCH 活動時間窗（保留來源活動自洽的場次/報到/曝光時間，
    供需要「儲存能通過時間驗證」的 UI 測試；stage 由來源時窗與 regOpen 自然決定，呼叫端須自驗）。
    調過時間窗的複製品，場次/報到時間會與新窗矛盾，編輯頁儲存必被時間驗證擋下。
    """
    if stage not in _STAGE_WINDOWS:
        raise ValueError(f"stage 必須是 {list(_STAGE_WINDOWS)}，收到 {stage!r}")
    d_start, d_end, d_reg = _STAGE_WINDOWS[stage]
    now = datetime.now().astimezone()
    goto_app(page, base_url)
    pkid = clone_event(page, find_event_pkid(page, _STAGE_SOURCE_NAME))
    fields = {"id": pkid, "name": f"{name_prefix}_{stage}_{now:%m%d%H%M%S}"}
    if not keep_source_times:
        start, end = now + timedelta(days=d_start), now + timedelta(days=d_end)
        # 曝光窗同步調整（曝光結束須 ≥ 活動結束，否則編輯頁存檔會被曝光驗證先擋住）
        fields.update({"startTime": start.isoformat(), "endTime": end.isoformat(),
                       "publishStartTime": (start - timedelta(days=20)).isoformat(),
                       "publishEndTime": (end + timedelta(days=5)).isoformat()})
    api_call(page, "PATCH", "/reventmodule/Entity/EVEvent", fields)
    set_registration_open(page, pkid, now + timedelta(days=d_reg))
    api_call(page, "PATCH", f"/reventmodule/List/EVEvent/{pkid}/Status", {"status": {"key": "2"}})
    return pkid


def get_field_edit_rules(page: Page, pkid: str) -> dict:
    """GET FieldEditRules：回 editableStage 與 77 欄 fieldMeta。"""
    return api_call(page, "GET", f"/reventmodule/Action/EVEvent/{pkid}/FieldEditRules")


#: 報名欄位模板 id（GET /reventmodule/Template/EVFormField/{eventId} 實測，2026-07-12）
FORM_FIELD_TEMPLATES = {"姓名": "1", "手機號碼": "2", "生理性別": "3", "行政區": "4",
                        "生日": "5", "聯絡地址": "6", "電子郵件": "7", "身分證字號": "8"}


def add_registrant_field(page: Page, pkid: str, template_name: str,
                         required: bool = False) -> str:
    """從模板複製一個報名者欄位到活動（B6 多欄位活動造態），回傳新欄位 id。

    Copy 回傳的 id 是模板 id 非新欄位 id；實際 id 需 GET Event/EVFormField 反查。
    isRequired 的 PATCH 必須帶 evEventEntity 連結否則 404「指定的活動報名表不存在」。
    """
    tid = FORM_FIELD_TEMPLATES[template_name]
    api_call(page, "POST", "/reventmodule/Template/EVFormField/Copy",
             {"id": tid, "eventId": pkid, "groupSeqNo": "1",
              "category": "Registration", "fieldGroup": "Registrant"})
    ex = api_call(page, "GET", f"/reventmodule/Event/EVFormField/{pkid}")
    items = ex if isinstance(ex, list) else (ex.get("data") or [])
    fid = next(str(it["id"]) for it in items if it.get("name") == template_name)
    if required:
        api_call(page, "PATCH", "/reventmodule/Basic/EVFormField",
                 {"id": fid, "isRequired": True, "evEventEntity": {"key": pkid}})
    return fid


def patch_session_times(page: Page, pkid: str, times_by_index: dict[int, tuple[datetime, datetime]]) -> None:
    """改指定場次（evEventNodes，依序號索引）的起迄時間。

    ⚠ EVEvent 巢狀 PATCH 的 evEventNodes 是**整集合置換**：只傳部分場次會刪掉未傳的
    （2026-07-12 IT-10 實測，7 場剩 1 場）。故一律全量帶 {id}，僅目標場次帶新時間；
    未改場次帶 {id} 即保留原欄位。EVEventNode 單獨 PATCH/PUT 皆 405。
    """
    ent = api_call(page, "GET", f"/reventmodule/Entity/EVEvent/{pkid}")
    payload = []
    for i, nd in enumerate(ent.get("evEventNodes") or []):
        item: dict = {"id": nd["id"]}
        if i in times_by_index:
            st, en = times_by_index[i]
            item.update({"startTime": st.isoformat(), "endTime": en.isoformat()})
        payload.append(item)
    api_call(page, "PATCH", "/reventmodule/Entity/EVEvent", {"id": pkid, "evEventNodes": payload})


# ════════════════════════════════════════════════════════════════════════════
# 分組管理（驗證日期：2026-05-20；三工項變體通用化）
# ════════════════════════════════════════════════════════════════════════════

# basis → (checkbox input value, 就緒訊號)
_GROUPING_READY = {
    "Area":    lambda page: page.locator(f"[data-field-id='{_SEC_GROUP}_areaList']").is_visible(),
    "Session": lambda page: page.get_by_text("新增場次", exact=True).count() > 0,  # sessionList 無 field-id
    "Section": lambda page: page.locator(f"[data-field-id='{_SEC_GROUP}_sectionList']").is_visible(),
}


def enable_grouping(page: Page, basis: str) -> None:
    """啟用「需要分組」並勾選分組依據，等清單區塊展開。

    basis：'Area'（區域/入口）/ 'Session'（場次）/ 'Section'（組別）。
    冪等：已啟用直接 return，避免點擊觸發 Vue re-eval 或誤 uncheck。
    """
    if basis not in _GROUPING_READY:
        raise ValueError(f"basis 必須是 {list(_GROUPING_READY)}，收到 {basis!r}")

    scroll_to_anchor(page, ANCHOR_RULE)
    if _GROUPING_READY[basis](page):
        return

    field_j = EVEventEditPage.field_container(page, f"{_SEC_GROUP}_isGroupingRequired")
    field_j.get_by_text("需要", exact=True).first.click()
    page.wait_for_timeout(800)

    field_l = EVEventEditPage.field_container(page, f"{_SEC_GROUP}_groupingBasis")
    try:
        field_l.scroll_into_view_if_needed(timeout=5_000)
        page.wait_for_timeout(500)
    except Exception:
        pass

    # PrimeVue checkbox 需點 input（force=True 穿透視覺隱藏）；先查勾選態防誤 uncheck
    basis_input = field_l.locator(f"input[value='{basis}']")
    if not basis_input.is_checked():
        basis_input.click(force=True)

    # STGroupManage 初始化較慢，輪詢就緒訊號
    for _ in range(15):
        if _GROUPING_READY[basis](page):
            return
        page.wait_for_timeout(1_000)
    raise RuntimeError(f"enable_grouping({basis!r}) 15 秒內清單區塊未展開")


def add_session(page: Page, **kwargs) -> None:
    """[待驗證] 點「新增場次」並填寫場次表單。

    2-3-2-3 只驗證過入口存在（「新增場次」為 <div>）；
    對話框/表單內部 DOM 未探勘。實作前先跑 dom_probe：
        click text:新增場次 → buttons / fields / html
    探勘結論回填 docs/dom_facts/EVEventEdit.md 後再實作本函式。
    """
    raise NotImplementedError("add_session 待 dom_probe 探勘場次表單 DOM 後實作")


# ════════════════════════════════════════════════════════════════════════════
# Tab 切換（驗證日期：2026-05-15；PrimeVue lazy render）
# ════════════════════════════════════════════════════════════════════════════

def open_tab(page: Page, tab_text: str) -> None:
    """切換 tab（報名欄位設定 / 憑證與報到管理…）；filter(has_text) 避開 SVG 污染 accessible name。"""
    page.locator("[role='tab']").filter(has_text=tab_text).first.click()
    page.wait_for_timeout(1_000)  # lazy render，等 panel 進 DOM


# ════════════════════════════════════════════════════════════════════════════
# 儲存（驗證日期：2026-05-17）
# ════════════════════════════════════════════════════════════════════════════

def save(page: Page) -> bool:
    """點「儲存變更」，回傳是否出現 success toast。

    警告：只有 UI 操作觸發過 dirty tracking 的欄位會被送出；
    純 Playwright type 的欄位不算 dirty（改用 patch_event_info）。
    """
    EVEventEditPage.save_button(page).click()
    try:
        page.wait_for_selector(
            ".p-toast-message-success, [class*='toast'][class*='success']",
            state="visible", timeout=5_000,
        )
        return True
    except Exception:
        return False
