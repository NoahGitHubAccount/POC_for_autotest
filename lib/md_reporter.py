"""自製 pytest plugin：每葉節點工項一份 md 報告，每次執行一個 run 目錄。

報告含：
- 標頭：工項編號 / 標題 / 執行時間（YYYY-MM-DD HH:MM）
- 總覽表：每個 AC 案例的 PASSED/FAILED/SKIPPED + 耗時 + 截圖連結
- 失敗詳情：含 測試案例編號、工項編號、預期、實際、URL、附件路徑、inline 截圖
- 結果截圖（mode=always）：每個 case 的 inline 截圖

截圖模式（pytest CLI option）：
- `--shot=failed_only`（預設）：只在失敗時拍
- `--shot=always`：每個 test 都拍（最終交付用）
- `--shot=off`：完全不拍
"""
from __future__ import annotations
import datetime as _dt
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"

_RUN_ID_KEY = "_md_reporter_run_id"
_RESULTS_KEY = "_md_reporter_results"

SHOT_MODES = ("failed_only", "always", "off")


def pytest_addoption(parser):
    parser.addoption(
        "--shot",
        action="store",
        default="failed_only",
        choices=SHOT_MODES,
        help="截圖模式：failed_only（預設，只失敗拍）/ always（每個 test 都拍）/ off",
    )


def _shot_mode(config) -> str:
    return config.getoption("--shot")


def _run_id(session) -> str:
    rid = getattr(session.config, _RUN_ID_KEY, None)
    if rid is None:
        rid = _dt.datetime.now().strftime("%Y%m%d_%H%M")
        setattr(session.config, _RUN_ID_KEY, rid)
    return rid


def _run_dir(session) -> Path:
    return REPORTS_DIR / f"{_run_id(session)}_run"


def _results(session) -> list:
    r = getattr(session.config, _RESULTS_KEY, None)
    if r is None:
        r = []
        setattr(session.config, _RESULTS_KEY, r)
    return r


def _wbs_of(item) -> str:
    for m in item.iter_markers("wbs"):
        if m.args:
            return str(m.args[0])
    return "unmarked"


def _take_screenshot(item, outcome_str: str, run_dir: Path) -> str | None:
    """依 --shot 模式拍 page 截圖，回傳相對 md 報告的路徑（含 ./）。"""
    mode = _shot_mode(item.session.config)
    if mode == "off":
        return None
    if mode == "failed_only" and outcome_str != "failed":
        return None

    page = item.funcargs.get("page")
    if page is None:
        return None
    try:
        if page.is_closed():
            return None
    except Exception:
        return None

    shots_dir = run_dir / "screenshots"
    shots_dir.mkdir(parents=True, exist_ok=True)
    fname = _safe_filename(f"{_wbs_of(item)}__{item.name}.png")
    target = shots_dir / fname
    try:
        page.screenshot(path=str(target), full_page=True)
    except Exception:
        return None
    return f"./screenshots/{fname}"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when != "call":
        return

    shot_rel = _take_screenshot(item, rep.outcome, _run_dir(item.session))

    _results(item.session).append(
        {
            "wbs": _wbs_of(item),
            "nodeid": item.nodeid,
            "name": item.name,
            "title": (item.function.__doc__ or "").strip().splitlines()[0]
            if item.function.__doc__
            else item.name,
            "outcome": rep.outcome,
            "duration": rep.duration,
            "longrepr": str(rep.longrepr) if rep.longrepr else "",
            "actual": getattr(item, "_actual", None),
            "expected": getattr(item, "_expected", None),
            "url": getattr(item, "_last_url", None),
            "shot": shot_rel,
        }
    )


def pytest_sessionfinish(session, exitstatus):
    results = _results(session)
    if not results:
        return

    rid = _run_id(session)
    run_dir = REPORTS_DIR / f"{rid}_run"
    run_dir.mkdir(parents=True, exist_ok=True)
    mode = _shot_mode(session.config)

    by_wbs: dict[str, list] = {}
    for r in results:
        by_wbs.setdefault(r["wbs"], []).append(r)

    now_str = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")

    summary_rows = []
    for wbs, items in sorted(by_wbs.items()):
        title = _try_load_wbs_title(wbs) or wbs
        report_path = run_dir / _safe_filename(f"{title}.md")
        report_path.write_text(_render_one(wbs, title, items, now_str, mode), encoding="utf-8")
        passed = sum(1 for x in items if x["outcome"] == "passed")
        failed = sum(1 for x in items if x["outcome"] == "failed")
        skipped = sum(1 for x in items if x["outcome"] == "skipped")
        summary_rows.append((wbs, title, passed, failed, skipped, report_path.name))

    summary_path = run_dir / "_summary.md"
    summary_path.write_text(_render_summary(rid, now_str, mode, summary_rows), encoding="utf-8")


def _render_one(wbs: str, title: str, items: list, now_str: str, mode: str) -> str:
    passed = sum(1 for x in items if x["outcome"] == "passed")
    failed = sum(1 for x in items if x["outcome"] == "failed")
    skipped = sum(1 for x in items if x["outcome"] == "skipped")

    lines: list[str] = []
    lines.append(f"# 測試報告：{title}")
    lines.append("")
    lines.append(f"- 工項編號：**{wbs}**")
    lines.append(f"- 執行時間：**{now_str}**")
    lines.append(f"- 截圖模式：`{mode}`")
    lines.append(f"- 結果：✅ {passed} ／ ❌ {failed} ／ ⏭ {skipped}")
    lines.append("")

    lines.append("## 總覽")
    lines.append("| # | 案例 | 結果 | 耗時 | 截圖 |")
    lines.append("|---|------|------|------|------|")
    for i, x in enumerate(items, 1):
        icon = {"passed": "✅", "failed": "❌", "skipped": "⏭"}.get(x["outcome"], "?")
        shot_cell = f"[圖]({x['shot']})" if x.get("shot") else "—"
        lines.append(
            f"| {i} | {x['title']} | {icon} {x['outcome']} | {x['duration']:.2f}s | {shot_cell} |"
        )
    lines.append("")

    fails = [x for x in items if x["outcome"] == "failed"]
    if fails:
        lines.append("## 失敗詳情")
        for x in fails:
            lines.append("")
            lines.append(f"### 測試案例編號：{x['name']}")
            lines.append(f"- 工項編號：{wbs}")
            lines.append(f"- 預期：{x['expected'] or '（未提供）'}")
            lines.append(f"- 實際：{x['actual'] or '（未提供）'}")
            lines.append(f"- URL：{x['url'] or '（未提供）'}")
            lines.append(f"- nodeid：`{x['nodeid']}`")
            if x.get("shot"):
                lines.append("")
                lines.append(f"![失敗時畫面]({x['shot']})")
            lines.append("")
            lines.append("```")
            lines.append(x["longrepr"][:2000])
            lines.append("```")

    if mode == "always":
        with_shots = [x for x in items if x.get("shot")]
        if with_shots:
            lines.append("")
            lines.append("## 結果截圖")
            for i, x in enumerate(with_shots, 1):
                icon = {"passed": "✅", "failed": "❌", "skipped": "⏭"}.get(x["outcome"], "?")
                lines.append("")
                lines.append(f"### {i}. {x['name']} {icon}")
                lines.append(f"![{x['name']}]({x['shot']})")

    lines.append("")
    return "\n".join(lines)


def _render_summary(rid: str, now_str: str, mode: str, rows: list) -> str:
    out = [
        f"# Run {rid}",
        "",
        f"- 執行時間：**{now_str}**",
        f"- 截圖模式：`{mode}`",
        "",
        "## 工項彙總",
    ]
    out.append("| 工項 | 標題 | ✅ | ❌ | ⏭ | 報告 |")
    out.append("|------|------|----|----|----|------|")
    for wbs, title, p, f, s, fname in rows:
        out.append(f"| {wbs} | {title} | {p} | {f} | {s} | [{fname}]({fname}) |")
    out.append("")
    return "\n".join(out)


def _safe_filename(name: str) -> str:
    bad = '<>:"/\\|?*'
    for ch in bad:
        name = name.replace(ch, "_")
    return name.strip()


def _try_load_wbs_title(wbs: str) -> str | None:
    """從 specs/<父>/<工項>.md 取標題第一行 H1，作為報告檔名與標題。"""
    if "-" not in wbs:
        return None
    specs_dir = PROJECT_ROOT / "specs"
    if not specs_dir.exists():
        return None
    target_prefix = f"{wbs} "
    for parent in specs_dir.iterdir():
        if not parent.is_dir():
            continue
        for f in parent.iterdir():
            if f.is_file() and f.name.startswith(target_prefix) and f.suffix == ".md":
                return f.stem
    return None
