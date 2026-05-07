"""pytest 全域設定：提供 config fixture 與 storageState 注入。"""
from __future__ import annotations
import pytest
from lib.auth import (
    DEFAULT_ROLE,
    has_fresh_session,
    load_session_storage_init_script,
    storage_path,
)
from lib.config_loader import load_config

# 註冊 md_reporter 為 pytest plugin
pytest_plugins = ("lib.md_reporter",)


@pytest.fixture(scope="session")
def config() -> dict:
    return load_config()


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, config):
    cfg = config
    args = dict(browser_context_args)
    vp = cfg.get("browser", {}).get("viewport", {})
    if vp:
        args["viewport"] = {"width": vp["width"], "height": vp["height"]}

    role = DEFAULT_ROLE
    if has_fresh_session(role, cfg["captcha"]["session_max_age_min"]):
        args["storage_state"] = str(storage_path(role))
    return args


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args, config):
    args = dict(browser_type_launch_args)
    args["headless"] = not config.get("browser", {}).get("headed", True)
    sm = config.get("browser", {}).get("slow_mo_ms", 0)
    if sm:
        args["slow_mo"] = sm
    return args


@pytest.fixture(scope="session")
def authenticated(config):
    """確保有有效 session；若無，提示先跑 warm-login 並失敗。"""
    if not has_fresh_session(DEFAULT_ROLE, config["captcha"]["session_max_age_min"]):
        pytest.fail(
            "找不到有效的 session（.auth/admin.json 不存在或已過期）。\n"
            "請先執行：python tools/run.py --warm-login"
        )
    return True


@pytest.fixture(scope="function", autouse=True)
def _restore_session_storage(context, authenticated):
    """每個測試的 context 注入 init script，把 sessionStorage 還原。

    Playwright 1.48 的 storage_state 不抓 sessionStorage；warm-login 另存一份，
    這裡用 add_init_script 在每個 page navigate 前還原。
    """
    script = load_session_storage_init_script(DEFAULT_ROLE)
    if script:
        context.add_init_script(script)
    yield


@pytest.fixture
def report_attach(request):
    """測試案例呼叫此 fixture 將 expected/actual/url 附到 item 供 reporter 使用。"""
    def _attach(*, expected: str | None = None, actual: str | None = None, url: str | None = None):
        node = request.node
        if expected is not None:
            node._expected = expected
        if actual is not None:
            node._actual = actual
        if url is not None:
            node._last_url = url
    return _attach
