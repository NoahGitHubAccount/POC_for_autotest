"""登入流程：支援 manual / bypass / reuse 三模式，含 storageState 重用。

設計原則：
- 互動式登入只在 warm_login 流程使用；測試本身一律靠 storageState。
- 如此可避免每個測試案例都觸發 CAPTCHA。
- Playwright 1.48 的 storage_state 不抓 sessionStorage，需另存後用 add_init_script 還原。
"""
from __future__ import annotations
import json
import time
from pathlib import Path
from playwright.sync_api import Page, BrowserContext

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUTH_DIR = PROJECT_ROOT / ".auth"
DEFAULT_ROLE = "admin"


def storage_path(role: str = DEFAULT_ROLE) -> Path:
    return AUTH_DIR / f"{role}.json"


def session_storage_path(role: str = DEFAULT_ROLE) -> Path:
    return AUTH_DIR / f"{role}.session.json"


def has_fresh_session(role: str, max_age_min: int) -> bool:
    p = storage_path(role)
    if not p.exists():
        return False
    age_sec = time.time() - p.stat().st_mtime
    return age_sec < max_age_min * 60


def perform_interactive_login(page: Page, config: dict, role: str = DEFAULT_ROLE) -> None:
    """互動式登入：填帳密後依 captcha.mode 處理驗證碼，等待 URL 跳轉。"""
    acc = config["accounts"][role]
    base_url = config["base_url"]
    entry_path = config["entry_path"]
    cap = config["captcha"]
    post_login = config["post_login_url_glob"]

    page.goto(base_url + entry_path)
    page.get_by_placeholder("請輸入帳號").fill(acc["username"])
    page.get_by_placeholder("請輸入密碼").fill(acc["password"])

    mode = cap["mode"]
    if mode == "bypass":
        page.get_by_placeholder("請輸入驗證碼").fill(cap.get("test_code", ""))
        page.get_by_role("button", name="登入").click()
    elif mode == "manual":
        print(
            "\n" + "=" * 64 + "\n"
            "[CAPTCHA] 請在瀏覽器中：\n"
            "  1. 手動輸入驗證碼\n"
            "  2. 點擊「登入」按鈕\n"
            "本程式會自動偵測登入成功（最長等 5 分鐘）\n"
            + "=" * 64 + "\n"
        )
    elif mode == "reuse":
        raise RuntimeError("captcha.mode=reuse 不應走互動登入流程；請改用既有 storageState")
    else:
        raise ValueError(f"未知 captcha.mode={mode}")

    page.wait_for_url(post_login, timeout=300_000)


def save_storage_state(context: BrowserContext, role: str = DEFAULT_ROLE) -> Path:
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    p = storage_path(role)
    context.storage_state(path=str(p))
    return p


def save_session_storage(page: Page, role: str = DEFAULT_ROLE) -> Path:
    """Dump 當前 page 的 sessionStorage（Playwright storage_state 不抓的部分）。"""
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    data = page.evaluate(
        "() => Object.fromEntries(Object.entries(sessionStorage))"
    )
    p = session_storage_path(role)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def prepare_authenticated_context(browser, role: str = DEFAULT_ROLE, **context_kwargs):
    """建立已注入 storage_state + sessionStorage init script 的 context。

    給 ad-hoc 工具腳本使用（pytest 流程走 conftest 不需此函式）。
    """
    sp = storage_path(role)
    if not sp.exists():
        raise FileNotFoundError(f"找不到 {sp}，請先跑 warm-login")
    ctx = browser.new_context(storage_state=str(sp), **context_kwargs)
    script = load_session_storage_init_script(role)
    if script:
        ctx.add_init_script(script)
    return ctx


def load_session_storage_init_script(role: str = DEFAULT_ROLE) -> str | None:
    """讀 session storage dump 並產生用於 add_init_script 的 JS 字串。"""
    p = session_storage_path(role)
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    if not data:
        return None
    payload = json.dumps(data, ensure_ascii=False)
    return (
        "(() => {"
        f"  const data = {payload};"
        "  for (const [k, v] of Object.entries(data)) {"
        "    try { sessionStorage.setItem(k, v); } catch (e) {}"
        "  }"
        "})();"
    )
