"""從 PDF 抽指定頁文字輸出，給 AI 後續轉成 spec md 用。

用法：
    python tools/extract_pdf_text.py --pages 17                # 單頁
    python tools/extract_pdf_text.py --pages 17,18,19          # 多頁
    python tools/extract_pdf_text.py --pages 17-20             # 範圍
    python tools/extract_pdf_text.py --pages 17 --out spec.txt # 輸出到檔案
    python tools/extract_pdf_text.py --pdf 自訂.pdf --pages 1-3

預設 PDF 為專案根目錄下的「需求規格.pdf」（user 本機自行命名 / rename 對應）。
若你的 PDF 檔名不同，請傳 --pdf 指定。
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

import pdfplumber

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PDF = PROJECT_ROOT / "需求規格.pdf"


def parse_pages(spec: str) -> list[int]:
    out: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return sorted(out)


def extract(pdf_path: Path, pages: list[int]) -> str:
    chunks: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        for p in pages:
            if not (1 <= p <= total):
                print(f"略過 p.{p}（PDF 共 {total} 頁）", file=sys.stderr)
                continue
            text = pdf.pages[p - 1].extract_text() or ""
            chunks.append(f"===== PAGE {p} =====\n{text}")
    return "\n\n".join(chunks)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", default=str(DEFAULT_PDF))
    parser.add_argument("--pages", required=True, help="頁碼，如 17 或 17-20 或 17,18")
    parser.add_argument("--out", help="輸出檔（預設 stdout）")
    args = parser.parse_args()

    pages = parse_pages(args.pages)
    text = extract(Path(args.pdf), pages)

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"已寫入 {args.out}（{len(text)} chars）", file=sys.stderr)
    else:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
