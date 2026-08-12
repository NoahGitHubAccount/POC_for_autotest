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


def pytest_addoption(parser):
    parser.addoption("--env", default=None, help="目標環境：dev | test | prod | local（預設讀 TEST_ENV 環境變數）")
    parser.addoption("--include-frozen", action="store_true", default=False,
                     help="連已定版（凍結）案例一起跑（回歸用；預設凍結案例自動跳過）")


def _load_frozen_nodeids() -> set[str]:
    """讀取定版凍結清單（reports/final/frozen_tests.txt，# 開頭為註解）。"""
    from pathlib import Path
    frozen_file = Path(__file__).parent / "reports" / "final" / "frozen_tests.txt"
    if not frozen_file.exists():
        return set()
    return {
        line.strip()
        for line in frozen_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }


def pytest_collection_modifyitems(config, items):
    """已定版案例自動 deselect（定版清單見 reports/final/frozen_tests.txt）；--include-frozen 可強制全跑。"""
    if config.getoption("--include-frozen"):
        return
    frozen = _load_frozen_nodeids()
    if not frozen:
        return
    kept, dropped = [], []
    for item in items:
        # nodeid 可能帶參數尾碼 [chromium]，凍結清單存「不含參數」形式，前綴比對
        base = item.nodeid.split("[", 1)[0]
        (dropped if base in frozen else kept).append(item)
    if dropped:
        config.hook.pytest_deselected(items=dropped)
        items[:] = kept


@pytest.fixture(scope="session")
def config(request) -> dict:
    env = request.config.getoption("--env") or None
    return load_config(env=env)


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
    """確保有有效 session；若無，skip 提示先跑 warm-login。

    用 skip 而非 fail：xfail 標記會把 setup 的 Failed 吞成「假 xfail」
    （2026-07-13 兩度事故——過期 session 被記成 xfail、圖文不符）；skip 優先權高於 xfail。
    """
    if not has_fresh_session(DEFAULT_ROLE, config["captcha"]["session_max_age_min"]):
        pytest.skip(
            "找不到有效的 session（.auth/admin.json 不存在或已過期）。"
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
def snap(request):
    """一案多圖：測試中途對指定 page 拍快照入報告（跨頁/前後台對照案每個關鍵畫面各拍一張）。

    用法：snap(page, "前台資訊頁") / snap(admin_page, "後台編輯頁")
    """
    from lib.md_reporter import snap_page

    def _snap(page, label: str):
        return snap_page(request.node, page, label)
    return _snap


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
