# -*- coding: utf-8 -*-
"""定版工具（三段流程第 3 段）：使用者審查通過後，把「待審匯集」定版凍結。

用法：
    python tools/finalize_report.py <wbs>                    # 定版整個工項
    python tools/finalize_report.py <wbs> --cases 子字串1,子字串2  # 案例級定版（其餘留待審）
    python tools/finalize_report.py <wbs> --dry-run          # 只列將定版的案例

三段流程：
    1. 匯集：tools/collect_to_review.py <run_id> <wbs>   → reports/review/<工項>（未凍結）
    2. 審查：使用者看 reports/review/<工項> 與待審彙整報告
    3. 定版：本工具 → 移到 reports/final/<工項> + 案例 nodeid 寫入 frozen_tests（凍結不重測）
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS = PROJECT_ROOT / "reports"
REVIEW = REPORTS / "review"
FINAL = REPORTS / "final"
FROZEN = FINAL / "frozen_tests.txt"


def _find_nodeid(func: str) -> str | None:
    for py in (PROJECT_ROOT / "tests").rglob("test_*.py"):
        if f"def {func}(" in py.read_text(encoding="utf-8"):
            return f"{py.relative_to(PROJECT_ROOT).as_posix()}::{func}"
    return None


_FINAL_HEADER_NOTE = (
    "> 一列 = 一個使用者確認定版的案例（凍結不重測）；回歸更新時覆寫該列。\n"
    "> 凍結清單：`reports/final/frozen_tests.txt`；回歸執行：`pytest --include-frozen -k <案例>`\n"
)
_TABLE_HEADER = (
    "| # | 案例（函式） | AC 描述 | 結果 | 預期 | 實際 | 說明（非 PASS） | 截圖 | 定版日期 | 來源 run |\n"
    "|---|---|---|---|---|---|---|---|---|---|\n"
)


def _rows_of(md_text: str) -> list[str]:
    return [ln for ln in md_text.splitlines()
            if re.match(r"^\|\s*\d+\s*\|\s*`test_", ln)]


def _renumber(rows: list[str]) -> list[str]:
    out = []
    for i, ln in enumerate(rows, 1):
        out.append(re.sub(r"^\|\s*\d+", f"| {i}", ln, count=1))
    return out


def _freeze(funcs: list[str]) -> int:
    frozen = FROZEN.read_text(encoding="utf-8").splitlines() if FROZEN.exists() else []
    added = 0
    for func in funcs:
        nid = _find_nodeid(func)
        if nid and nid not in frozen:
            frozen.append(nid)
            added += 1
    FROZEN.write_text("\n".join(frozen) + "\n", encoding="utf-8")
    return added


def _move_shots(rows: list[str], src_dir: Path, dst_dir: Path) -> None:
    (dst_dir / "screenshots").mkdir(parents=True, exist_ok=True)
    for ln in rows:
        for m in re.finditer(r"\(\./screenshots/([^)]+)\)", ln):
            from urllib.parse import unquote
            fname = unquote(m.group(1))
            src = src_dir / "screenshots" / fname
            if src.exists():
                shutil.move(str(src), str(dst_dir / "screenshots" / fname))


def _finalize_cases(src_dir: Path, case_substrs: list[str], dry: bool) -> int:
    """案例級定版：把台帳中符合子字串的列移入 final 台帳，其餘留待審。"""
    ledger = src_dir / f"{src_dir.name}.md"
    text = ledger.read_text(encoding="utf-8")
    rows = _rows_of(text)
    picked = [r for r in rows if any(s in r for s in case_substrs)]
    rest = [r for r in rows if r not in picked]
    if not picked:
        print(f"[錯誤] 台帳無符合 --cases 的案例列", file=sys.stderr)
        return 2
    funcs = [m.group(1) for r in picked for m in [re.search(r"`([^`]+)`", r)] if m]
    if dry:
        print(f"[dry-run] 將案例級定版 {src_dir.name}：{len(picked)} 案（留審 {len(rest)}）")
        for f in funcs:
            print(f"  - {f}")
        return 0

    dst_dir = FINAL / src_dir.name
    dst_ledger = dst_dir / f"{src_dir.name}.md"
    dst_dir.mkdir(parents=True, exist_ok=True)
    if dst_ledger.exists():
        dst_text = dst_ledger.read_text(encoding="utf-8")
        merged = _rows_of(dst_text)
        # 同名案例覆寫舊列
        merged = [r for r in merged
                  if not any(f"`{f}`" in r for f in funcs)] + picked
    else:
        merged = picked
    dst_ledger.write_text(
        f"# 定版台帳：{src_dir.name}\n\n{_FINAL_HEADER_NOTE}\n{_TABLE_HEADER}"
        + "\n".join(_renumber(merged)) + "\n",
        encoding="utf-8")
    _move_shots(picked, src_dir, dst_dir)

    # review 台帳留下未定版列
    head = text.split("| # |", 1)[0].rstrip("\n")
    ledger.write_text(f"{head}\n\n{_TABLE_HEADER}" + "\n".join(_renumber(rest)) + ("\n" if rest else ""),
                      encoding="utf-8")
    if not rest:  # 全數定版 → 待審資料夾清空可移除
        shots = src_dir / "screenshots"
        if shots.exists() and not any(shots.iterdir()):
            shots.rmdir()

    added = _freeze(funcs)
    print(f"已案例級定版：{dst_dir}")
    print(f"  定版 {len(picked)} 案（覆寫/新增）、留審 {len(rest)} 案、新增凍結 {added} 筆")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("wbs", help="工項編號，如 IT-04")
    ap.add_argument("--cases", help="案例子字串（逗號分隔）：只定版符合的案例，其餘留待審")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src_dir = next((d for d in REVIEW.iterdir()
                    if d.is_dir() and d.name.startswith(f"{args.wbs} ")), None) if REVIEW.exists() else None
    if src_dir is None:
        print(f"[錯誤] reports/review/ 找不到工項 {args.wbs}（需先 collect_to_review 匯集）", file=sys.stderr)
        return 2

    if args.cases:
        return _finalize_cases(src_dir, [s.strip() for s in args.cases.split(",") if s.strip()], args.dry_run)

    ledger = src_dir / f"{src_dir.name}.md"
    funcs = re.findall(r"^\| \d+ \| `([^`]+)`", ledger.read_text(encoding="utf-8"), re.M)
    if args.dry_run:
        print(f"[dry-run] 將定版 {src_dir.name}：{len(funcs)} 案")
        for f in funcs:
            print(f"  - {f}")
        return 0

    # 台帳標題「待審匯集」→「定版台帳」
    text = ledger.read_text(encoding="utf-8").replace(
        f"# 待審匯集：{src_dir.name}", f"# 定版台帳：{src_dir.name}")
    text = re.sub(r"^> 一列 = 一個已測案例.*$",
                  "> 一列 = 一個使用者確認定版的案例（凍結不重測）；回歸更新時覆寫該列。",
                  text, count=1, flags=re.M)
    ledger.write_text(text, encoding="utf-8")

    dst_dir = FINAL / src_dir.name
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    shutil.move(str(src_dir), str(dst_dir))

    frozen = FROZEN.read_text(encoding="utf-8").splitlines() if FROZEN.exists() else []
    added = 0
    for func in funcs:
        nid = _find_nodeid(func)
        if nid and nid not in frozen:
            frozen.append(nid)
            added += 1
    FROZEN.write_text("\n".join(frozen) + "\n", encoding="utf-8")

    print(f"已定版：{dst_dir}")
    print(f"  {len(funcs)} 案移入 final/，新增凍結 {added} 筆")
    print(f"凍結清單共 {sum(1 for l in frozen if l.strip() and not l.startswith('#'))} 筆")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
