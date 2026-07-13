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
        shots = [unquote(s) for s in re.findall(r"\((\./screenshots/[^)]+)\)", cells[7])]  # 一案多圖
        rows.append({
            "n": cells[0], "func": cells[1].strip("`"), "title": cells[2],
            "status": cells[3], "expected": cells[4], "actual": cells[5],
            "explain": cells[6], "shot": shots[0] if shots else None, "shots": shots,
            "date": cells[8], "run": cells[9],
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
            for k, s in enumerate(r.get("shots") or [], 1):
                rel = s.replace("./screenshots/", f"./{md.parent.name}/screenshots/")
                rel = quote(rel, safe="/.")  # 空格與 [] 需 URL 編碼，否則多數渲染器不顯示
                if k > 1:
                    sec.append("")
                    sec.append(f"（圖{k}）")
                sec.append("")
                sec.append(f"![case{r['n']}_{k}]({rel})")  # alt 短 ASCII（長中文 alt 會破格）
            if not r.get("shots"):
                sec.append("- （無截圖）")
        sections.append("\n".join(sec))

    out.append("")
    out.extend(sections)
    out_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"已產出：{out_path}")
    return True


def _case_block(r: dict, ledger_dir_name: str, idx: int, wbs: str) -> list[str]:
    """單一案例的截圖區塊（跨工項扁平視圖用，標題帶工項）。

    區塊結構鎖定＝已驗證可顯示的形態（2026-07-12 A/B 實測）：標題→空行→圖→空行→bullets。
    標題勿用 [方括號]（Markdown 連結語法）、alt 用短 ASCII、圖與標題間勿夾清單。
    """
    sec = ["", f"#### {idx}.（{wbs}）{r['title']} — {r['status']}"]
    for k, s in enumerate(r.get("shots") or [], 1):
        rel = s.replace("./screenshots/", f"./{ledger_dir_name}/screenshots/")
        rel = quote(rel, safe="/.")  # 空格與 [] 需 URL 編碼，否則多數渲染器不顯示
        if k > 1:
            sec += ["", f"（圖{k}）"]
        sec += ["", f"![case{idx}_{k}]({rel})"]
    sec += ["", f"- 預期：{r['expected']}", f"- 實際：{r['actual']}"]
    if r["explain"] and r["explain"] != "—":
        sec.append(f"- 說明：{r['explain']}")
    if not r.get("shots"):
        sec.append("- （無截圖）")
    return sec


def _build_review_flat(base: Path, out_path: Path) -> bool:
    """待審彙整（使用者審查視角）：**全域** PASS 區在前、xfail 區在後，不分工項混排；
    工項只作為列上標籤；規則原文對照集中附錄。"""
    ledgers = sorted(
        (d / f"{d.name}.md")
        for d in base.iterdir()
        if d.is_dir() and (d / f"{d.name}.md").exists()
    ) if base.exists() else []
    if not ledgers:
        print(f"[略過] {base} 下沒有台帳")
        return False

    all_rows: list[tuple[str, str, dict]] = []  # (wbs_stem, ledger_dir_name, row)
    overview: list[str] = []
    for md in ledgers:
        rows = _parse_rows(md.read_text(encoding="utf-8"))
        p = sum(1 for r in rows if "✅" in r["status"])
        xf = sum(1 for r in rows if "xfail" in r["status"])
        other = len(rows) - p - xf
        last = max((r["date"] for r in rows), default="—")
        overview.append(f"| {md.stem} | {len(rows)} | {p} | {xf} | {other} | {last} |")
        for r in rows:
            all_rows.append((md.stem, md.parent.name, r))

    passes = [(w, d, r) for w, d, r in all_rows if "✅" in r["status"]]
    others = [(w, d, r) for w, d, r in all_rows if "✅" not in r["status"]]

    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    out: list[str] = [
        "# 整合測試 — 待審彙整報告",
        "",
        f"- 彙整時間：**{now}**",
        f"- 收錄範圍：已測待審之案例（尚未定版），共 {len(ledgers)} 個測試項目、{len(all_rows)} 案"
        f"（✅ {len(passes)}／⚠ {len(others)}）",
        "- 排版：**全部工項的 ✅ 通過案例集中在前、⚠ 發現問題(xfail) 集中在後**；工項見列上標籤；規則原文見文末附錄",
        "",
        "## 測試項目總覽",
        "",
        "| 測試項目 | 案例數 | ✅ 通過 | ⚠ 發現問題(xfail) | 其他 | 收集日期 |",
        "|---|---|---|---|---|---|",
        *overview,
    ]

    def _flat_section(header: str, group: list, start: int) -> list[str]:
        sec = ["", f"## {header}", "",
               "| # | 工項 | 子測試項目 | 結果 | 說明 | 收集日期 |",
               "|---|---|---|---|---|---|"]
        for i, (w, _d, r) in enumerate(group, start):
            wbs = w.split(" ")[0]
            sec.append(f"| {i} | {wbs} | {r['title']} | {r['status']} | {r['explain']} | {r['date']} |")
        sec += ["", f"### 截圖（{header.split('（')[0]}）"]
        for i, (w, d, r) in enumerate(group, start):
            sec += _case_block(r, d, i, w.split(" ")[0])
        return sec

    out += _flat_section(f"✅ 通過案例（{len(passes)} 案）", passes, 1)
    out += _flat_section(f"⚠ 發現問題案例（{len(others)} 案）", others, len(passes) + 1)

    out += ["", "## 附錄：各工項規則原文對照", ""]
    for md in ledgers:
        spec_req = load_spec_requirements(md.stem.split(" ")[0])
        if spec_req:
            out += [f"### {md.stem}", "", spec_req, ""]

    out_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"已產出：{out_path}")
    return True


def _build_final_grouped(out_path: Path) -> bool:
    """整合測試總報告（2026-07-13 使用者指定）：**收錄全部已測案例**（定版＋待審，
    每案標註審查狀態）——問題單每一條 ISS 都必須有對應案例在報告內。
    大綱：摘要 → PASS（依工項分節：規則說明＋各 AC）→ xfail 集中（跨工項扁平、標籤帶工項）。"""
    # 收兩區台帳：同工項的定版與待審列合併（定版在前）
    by_stem: dict[str, list[tuple[Path, str, dict]]] = {}
    for base, tag, rel_prefix in ((FINAL, "已定版", "."), (REVIEW, "待審", "../review")):
        if not base.exists():
            continue
        for d in sorted(base.iterdir()):
            md = d / f"{d.name}.md"
            if not (d.is_dir() and md.exists()):
                continue
            for r in _parse_rows(md.read_text(encoding="utf-8")):
                r["_tag"] = tag
                r["_shotdir"] = f"{rel_prefix}/{d.name}/screenshots/"
                by_stem.setdefault(d.name, []).append((md, tag, r))
    if not by_stem:
        print("[略過] final/review 均無台帳")
        return False

    overview: list[str] = []
    tot_p = tot_x = 0
    for stem in sorted(by_stem):
        rows = [r for _m, _t, r in by_stem[stem]]
        p = sum(1 for r in rows if "✅" in r["status"])
        xf = len(rows) - p
        pending = sum(1 for _m, t, _r in by_stem[stem] if t == "待審")
        tot_p += p
        tot_x += xf
        overview.append(f"| {stem} | {len(rows)} | {p} | {xf} | {pending} |")

    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    out: list[str] = [
        "# 整合測試總報告",
        "",
        f"- 產出時間：**{now}**",
        f"- 收錄範圍：**全部已測案例（已定版＋待審）**，共 {len(by_stem)} 個測試項目、"
        f"{tot_p + tot_x} 案（✅ 通過 {tot_p}／⚠ 發現問題 {tot_x}）；每案標註審查狀態",
        "",
        "## 摘要",
        "",
        "| 測試項目 | 案例數 | ✅ 通過 | ⚠ 發現問題(xfail) | 其中待審 |",
        "|---|---|---|---|---|",
        *overview,
        "",
        "## 一、通過案例（PASS）",
    ]

    def _case_shots(r: dict, alt_prefix: str) -> list[str]:
        sec = []
        for k, s in enumerate(r.get("shots") or [], 1):
            rel = quote(s.replace("./screenshots/", r["_shotdir"]), safe="/.")
            if k > 1:
                sec += ["", f"（圖{k}）"]
            sec += ["", f"![{alt_prefix}_{k}]({rel})"]
        return sec

    for stem in sorted(by_stem):
        passes = [r for _m, _t, r in by_stem[stem] if "✅" in r["status"]]
        if not passes:
            continue
        out += ["", f"### {stem}", ""]
        spec_req = load_spec_requirements(stem.split(" ")[0])
        if spec_req:
            out += ["**規則說明**", "", spec_req, ""]
        for i, r in enumerate(passes, 1):
            out += ["", f"#### {r['title']} — ✅（{r['_tag']}）"]
            out += _case_shots(r, f"p{stem.split(' ')[0]}_{i}")
            out += ["", f"- 預期：{r['expected']}", f"- 實際：{r['actual']}",
                    f"- 審查狀態：{r['_tag']}"]

    out += ["", "## 二、發現問題案例（xfail 集中）"]
    n = 0
    for stem in sorted(by_stem):
        for _m, _t, r in by_stem[stem]:
            if "✅" in r["status"]:
                continue
            n += 1
            wbs = stem.split(" ")[0]
            out += ["", f"#### {n}.（{wbs}）{r['title']} — {r['status']}（{r['_tag']}）"]
            out += _case_shots(r, f"x{n}")
            out += ["", f"- 預期：{r['expected']}", f"- 實際：{r['actual']}"]
            if r["explain"] and r["explain"] != "—":
                out.append(f"- 說明：{r['explain']}")
            out.append(f"- 審查狀態：{r['_tag']}")

    # 三、問題單全文對照（收錄現行問題單 TSV → 表格，保證問題單每一條都在總報告）
    issue_file = PROJECT_ROOT / "整合測試_問題單.md"
    if issue_file.exists():
        itext = issue_file.read_text(encoding="utf-8")
        out += ["", "## 三、問題單（現行全文對照）", "",
                "| # | 類別 | 標題 | 嚴重度 | 描述 | 狀態 |", "|---|---|---|---|---|---|"]
        m = re.search(r"```tsv\n(.*?)```", itext, re.S)
        rows_n = 0
        if m:
            for ln in m.group(1).splitlines():
                cells = [c.strip().strip('"') for c in ln.split("\t")]
                if len(cells) >= 6 and cells[1]:
                    rows_n += 1
                    out.append(f"| {rows_n} | {cells[1]} | {cells[2]} | {cells[3]} "
                               f"| {_md_cell_escape(cells[4])} | {cells[5]} |")
        cm = re.search(r"（內部追蹤碼對照：(.+?)）", itext, re.S)
        if cm:
            out += ["", f"內部追蹤碼對照：{' '.join(cm.group(1).split())}"]

    out_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"已產出：{out_path}")

    # 問題單 ISS 覆蓋核對：每個 ISS-xxx 應在報告內出現
    if issue_file.exists():
        report_text = "\n".join(out)
        listed = set(re.findall(r"ISS-(\d{3})", itext))
        struck = set(re.findall(r"~~ISS-(\d{3})", itext))
        missing = sorted(i for i in listed - struck if f"ISS-{i}" not in report_text)
        if missing:
            print(f"⚠ 問題單 ISS 未在總報告出現：{['ISS-' + m for m in missing]}（請確認對應案例是否已測/已收）")
        else:
            print("✓ 問題單 ISS 全數在總報告（xfail 案例＋問題單對照章節）")
    return True


def _md_cell_escape(t: str) -> str:
    return " ".join(t.split()).replace("|", "\\|")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", action="store_true", help="只產 final 定版總報告")
    ap.add_argument("--review", action="store_true", help="只產 review 待審彙整")
    args = ap.parse_args()
    do_final = args.final or not args.review
    do_review = args.review or not args.final
    if do_final:
        # 總報告＝交付視角（2026-07-13 使用者指定）：收全部已測案例（定版＋待審）
        # 摘要→PASS 依工項（含規則說明）→xfail 集中；ISS 覆蓋自動核對
        _build_final_grouped(FINAL / "整合測試總報告.md")
    if do_review:
        # 待審軌＝使用者審查視角：全域 PASS 前、xfail 後（2026-07-12 裁示，勿改回工項分節）
        _build_review_flat(REVIEW, REVIEW / "待審彙整報告.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
