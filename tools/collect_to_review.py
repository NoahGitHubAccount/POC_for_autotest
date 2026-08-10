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
            # 主圖名=<wbs>__<func>[chromium].png；snap 圖名多 __<label> 尾段，主圖必為第一張。
            # 參數化案例＝<func>[chromium-<param>].png：param 必須保留（否則 N 案坍縮成同一 key
            # 互相覆蓋，2026-07-30 IT-05 17 案只剩 1 列的教訓）；非參數化維持舊行為（整段剝除）。
            name = Path(shot).name.split("__", 1)[-1]
            # PASS ＋ failed_only 模式下不會有主圖，shots[0] 會是 snap 圖
            # （檔名多一段 `__<label>`）。不先剝掉尾段，func 會變成整串檔名 →
            # 台帳新增一列垃圾 key 而非更新既有列（2026-08-01 no215 補證時發現）。
            name = re.sub(r"(\[[^\]]*\])__.+\.png$", r"\1.png", name)
            func = re.sub(r"\[chromium-([^\]]+)\]\.png$", r"[\1]", name)
            if func.endswith(".png"):  # 非參數化：[chromium].png 或其他瀏覽器參數
                func = re.sub(r"\[.*?\]\.png$", "", func)
        if func:
            cases[func] = {"title": title, "status": status, "explain": explain or "—",
                           "shot": shot, "shots": shots, "expected": "—", "actual": "—"}
    for m in re.finditer(r"^### \d+\. (\S+?\[[^\]]*\])[^\n]*\n(.*?)(?=^### |\Z)", text, re.M | re.S):
        raw, block = m.group(1), m.group(2)
        # 與上方 shot 檔名同一正規化：參數化保留 param、非參數化剝除 [chromium]
        func = re.sub(r"\[chromium-([^\]]+)\]$", r"[\1]", raw)
        func = re.sub(r"\[chromium\]$", "", func)
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
        # 台帳截圖一律純 ASCII 短檔名（IT-xx_acN_k.png）：中文/[]/+ 等長檔名
        # 會讓部分檢視器（Obsidian 等）解析失敗（2026-07-13 使用者回報）
        m = re.search(r"_(ac\d+[a-z]?)", func)
        if m:
            slug = m.group(1)
        else:
            # 參數化案例用參數 id 當 slug（保持 ASCII：非英數字元轉 _）
            pm = re.search(r"\[([^\]]+)\]$", func)
            slug = (re.sub(r"[^A-Za-z0-9.-]", "_", pm.group(1)) if pm
                    else f"c{abs(hash(func)) % 10000}")
        for k, s in enumerate(c.get("shots") or ([c["shot"]] if c["shot"] else []), 1):
            src = run_dir / s.lstrip("./")
            if src.exists():
                dst_name = f"{args.wbs}_{slug}_{k}.png"
                shutil.copy2(src, shots_dir / dst_name)
                label = "圖" if k == 1 else f"圖{k}"
                links.append(f"[{label}](./screenshots/{dst_name})")
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
