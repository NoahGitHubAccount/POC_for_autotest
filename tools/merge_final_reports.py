# -*- coding: utf-8 -*-
"""彙整工具：把台帳合併成一份總報告（含規格對照與截圖）。

用法：
    python tools/merge_final_reports.py            # 兩軌都產
    python tools/merge_final_reports.py --final    # 只產 final 定版總報告
    python tools/merge_final_reports.py --review   # 只產 review 待審彙整

輸出：
    reports/final/整合測試總報告.md    ← 已審定版（業主交付版）
    reports/review/待審彙整報告.md     ← 待審匯集（供使用者審查，未定版）
Word 交付：產出後用 tools/md_to_docx.py 轉檔（截圖一併嵌入）。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from pathlib import Path
from urllib.parse import quote, unquote

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.md_reporter import load_spec_requirements  # noqa: E402
FINAL = PROJECT_ROOT / "reports" / "final"
REVIEW = PROJECT_ROOT / "reports" / "review"


def _parse_rows(text: str) -> list[dict]:
    """解析台帳列 → [{n,func,title,status,expected,actual,explain,shot,date,run}]。"""
    rows = []
    for line in text.splitlines():
        if not line.startswith("| ") or "---" in line or "案例（函式）" in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 10:
            continue
        shot = None
        sm = re.search(r"\((\./screenshots/[^)]+)\)", cells[7])
        if sm:
            shot = unquote(sm.group(1))  # 台帳內可能已編碼，先還原
        rows.append({
            "n": cells[0], "func": cells[1].strip("`"), "title": cells[2],
            "status": cells[3], "expected": cells[4], "actual": cells[5],
            "explain": cells[6], "shot": shot, "date": cells[8], "run": cells[9],
        })
    return rows


def _build(base: Path, out_path: Path, title: str, scope: str, date_label: str) -> bool:
    ledgers = sorted(
        (d / f"{d.name}.md")
        for d in base.iterdir()
        if d.is_dir() and (d / f"{d.name}.md").exists()
    ) if base.exists() else []
    if not ledgers:
        print(f"[略過] {base} 下沒有台帳")
        return False

    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    out: list[str] = [
        f"# {title}",
        "",
        f"- 彙整時間：**{now}**",
        f"- 收錄範圍：{scope}，共 {len(ledgers)} 個測試項目",
        "",
        "## 測試項目總覽",
        "",
        f"| 測試項目 | 案例數 | ✅ 通過 | ⚠ 發現問題(xfail) | 其他 | {date_label} |",
        "|---|---|---|---|---|---|",
    ]
    sections: list[str] = []
    for md in ledgers:
        rows = _parse_rows(md.read_text(encoding="utf-8"))
        # 列順序＝先 pass/xfail 分組再案例（使用者閱讀習慣）：PASS 前、xfail/其他 後，組內維持台帳順序
        rows.sort(key=lambda r: 0 if "✅" in r["status"] else 1)
        p = sum(1 for r in rows if "✅" in r["status"])
        xf = sum(1 for r in rows if "xfail" in r["status"])
        other = len(rows) - p - xf
        last = max((r["date"] for r in rows), default="—")
        out.append(f"| {md.stem} | {len(rows)} | {p} | {xf} | {other} | {last} |")

        sec = [f"\n## {md.stem}", ""]
        spec_req = load_spec_requirements(md.stem.split(" ")[0])
        if spec_req:
            sec += ["### 測試規格要求（對照）", "", spec_req, ""]
        sec += ["### 案例狀態", "",
               "| # | 子測試項目 | 結果 | 說明 | 定版日期 |",
               "|---|---|---|---|---|"]
        for r in rows:
            sec.append(f"| {r['n']} | {r['title']} | {r['status']} | {r['explain']} | {r['date']} |")
        sec.append("")
        sec.append("### 案例截圖")
        for r in rows:
            sec.append("")
            sec.append(f"#### {r['n']}. {r['title']} — {r['status']}")
            sec.append(f"- 預期：{r['expected']}")
            sec.append(f"- 實際：{r['actual']}")
            if r["explain"] and r["explain"] != "—":
                sec.append(f"- 說明：{r['explain']}")
            if r["shot"]:
                rel = r["shot"].replace("./screenshots/", f"./{md.parent.name}/screenshots/")
                rel = quote(rel, safe="/.")  # 空格與 [] 需 URL 編碼，否則多數渲染器不顯示
                sec.append("")
                sec.append(f"![{r['func']}]({rel})")
            else:
                sec.append("- （無截圖）")
        sections.append("\n".join(sec))

    out.append("")
    out.extend(sections)
    out_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"已產出：{out_path}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", action="store_true", help="只產 final 定版總報告")
    ap.add_argument("--review", action="store_true", help="只產 review 待審彙整")
    args = ap.parse_args()
    do_final = args.final or not args.review
    do_review = args.review or not args.final
    if do_final:
        _build(FINAL, FINAL / "整合測試總報告.md", "整合測試總報告",
               "已確認定版之測試案例（持續累積）", "最後定版日")
    if do_review:
        _build(REVIEW, REVIEW / "待審彙整報告.md", "整合測試 — 待審彙整報告",
               "已測待審之案例（尚未定版）", "收集日期")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
