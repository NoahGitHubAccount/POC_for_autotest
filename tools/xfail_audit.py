"""
xfail_audit.py -- 掃描全套 tests/ 找出「逾期未解」的 xfail marker。

用法：
    python tools/xfail_audit.py [--days 14] [--path tests/]

輸出三類 xfail：
    ZOMBIE   reason 含日期，且距今超過 --days 天（預設 14）
    BLOCKER  reason 含 BLOCKER: 前綴（待外部確認，不計天數）
    NO-DATE  reason 不含日期，無法判斷年齡

退出碼：0 = 無 ZOMBIE；1 = 有 ZOMBIE（CI 可用此做門禁）
"""

import argparse
import ast
import re
import sys
from datetime import date, datetime
from pathlib import Path


DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=14)
    p.add_argument("--path", default="tests")
    return p.parse_args()


def extract_xfails(filepath):
    results = []
    try:
        src = filepath.read_text(encoding="utf-8")
        tree = ast.parse(src)
    except Exception:
        return results

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for deco in node.decorator_list:
            deco_src = ast.unparse(deco) if hasattr(ast, "unparse") else ""
            if "xfail" not in deco_src:
                continue
            reason = ""
            if isinstance(deco, ast.Call):
                for kw in deco.keywords:
                    if kw.arg == "reason" and isinstance(kw.value, ast.Constant):
                        reason = kw.value.value
            results.append((node.lineno, reason))
    return results


def classify(reason, threshold_days, today):
    if reason.startswith("BLOCKER:"):
        return "BLOCKER"
    m = DATE_RE.search(reason)
    if not m:
        return "NO-DATE"
    try:
        d = datetime.strptime(m.group(1), "%Y-%m-%d").date()
        return "ZOMBIE" if (today - d).days > threshold_days else "FRESH"
    except ValueError:
        return "NO-DATE"


def main():
    args = parse_args()
    root = Path(args.path)
    today = date.today()
    zombie_count = 0

    print(f"xfail_audit  path={root}  threshold={args.days}days  today={today}\n")

    for f in sorted(root.rglob("test_*.py")):
        hits = extract_xfails(f)
        for lineno, reason in hits:
            cls = classify(reason, args.days, today)
            if cls == "FRESH":
                continue
            rel = f.relative_to(Path("."))
            print(f"  [{cls:<8}] {rel}:{lineno}")
            if reason:
                print(f"             reason: {reason}")
            if cls == "ZOMBIE":
                zombie_count += 1

    print(f"\n合計 ZOMBIE={zombie_count}")
    sys.exit(1 if zombie_count > 0 else 0)


if __name__ == "__main__":
    main()