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
import os
import re
import sys
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
        # 外部排程（如 nightly_run.ps1）可用環境變數指定，讓 gap 檔 / 報告 / docx 落同一目錄
        # 未指定時精度到秒：防同分鐘兩個 pytest 程序共用同一 run 目錄（見 99 經驗 2026-05-18）
        rid = os.environ.get("MD_REPORT_RUN_ID") or _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
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
        # full_page：多點證據（如整頁必填紅字）需整頁截圖。長圖顯示異常已排除
        # ＝彙整報告 alt 文字問題非圖片本身（2026-07-12 A/B 實測），勿改 viewport。
        page.screenshot(path=str(target), full_page=True, timeout=20_000)
    except Exception as e:
        # 極長頁面（例如展開全部場次卡的 modal）full_page 會逾時。原本直接 return None
        # ＝該案靜默無圖，審查時只看到「—」卻查不出原因，且 mode=always 下連
        # 「結果截圖」區（預期／實際的來源）都不會產生（2026-08-01 no215 補證時發現）。
        # 退一步拍可視區，至少留下證據並把原因印出來。
        print(f"[md_reporter] full_page 截圖失敗（{type(e).__name__}），改拍可視區：{fname}",
              file=sys.stderr)
        try:
            page.screenshot(path=str(target), full_page=False, timeout=15_000)
        except Exception as e2:
            print(f"[md_reporter] 可視區截圖亦失敗（{type(e2).__name__}）：{fname}", file=sys.stderr)
            return None
    return f"./screenshots/{fname}"


def snap_page(item, page, label: str) -> str | None:
    """測試中途快照（一案多圖用）：立刻截當下頁面存 run 目錄並登記到 item。

    供 conftest 的 snap fixture 呼叫；跨頁/前後台對照案每個關鍵畫面各拍一張
    （2026-07-12 使用者退件要求：跨多頁面的案例圖片要各抓一張）。
    """
    run_dir = _run_dir(item.session)
    shots_dir = run_dir / "screenshots"
    shots_dir.mkdir(parents=True, exist_ok=True)
    # label 消毒：+ % # ? & = 空格等符號會讓檢視器解析圖片路徑失敗（2026-07-13 使用者回報 + 案例）
    label = re.sub(r"[+%#?&=\s]", "_", label)
    fname = _safe_filename(f"{_wbs_of(item)}__{item.name}__{label}.png")
    try:
        # snap＝「當下畫面」一屏（呼叫端先捲到目標）；整頁證據由案末主圖（full_page）負責
        page.screenshot(path=str(shots_dir / fname), full_page=False)
    except Exception:
        return None
    rel = f"./screenshots/{fname}"
    shots = getattr(item, "_extra_shots", None)
    if shots is None:
        shots = []
        item._extra_shots = shots
    shots.append((label, rel))
    return rel


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()

    # 計算 @pytest.mark.skip / skipif 的 setup-phase skip（不會進 call phase）
    if rep.when == "setup" and rep.outcome == "skipped":
        n = getattr(item.session.config, "_md_setup_skips", 0)
        setattr(item.session.config, "_md_setup_skips", n + 1)
        return

    if rep.when != "call":
        return

    shot_rel = _take_screenshot(item, rep.outcome, _run_dir(item.session))

    _results(item.session).append(
        {
            "wbs": _wbs_of(item),
            "nodeid": item.nodeid,
            "name": item.name,
            # 參數化案例可用 `request.node._case_title = "..."` 覆寫列標題
            # （否則 N 列共用同一句 docstring，審查者無法分辨各列測什麼）
            "title": getattr(item, "_case_title", None)
            or ((item.function.__doc__ or "").strip().splitlines()[0]
                if item.function.__doc__ else item.name),
            "outcome": rep.outcome,
            "wasxfail": bool(getattr(rep, "wasxfail", None)),
            "xfail_reason": str(getattr(rep, "wasxfail", "") or ""),
            "duration": rep.duration,
            "longrepr": str(rep.longrepr) if rep.longrepr else "",
            "actual": getattr(item, "_actual", None),
            "expected": getattr(item, "_expected", None),
            "url": getattr(item, "_last_url", None),
            "shot": shot_rel,
            "extra_shots": list(getattr(item, "_extra_shots", []) or []),
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
        passed  = sum(1 for x in items if x["outcome"] == "passed"  and not x.get("wasxfail"))
        failed  = sum(1 for x in items if x["outcome"] == "failed")
        xfail   = sum(1 for x in items if x["outcome"] == "skipped" and     x.get("wasxfail"))
        skipped = sum(1 for x in items if x["outcome"] == "skipped" and not x.get("wasxfail"))
        summary_rows.append((wbs, title, passed, failed, xfail, skipped, report_path.name))

    setup_skips = getattr(session.config, "_md_setup_skips", 0)
    totals = {
        "passed":  sum(1 for r in results if r["outcome"] == "passed"  and not r.get("wasxfail")),
        "failed":  sum(1 for r in results if r["outcome"] == "failed"),
        "xfail":   sum(1 for r in results if r["outcome"] == "skipped" and     r.get("wasxfail")),
        "xpass":   sum(1 for r in results if r["outcome"] == "passed"  and     r.get("wasxfail")),
        "skipped": sum(1 for r in results if r["outcome"] == "skipped" and not r.get("wasxfail")) + setup_skips,
    }
    totals["total"] = sum(totals.values())

    summary_path = run_dir / "_summary.md"
    summary_path.write_text(_render_summary(rid, now_str, mode, summary_rows, totals), encoding="utf-8")


def _md_cell(text: str, limit: int = 160) -> str:
    """表格儲存格安全化：去換行、跳脫直線、截長。"""
    t = " ".join(str(text).split()).replace("|", "\\|")
    return t[:limit] + ("…" if len(t) > limit else "")


def _skip_reason(x: dict) -> str:
    """從 longrepr 取 skip 理由（格式 ('file', line, 'Skipped: <理由>')）。"""
    m = re.search(r"Skipped:?\s*(.+?)['\")]*$", x.get("longrepr", ""))
    return m.group(1) if m else x.get("longrepr", "")


def _explain(x: dict) -> str:
    """非 PASS 狀態的說明：xfail=原因、skipped=理由、failed=預期+實際。PASS 免說明。"""
    if x["outcome"] == "failed":
        return _md_cell(f"預期：{x.get('expected') or '（未提供）'}；實際：{x.get('actual') or '（未提供）'}")
    if x.get("wasxfail"):
        return _md_cell(f"xfail：{x.get('xfail_reason') or '（未註明原因）'}")
    if x["outcome"] == "skipped":
        return _md_cell(f"skip：{_skip_reason(x) or '（未註明理由）'}")
    return "—"


def _pass_first(items: list) -> list:
    """報告列順序＝先 pass/xfail 分組再案例（使用者閱讀習慣）：PASS 在前、xfail/failed/skip 在後，組內維持執行順序。"""
    return sorted(items, key=lambda x: 0 if (x["outcome"] == "passed" and not x.get("wasxfail")) else 1)


def _render_one(wbs: str, title: str, items: list, now_str: str, mode: str) -> str:
    items = _pass_first(items)
    passed  = sum(1 for x in items if x["outcome"] == "passed"  and not x.get("wasxfail"))
    failed  = sum(1 for x in items if x["outcome"] == "failed")
    xfail   = sum(1 for x in items if x["outcome"] == "skipped" and     x.get("wasxfail"))
    skipped = sum(1 for x in items if x["outcome"] == "skipped" and not x.get("wasxfail"))

    lines: list[str] = []
    lines.append(f"# 測試報告：{title}")
    lines.append("")
    lines.append(f"- 工項編號：**{wbs}**")
    lines.append(f"- 執行時間：**{now_str}**")
    lines.append(f"- 截圖模式：`{mode}`")
    parts = [f"✅ {passed}", f"❌ {failed}"]
    if xfail:
        parts.append(f"⚠ xfail {xfail}")
    if skipped:
        parts.append(f"⏭ {skipped}")
    lines.append(f"- 結果：{' ／ '.join(parts)}")
    lines.append("")

    spec_req = load_spec_requirements(wbs)
    if spec_req:
        lines.append("## 測試規格要求（對照）")
        lines.append("")
        lines.append(spec_req)
        lines.append("")

    lines.append("## 總覽")
    lines.append("| # | 案例 | 結果 | 耗時 | 截圖 | 說明（非 PASS 必填） |")
    lines.append("|---|------|------|------|------|------|")
    for i, x in enumerate(items, 1):
        if x.get("wasxfail"):
            status = "⚠ xfail"
        else:
            icon = {"passed": "✅", "failed": "❌", "skipped": "⏭"}.get(x["outcome"], "?")
            status = f"{icon} {x['outcome']}"
        pure_skip = x["outcome"] == "skipped" and not x.get("wasxfail")
        shot_cell = f"[圖]({x['shot']})" if x.get("shot") and not pure_skip else "—"
        for j, (_lbl, rel) in enumerate(x.get("extra_shots") or [], 2):
            shot_cell += f" [圖{j}]({rel})"
        lines.append(
            f"| {i} | {x['title']} | {status} | {x['duration']:.2f}s | {shot_cell} | {_explain(x)} |"
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
        # 純 skip（非 xfail）從未執行操作，截圖必為空白頁 → 不列截圖區（總覽表已附理由）
        with_shots = [x for x in items if (x.get("shot") or x.get("extra_shots"))
                      and (x["outcome"] != "skipped" or x.get("wasxfail"))]
        if with_shots:
            lines.append("")
            lines.append("## 結果截圖")
            for i, x in enumerate(with_shots, 1):
                if x.get("wasxfail"):
                    icon = "⚠ xfail"
                else:
                    icon = {"passed": "✅", "failed": "❌", "skipped": "⏭"}.get(x["outcome"], "?")
                lines.append("")
                lines.append(f"### {i}. {x['name']} {icon}")
                lines.append(f"- 案例：{x['title']}")
                lines.append(f"- 預期：{x.get('expected') or '（未提供）'}")
                lines.append(f"- 實際：{x.get('actual') or '（未提供）'}")
                if x["outcome"] != "passed" or x.get("wasxfail"):
                    lines.append(f"- 說明：{_explain(x)}")
                if x.get("shot"):
                    lines.append("")
                    lines.append(f"![shot{i}]({x['shot']})")
                # 一案多圖：測試中途 snap 的跨頁/前後台對照圖，逐張帶標籤列出
                for j, (lbl, rel) in enumerate(x.get("extra_shots") or [], 2):
                    lines.append("")
                    lines.append(f"（圖{j}：{lbl}）")
                    lines.append("")
                    lines.append(f"![shot{i}_{j}]({rel})")

    lines.append("")
    return "\n".join(lines)


def _render_summary(rid: str, now_str: str, mode: str, rows: list, totals: dict) -> str:
    total = totals["total"]

    def pct(n: int) -> str:
        return f"{n / total * 100:.1f}%" if total else "0%"

    out = [
        f"# Run {rid}",
        "",
        f"- 執行時間：**{now_str}**",
        f"- 截圖模式：`{mode}`",
        "",
        "## 整體結果",
        "",
        "| 狀態 | 數量 | 佔比 |",
        "|------|-----:|-----:|",
        f"| **合計** | **{total}** | 100% |",
        f"| ✅ PASSED  | {totals['passed']}  | {pct(totals['passed'])} |",
        f"| ❌ FAILED  | {totals['failed']}  | {pct(totals['failed'])} |",
        f"| ⚠ XFAIL   | {totals['xfail']}   | {pct(totals['xfail'])} |",
        f"| ⬆ XPASS   | {totals['xpass']}   | {pct(totals['xpass'])} |",
        f"| ⏭ SKIPPED | {totals['skipped']} | {pct(totals['skipped'])} |",
        "",
        "## 工項彙總",
    ]
    out.append("| 工項 | 標題 | ✅ | ❌ | ⚠ XF | ⏭ | 報告 |")
    out.append("|------|------|----|----|-------|----|----|")
    for wbs, title, p, f, xf, s, fname in rows:
        out.append(f"| {wbs} | {title} | {p} | {f} | {xf} | {s} | [{fname}]({fname}) |")
    out.append("")
    return "\n".join(out)


def _safe_filename(name: str) -> str:
    bad = '<>:"/\\|?*'
    for ch in bad:
        name = name.replace(ch, "_")
    return name.strip()


def _find_spec_file(wbs: str) -> Path | None:
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
                return f
    return None


def _try_load_wbs_title(wbs: str) -> str | None:
    """從 specs/<父>/<工項>.md 取標題第一行 H1，作為報告檔名與標題。"""
    f = _find_spec_file(wbs)
    return f.stem if f else None


def load_spec_requirements(wbs: str) -> str | None:
    """從 spec 檔抽「規則」引言與「驗收條件 (AC)」清單，供報告對照規格要求。"""
    f = _find_spec_file(wbs)
    if f is None:
        return None
    text = f.read_text(encoding="utf-8")
    parts: list[str] = []
    # H1 後的 blockquote（> 規則：…）
    m = re.search(r"^# .+?\n+((?:^>.*\n?)+)", text, re.M)
    if m:
        parts.append(m.group(1).rstrip())
    # 驗收條件段（優先 AI-MANAGED 標界，否則取 heading 到下一個 ## 為止）
    m = re.search(r"<!-- AI-MANAGED START: acceptance-criteria -->\n(.*?)<!-- AI-MANAGED END",
                  text, re.S)
    if not m:
        m = re.search(r"^## 驗收條件.*?\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if m:
        parts.append("**驗收條件 (AC)**\n" + m.group(1).strip())
    return "\n\n".join(parts) if parts else None
