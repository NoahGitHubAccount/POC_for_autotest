# -*- coding: utf-8 -*-
"""匯集工具（三段流程第 1 段）：把散裝的工作區 run 報告，收集彙整進「待審匯集區」。

用法：
    python tools/collect_to_review.py <run_id> <wbs> [--cases 子字串1,子字串2] [--dry-run]

行為：
    1. 解析 reports/<run_id>_run/ 中該 wbs 的報告 md
    2. 追加/更新案例列到 reports/review/<報告名>/<報告名>.md（彙整台帳），複製截圖
    3. **不碰 frozen_tests、不定版**——僅集中供使用者審查
    同工項多份 run 各呼叫一次即累積合併（例：IT-06 ac1-4 與 ac5-6 兩份 run）。
    審查通過後再用 tools/finalize_report.py <wbs> 定版凍結。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS = PROJECT_ROOT / "reports"
REVIEW = REPORTS / "review"

LEDGER_HEADER = (
    "| # | 案例（函式） | AC 描述 | 結果 | 預期 | 實際 | 說明（非 PASS） | 截圖 | 收集日期 | 來源 run |\n"
    "|---|---|---|---|---|---|---|---|---|---|\n"
)


def _parse_report(md_path: Path) -> dict[str, dict]:
    text = md_path.read_text(encoding="utf-8")
    cases: dict[str, dict] = {}
    for m in re.finditer(
        r"^\|\s*\d+\s*\|(.+?)\|(.+?)\|\s*[\d.]+s\s*\|(.+?)\|(.*?)\|\s*$", text, re.M
    ):
        title, status, shot_cell, explain = (g.strip() for g in m.groups())
        shots = re.findall(r"\((\./screenshots/[^)]+)\)", shot_cell)  # 一案多圖：全取
        shot = shots[0] if shots else None
        func = None
        if shot:
            # 主圖名=<wbs>__<func>[chromium].png；snap 圖名多 __<label> 尾段，主圖必為第一張
            func = re.sub(r"\[.*?\]\.png$", "", Path(shot).name.split("__", 1)[-1])
        if func:
            cases[func] = {"title": title, "status": status, "explain": explain or "—",
                           "shot": shot, "shots": shots, "expected": "—", "actual": "—"}
    for m in re.finditer(r"^### \d+\. (\S+?)\[[^\]]*\][^\n]*\n(.*?)(?=^### |\Z)", text, re.M | re.S):
        func, block = m.group(1), m.group(2)
        if func not in cases:
            continue
        for key, label in (("expected", "預期"), ("actual", "實際")):
            km = re.search(rf"^- {label}：(.+)$", block, re.M)
            if km:
                cases[func][key] = km.group(1).strip()
    return cases


def _md_escape(t: str) -> str:
    return " ".join(t.split()).replace("|", "\\|")


def sort_and_renumber(lines: list[str]) -> list[str]:
    """台帳列排序：PASS 在前、xfail/fail 在後（使用者閱讀習慣），組內維持原順序並重編 #。"""
    head, rows = [], []
    for l in lines:
        if l.startswith("| ") and "---" not in l and "案例（函式）" not in l:
            rows.append(l)
        else:
            head.append(l)
    rows.sort(key=lambda l: 0 if "passed" in (l.split("|")[4] if l.count("|") >= 5 else "") else 1)
    out = []
    for i, l in enumerate(rows, 1):
        parts = l.split("|")
        parts[1] = f" {i} "
        out.append("|".join(parts))
    return head + out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_id")
    ap.add_argument("wbs")
    ap.add_argument("--cases", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    run_dir = REPORTS / f"{args.run_id}_run"
    if not run_dir.exists():
        print(f"[錯誤] 找不到 {run_dir}", file=sys.stderr)
        return 2
    report_md = next(
        (p for p in run_dir.glob("*.md")
         if p.name != "_summary.md" and f"工項編號：**{args.wbs}**" in p.read_text(encoding="utf-8")),
        None,
    )
    if report_md is None:
        print(f"[錯誤] {run_dir} 內找不到工項 {args.wbs} 的報告", file=sys.stderr)
        return 2

    cases = _parse_report(report_md)
    if args.cases:
        keys = [k.strip() for k in args.cases.split(",") if k.strip()]
        cases = {f: c for f, c in cases.items() if any(k in f for k in keys)}
    if not cases:
        print("[錯誤] 沒有可匯集案例（純 skip 無截圖者不列）", file=sys.stderr)
        return 2

    stem = report_md.stem
    ledger_dir = REVIEW / stem
    ledger_md = ledger_dir / f"{stem}.md"
    shots_dir = ledger_dir / "screenshots"
    today = _dt.date.today().isoformat()

    if args.dry_run:
        for f, c in cases.items():
            print(f"[dry-run] 匯集 {f}：{c['status']}")
        return 0

    ledger_dir.mkdir(parents=True, exist_ok=True)
    shots_dir.mkdir(exist_ok=True)
    if ledger_md.exists():
        lines = ledger_md.read_text(encoding="utf-8").splitlines(keepends=True)
    else:
        lines = [
            f"# 待審匯集：{stem}\n\n",
            "> 一列 = 一個已測案例（**尚未定版**，供使用者審查）。審查通過後執行 "
            "`python tools/finalize_report.py {wbs}` 定版凍結。\n\n".replace("{wbs}", args.wbs),
            LEDGER_HEADER,
        ]

    added, updated = [], []
    for func, c in sorted(cases.items()):
        shot_dst = "—"
        links = []
        for k, s in enumerate(c.get("shots") or ([c["shot"]] if c["shot"] else []), 1):
            src = run_dir / s.lstrip("./")
            if src.exists():
                shutil.copy2(src, shots_dir / src.name)
                label = "圖" if k == 1 else f"圖{k}"
                links.append(f"[{label}](./screenshots/{quote(src.name, safe='.')})")
        if links:
            shot_dst = " ".join(links)
        idx = next((i for i, l in enumerate(lines) if f"`{func}`" in l), None)
        n = (lines[idx].split("|")[1].strip() if idx is not None
             else sum(1 for l in lines if l.startswith("| ") and "---" not in l and "案例（函式）" not in l) + 1)
        row = (f"| {n} | `{func}` | {_md_escape(c['title'])} | {c['status']} "
               f"| {_md_escape(c['expected'])} | {_md_escape(c['actual'])} "
               f"| {_md_escape(c['explain'])} | {shot_dst} | {today} | {args.run_id} |\n")
        if idx is not None:
            lines[idx] = row
            updated.append(func)
        else:
            lines.append(row)
            added.append(func)

    lines = sort_and_renumber(lines)
    ledger_md.write_text("".join(lines), encoding="utf-8")
    print(f"待審匯集：{ledger_md}")
    print(f"  新增 {len(added)} 列、更新 {len(updated)} 列（未凍結，待審查）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
