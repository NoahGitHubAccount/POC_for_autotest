#!/usr/bin/env python3
"""偵測 spec 存在但缺少對應 test 的清單，輸出 gap 報告。

排除規則：
  1. spec 的 `測試範圍: false`（或缺失）
  2. wbs_test_labels.md 中標為 BLOCKED/SKIP/NOT-IMPL/MANUAL/INTEGRATION/PARTIAL 的工項

子層覆蓋：若父層 spec 目錄的 WBS ID 下有任何子項已有 tests/ 目錄，則視為已覆蓋。

用法：
    python scripts/gen_missing_tests.py
    python scripts/gen_missing_tests.py --json
"""
import re
import sys
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECS_DIR = ROOT / "specs"
TESTS_DIR = ROOT / "tests"
LABELS_FILE = ROOT / "input" / "wbs_test_labels.md"

_NON_AUTO_LABELS = {"MANUAL", "INTEGRATION", "SKIP", "NOT-IMPL", "BLOCKED", "PARTIAL"}


def load_labels() -> dict[str, str]:
    """從 wbs_test_labels.md 讀取 {wbs_id: label} 對照表。"""
    if not LABELS_FILE.exists():
        return {}
    labels: dict[str, str] = {}
    text = LABELS_FILE.read_text(encoding="utf-8")
    for m in re.finditer(r'^\|\s*`([\w\d.-]+[-][\w\d-]+)`\s*\|[^|]*\|\s*`([A-Z-]+)`\s*\|', text, re.MULTILINE):
        labels[m.group(1)] = m.group(2)
    return labels


def get_testable_spec_dirs(labels: dict[str, str]) -> list[tuple[str, str]]:
    """回傳 測試範圍: true 且標籤為 AUTO（或無標）的 spec 目錄 (wbs_id, dir_name) 清單。"""
    result: list[tuple[str, str]] = []
    if not SPECS_DIR.exists():
        return result

    for spec_dir in sorted(SPECS_DIR.iterdir()):
        if not spec_dir.is_dir():
            continue
        m = re.match(r'^([\d][\d\w.-]*[-][\d\w-]+)', spec_dir.name)
        if not m:
            continue
        wbs_id = m.group(1)

        # 若標籤為非 AUTO，排除
        if labels.get(wbs_id, "AUTO") in _NON_AUTO_LABELS:
            continue

        # 確認 spec 目錄內有任一 md 含 "測試範圍: true"
        for md in spec_dir.glob("*.md"):
            try:
                text = md.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if re.search(r'測試範圍\s*:\s*true', text, re.IGNORECASE):
                result.append((wbs_id, spec_dir.name))
                break

    return result


def get_existing_test_ids() -> set[str]:
    """回傳 tests/ 下已存在且含 test_*.py 的 WBS ID 集合。"""
    if not TESTS_DIR.exists():
        return set()
    ids: set[str] = set()
    for d in TESTS_DIR.iterdir():
        if not d.is_dir():
            continue
        m = re.match(r'^([\d][\d\w.-]*[-][\d\w-]+)', d.name)
        if not m:
            continue
        if any(d.glob("test_*.py")):
            ids.add(m.group(1))
    return ids


def is_test_covered(wbs_id: str, existing: set[str]) -> bool:
    """回傳 True 若 wbs_id 本身或任意子項已有 tests 目錄。"""
    if wbs_id in existing:
        return True
    # 子層覆蓋：existing 中有以 wbs_id 為前綴的更細粒度工項
    prefix = wbs_id + "-"
    return any(eid.startswith(prefix) for eid in existing)


def main():
    parser = argparse.ArgumentParser(description="偵測缺少 test 的 spec 目錄")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式輸出")
    args = parser.parse_args()

    labels = load_labels()
    testable = get_testable_spec_dirs(labels)
    existing = get_existing_test_ids()
    missing = [(wid, dname) for wid, dname in testable if not is_test_covered(wid, existing)]

    if args.json:
        print(json.dumps({"testable": len(testable), "existing": len(existing),
                          "missing": [{"id": w, "dir": d} for w, d in missing]},
                         ensure_ascii=False, indent=2))
        return

    print("## Test Gap 報告\n")
    print(f"- 可測試 spec 目錄（AUTO + 測試範圍: true）：{len(testable)}")
    print(f"- 已有 tests/ 目錄（直接或子層覆蓋）：{len(testable) - len(missing)}")
    print(f"- **缺少 test：{len(missing)}**\n")

    if missing:
        print("### 缺少 test 的 spec\n")
        print("| WBS ID | Spec 目錄 |")
        print("|---|---|")
        for wid, dname in missing:
            print(f"| `{wid}` | `specs/{dname}/` |")
        print()
        print("> 後續行動：使用 prompts/20_生成測試案例 提示詞，逐項產出 test_*.py。")
    else:
        print("✅ 所有可測試 spec 均已有 test 目錄（直接或子層覆蓋）。")


if __name__ == "__main__":
    main()
