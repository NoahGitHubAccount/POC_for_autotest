#!/usr/bin/env python3
"""偵測 WBS 工項中缺少 spec 的清單，輸出 gap 報告。

只對「可自動化」工項（標籤 AUTO 或未標，排除 MANUAL/INTEGRATION/SKIP/NOT-IMPL/BLOCKED/PARTIAL）
才列入 gap。標籤定義見 input/wbs_test_labels.md。

用法：
    python scripts/gen_missing_specs.py
    python scripts/gen_missing_specs.py --json    # 輸出 JSON（供腳本串接）
    python scripts/gen_missing_specs.py --all     # 列出全部（含非 AUTO）
"""
import re
import sys
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WBS_FILE = ROOT / "input" / "WBS.md"
LABELS_FILE = ROOT / "input" / "wbs_test_labels.md"
SPECS_DIR = ROOT / "specs"

# 這些標籤不納入自動化 gap 偵測
_NON_AUTO_LABELS = {"MANUAL", "INTEGRATION", "SKIP", "NOT-IMPL", "BLOCKED", "PARTIAL"}


def load_labels() -> dict[str, str]:
    """從 wbs_test_labels.md 讀取 {wbs_id: label} 對照表。"""
    if not LABELS_FILE.exists():
        return {}
    labels: dict[str, str] = {}
    text = LABELS_FILE.read_text(encoding="utf-8")
    # 解析 markdown 表格行：| `2-1-1` | 名稱 | `SKIP` | 理由 |
    for m in re.finditer(r'^\|\s*`([\w\d.-]+[-][\w\d-]+)`\s*\|[^|]*\|\s*`([A-Z-]+)`\s*\|', text, re.MULTILINE):
        labels[m.group(1)] = m.group(2)
    return labels


def extract_wbs_ids(wbs_text: str) -> list[tuple[str, str]]:
    """從 WBS.md 抽取 (ID, 名稱) 清單（去重）。"""
    seen: set[str] = set()
    items: list[tuple[str, str]] = []

    for m in re.finditer(r'^#{1,4}\s+([\d][\d\w.-]*[-][\d\w-]+)\s*(.*?)$', wbs_text, re.MULTILINE):
        wid = m.group(1).strip()
        name = re.sub(r'\s*\(.*?\)', '', m.group(2)).strip()
        if wid not in seen:
            seen.add(wid)
            items.append((wid, name))

    for m in re.finditer(r'^[-*]\s+([\d][\d\w.-]*[-][\d\w-]+)\s+(.*?)$', wbs_text, re.MULTILINE):
        wid = m.group(1).strip()
        name = re.sub(r'\s*\(.*?\)', '', m.group(2)).strip()
        if wid not in seen:
            seen.add(wid)
            items.append((wid, name))

    return items


def get_existing_spec_ids() -> set[str]:
    """回傳 specs/ 下已存在目錄的 WBS ID 集合。"""
    if not SPECS_DIR.exists():
        return set()
    ids: set[str] = set()
    for d in SPECS_DIR.iterdir():
        if d.is_dir():
            m = re.match(r'^([\d][\d\w.-]*[-][\d\w-]+)', d.name)
            if m:
                ids.add(m.group(1))
    return ids


def _wbs_ancestor_ids(wid: str) -> list[str]:
    """回傳 WBS ID 的所有父層前綴。
    例：'2-2-5-A-a' → ['2-2-5-A', '2-2-5', '2-2', '2']
    """
    parts = wid.split("-")
    ancestors = []
    for i in range(len(parts) - 1, 0, -1):
        ancestors.append("-".join(parts[:i]))
    return ancestors


def is_covered(wid: str, existing: set[str]) -> bool:
    """回傳 True 若 wid 本身或任意父層前綴已有 spec 目錄。"""
    if wid in existing:
        return True
    return any(anc in existing for anc in _wbs_ancestor_ids(wid))


def main():
    parser = argparse.ArgumentParser(description="偵測缺少 spec 的 WBS 工項")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式輸出")
    parser.add_argument("--all", action="store_true", help="列出全部工項（含非 AUTO）")
    args = parser.parse_args()

    if not WBS_FILE.exists():
        print(f"[ERROR] 找不到 {WBS_FILE}", file=sys.stderr)
        sys.exit(1)

    wbs_text = WBS_FILE.read_text(encoding="utf-8")
    labels = load_labels()
    all_items = extract_wbs_ids(wbs_text)
    existing = get_existing_spec_ids()

    def item_label(wid: str) -> str:
        return labels.get(wid, "AUTO")

    auto_items = [(w, n) for w, n in all_items if item_label(w) == "AUTO"]
    skipped_items = [(w, n, item_label(w)) for w, n in all_items if item_label(w) != "AUTO"]

    missing_auto = [(w, n) for w, n in auto_items if not is_covered(w, existing)]

    if args.json:
        print(json.dumps({
            "total": len(all_items),
            "auto": len(auto_items),
            "existing": len(existing),
            "missing": [{"id": w, "name": n} for w, n in missing_auto],
        }, ensure_ascii=False, indent=2))
        return

    print("## Spec Gap 報告\n")
    print(f"- WBS 總工項（去重）：{len(all_items)}")
    print(f"- 可自動化工項（AUTO）：{len(auto_items)}")
    print(f"- 已有 spec 目錄：{len(existing)}")
    print(f"- **缺少 spec（AUTO）：{len(missing_auto)}**\n")

    if missing_auto:
        print("### 缺少 spec 的可自動化工項\n")
        print("| WBS ID | 名稱 |")
        print("|---|---|")
        for wid, name in missing_auto:
            print(f"| `{wid}` | {name} |")
        print()
        print("> 後續行動：使用 prompts/10_PDF轉規格 提示詞，逐項產出 spec md。")
    else:
        print("✅ 所有可自動化工項均已有 spec 目錄。")

    if args.all and skipped_items:
        print("\n### 非 AUTO 工項（排除在 gap 偵測外）\n")
        print("| WBS ID | 名稱 | 標籤 |")
        print("|---|---|---|")
        for wid, name, label in skipped_items:
            print(f"| `{wid}` | {name} | `{label}` |")


if __name__ == "__main__":
    main()
