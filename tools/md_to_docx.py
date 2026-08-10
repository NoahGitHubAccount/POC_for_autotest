"""將 reports/<rid>_run/*.md 整併轉成單份 docx。

針對 md_reporter.py 的輸出格式做 line-based parser，支援：
- # / ## / ### 標題
- | 表格（含 separator 行）
- ```...``` code block
- ![alt](path) 圖片（path 相對 md 解析；用 BytesIO 顯式嵌入）
- - 列表
- 一般段落

整併規則：`_summary.md` 在最前，其餘工項報告依檔名排序，之間插 page break。
輸出單檔：`reports/<rid>_run/docx/<rid>_run_測試報告.docx`

不支援巢狀結構或一般化 markdown；reporter 不會產出複雜 markdown，足夠交付用。

用法：
    python tools/md_to_docx.py                 # 轉最新一筆 run
    python tools/md_to_docx.py 20260506_2030   # 轉指定 run
"""
from __future__ import annotations
import argparse
import re
import sys
from io import BytesIO
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Emu, Inches, Pt
except ImportError:
    print(
        "缺少 python-docx 依賴。請執行：pip install python-docx==1.1.2",
        file=sys.stderr,
    )
    raise

REPORTS_DIR = PROJECT_ROOT / "reports"

H_RE = re.compile(r"^(#{1,4})\s+(.*)$")
HR_RE = _HR_RE = re.compile(r"^\s*([-*_])(?:\s*\1){2,}\s*$")  # markdown 水平分隔線
TABLE_RE = re.compile(r"^\|(.*)\|\s*$")
TABLE_SEP_RE = re.compile(r"^\|[\s\-:|]+\|\s*$")
# 用 greedy `.+`：alt 與 path 都可能含 `[chromium]`（pytest-playwright 標籤），
# 不能用 `[^\]]*`/`[^)]+`——會在第一個 `]` 就停而對不上後面 `](`
IMG_RE = re.compile(r"^!\[(.+)\]\((.+)\)\s*$")
LIST_RE = re.compile(r"^- (.*)$")
FENCE_RE = re.compile(r"^```")
LINK_INLINE_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
BOLD_INLINE_RE = re.compile(r"\*\*(.+?)\*\*")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")


def _strip_inline_md(text: str) -> str:
    text = LINK_INLINE_RE.sub(r"\1", text)
    text = BOLD_INLINE_RE.sub(r"\1", text)
    text = INLINE_CODE_RE.sub(r"\1", text)
    return text


#: A4 直式扣掉頁邊距後的可用寬高（吋）；長截圖須等比縮到一頁內，否則會被切斷或撐爆版面
_MAX_W_IN = 6.0
_MAX_H_IN = 8.6

#: 需另起新頁的標題層級（2026-07-31 交付要求：章節標題一律起始於頁首）。
#: H2＝主章節（摘要／一、二、三…）、H3＝各案子章節；H1 是文件主標題不分頁。
#: ⚠ 案例型報告（上百個 H3）務必用 `--break-levels 2`，否則每案一頁會膨脹成上百頁。
_PAGE_BREAK_LEVELS = {2, 3}


def _embed_picture(doc, img_path: Path) -> None:
    """讀檔成 BytesIO 再丟給 add_picture，確保是嵌入而非任何形式的連結。

    尺寸策略：預設寬 6 吋；**若等比放大後高度超過一頁可用高度，改以高度為準等比縮小**
    （2026-07-31：手機長截圖以固定寬度嵌入後高達 13 吋，跨頁被截斷）。
    """
    with open(img_path, "rb") as f:
        data = f.read()
    doc.add_picture(BytesIO(data), width=Inches(_MAX_W_IN))
    pic = doc.inline_shapes[-1]
    h_in = pic.height / 914400  # EMU → inch
    if h_in > _MAX_H_IN:
        ratio = _MAX_H_IN / h_in
        pic.height = Inches(_MAX_H_IN)
        pic.width = Inches(_MAX_W_IN * ratio)


def _append_md_to_doc(doc, md_path: Path) -> None:
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    base_dir = md_path.parent

    in_code = False
    code_buf: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if FENCE_RE.match(line):
            if in_code:
                if code_buf:
                    p = doc.add_paragraph()
                    run = p.add_run("\n".join(code_buf))
                    run.font.name = "Consolas"
                    run.font.size = Pt(9)
                code_buf = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        m = H_RE.match(line)
        if m:
            level = len(m.group(1))
            h = doc.add_heading(_strip_inline_md(m.group(2)), level=level)
            # 章節標題起始於新頁：用 page_break_before 屬性（非 add_page_break()，
            # 後者會多插一個空段落）。H1 為文件主標題、且首個標題不需要分頁。
            if level in _PAGE_BREAK_LEVELS and len(doc.paragraphs) > 1:
                h.paragraph_format.page_break_before = True
            i += 1
            continue

        m = IMG_RE.match(line)
        if m:
            alt = m.group(1)
            from urllib.parse import unquote
            rel = unquote(m.group(2))  # 彙整報告路徑為 URL 編碼（%20/%E5…），先還原
            img_path = (base_dir / rel).resolve()
            if img_path.exists():
                try:
                    _embed_picture(doc, img_path)
                    if alt:
                        cap = doc.add_paragraph(alt)
                        if cap.runs:
                            cap.runs[0].italic = True
                except Exception as e:
                    doc.add_paragraph(f"[圖片載入失敗：{img_path.name} — {e}]")
            else:
                doc.add_paragraph(f"[找不到圖片：{rel}]")
            i += 1
            continue

        if TABLE_RE.match(line):
            tbl_lines = []
            while i < len(lines) and TABLE_RE.match(lines[i]):
                tbl_lines.append(lines[i])
                i += 1
            _emit_table(doc, tbl_lines)
            continue

        m = LIST_RE.match(line)
        if m:
            doc.add_paragraph(_strip_inline_md(m.group(1)), style="List Bullet")
            i += 1
            continue

        # markdown 水平分隔線（---／***／___）：章節已用 page_break_before 另起新頁，
        # 這些線在 docx 只會變成一行「---」文字雜訊 → 直接略過（2026-07-31）
        if _HR_RE.match(line):
            i += 1
            continue

        if line.strip():
            doc.add_paragraph(_strip_inline_md(line))
        else:
            doc.add_paragraph("")
        i += 1


#: 欄寬分配上下限（交付要求：欄寬不得等寬，依內容比例配置）。
#: 下限避免「#」「層級」這種一兩個字的欄位窄到字被折行；上限避免單一長文字欄吃掉整張表。
_MIN_COL_SHARE = 0.045
_MAX_COL_SHARE = 0.45
#: 極窄欄（流水編號）的權重地板，純比例會讓 1 字元欄只分到 0.7% 而擠成兩行
_NARROW_WEIGHT_FLOOR = 4


def _disp_len(s: str) -> int:
    """顯示寬度：中文與全形符號算 2，其餘算 1。"""
    return sum(2 if ord(ch) > 0x2E80 else 1 for ch in s)


def _col_shares(rows: list[list[str]], cols: int) -> list[float]:
    """依各欄最長內容分配欄寬比例，並套用上下限後重新分配剩餘寬度。"""
    w = [max(_NARROW_WEIGHT_FLOOR,
             max((_disp_len(r[c]) for r in rows if c < len(r)), default=1))
         for c in range(cols)]
    tot = float(sum(w)) or 1.0
    share = [x / tot for x in w]
    for _ in range(4):                      # 迭代收斂：夾限後把剩餘寬度按比例補回自由欄
        fixed = {i: (_MIN_COL_SHARE if s < _MIN_COL_SHARE else _MAX_COL_SHARE)
                 for i, s in enumerate(share)
                 if s < _MIN_COL_SHARE or s > _MAX_COL_SHARE}
        if not fixed:
            break
        free = [i for i in range(cols) if i not in fixed]
        rest = max(0.0, 1.0 - sum(fixed.values()))
        base = sum(share[i] for i in free) or 1.0
        share = [fixed.get(i, share[i] / base * rest) for i in range(cols)]
    return share


def _apply_col_widths(doc, tbl, rows: list[list[str]], cols: int) -> None:
    """把表格設為固定版面並依內容比例配欄寬（撐滿版面可用寬度）。"""
    sec = doc.sections[-1]
    usable = sec.page_width - sec.left_margin - sec.right_margin
    tbl.autofit = False
    tblPr = tbl._tbl.tblPr
    layout = tblPr.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tblPr.append(layout)
    layout.set(qn("w:type"), "fixed")       # 缺這行 Word 會自行 autofit，欄寬設定形同無效
    for i, share in enumerate(_col_shares(rows, cols)):
        w = Emu(int(usable * share))
        tbl.columns[i].width = w
        for cell in tbl.columns[i].cells:   # gridCol 與每格 tcW 都要設，Word 才會照辦
            cell.width = w


def _emit_table(doc, table_lines: list[str]) -> None:
    rows = []
    for ln in table_lines:
        if TABLE_SEP_RE.match(ln):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        rows.append(cells)
    if not rows:
        return
    cols = max(len(r) for r in rows)
    tbl = doc.add_table(rows=len(rows), cols=cols)
    try:
        tbl.style = "Light Grid Accent 1"
    except KeyError:
        pass
    for r_idx, row in enumerate(rows):
        for c_idx, cell in enumerate(row):
            tbl.rows[r_idx].cells[c_idx].text = _strip_inline_md(cell)
    _apply_col_widths(doc, tbl, [[_strip_inline_md(c) for c in r] for r in rows], cols)


def _ordered_md_files(run_dir: Path) -> list[Path]:
    summary = run_dir / "_summary.md"
    rest = sorted(p for p in run_dir.glob("*.md") if p.name != "_summary.md")
    return ([summary] if summary.exists() else []) + rest


def convert_run(run_id: str) -> Path:
    if run_id.endswith("_run"):
        run_dir = REPORTS_DIR / run_id
    else:
        run_dir = REPORTS_DIR / f"{run_id}_run"
    if not run_dir.is_dir():
        raise SystemExit(f"找不到 run 目錄：{run_dir}")

    md_files = _ordered_md_files(run_dir)
    if not md_files:
        raise SystemExit(f"{run_dir} 內無 md 檔可轉")

    doc = Document()
    for idx, md in enumerate(md_files):
        if idx > 0:
            doc.add_page_break()
        print(f"  → 併入 {md.name}")
        _append_md_to_doc(doc, md)

    out_dir = run_dir / "docx"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{run_dir.name}_測試報告.docx"
    doc.save(str(out_path))
    print(f"\n完成：{out_path.relative_to(PROJECT_ROOT)}")
    return out_path


def latest_run_id() -> str:
    runs = [p.name for p in REPORTS_DIR.iterdir() if p.is_dir() and p.name.endswith("_run")]
    if not runs:
        raise SystemExit("reports/ 內找不到任何 _run 目錄")
    return sorted(runs)[-1]


def _has_review_comments(docx_path: Path) -> int:
    """回傳該 docx 內的 Word 註解則數（讀不到或無註解回 0）。"""
    if not docx_path.exists():
        return 0
    try:
        import zipfile
        from xml.etree import ElementTree as ET
        with zipfile.ZipFile(docx_path) as z:
            if "word/comments.xml" not in z.namelist():
                return 0
            ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
            return len(ET.fromstring(z.read("word/comments.xml")).findall(ns + "comment"))
    except Exception:
        return 0


def convert_file(md_path: Path, out_path: Path | None = None, force: bool = False) -> Path:
    """單一 md → docx（圖片相對 md 位置解析；供定版/待審彙整報告轉檔）。

    ⚠ 覆寫保護：交付 docx 是**有狀態**檔案——使用者的 Word 審查註解與手調表格欄寬
    都只存在 docx 裡、md 沒有。整份重轉會靜默毀掉這些東西（2026-08-01 兩個會期同時
    產製本報告時實際發生）。因此偵測到目標檔含 Word 註解就中止，需 `--force` 才覆寫；
    正常情況下對已審查的交付檔應**就地 patch**，不要重轉。
    """
    md_path = md_path.resolve()
    if not md_path.is_file():
        raise SystemExit(f"找不到 md：{md_path}")
    out_path = (out_path or md_path.with_suffix(".docx")).resolve()

    n = _has_review_comments(out_path)
    if n and not force:
        raise SystemExit(
            f"[中止] {out_path.name} 內含 {n} 則 Word 審查註解，重轉會將其連同手調欄寬一併毀掉。\n"
            f"        審查結果請走 reports/final/審查核可紀錄.json ＋ 就地 patch；\n"
            f"        確定要整份覆寫請加 --force（建議先備份）。"
        )

    doc = Document()
    print(f"  → 轉換 {md_path.name}")
    _append_md_to_doc(doc, md_path)
    doc.save(str(out_path))
    print(f"\n完成：{out_path}")
    return out_path


def main() -> int:
    p = argparse.ArgumentParser(description="md_reporter 報告整併成單份 docx")
    p.add_argument(
        "run_id",
        nargs="?",
        help="run 目錄名（如 20260506_2030 或 20260506_2030_run）；省略則用最新一筆",
    )
    p.add_argument("--file", help="改轉單一 md 檔（如 reports/final/整合測試總報告.md）")
    p.add_argument("--out", help="輸出 docx 路徑（預設同名同目錄）。"
                                 "已通過冊交付檔名為『整合測試報告.docx』，與 md 檔名不同，需明示")
    p.add_argument("--force", action="store_true",
                   help="目標 docx 含 Word 審查註解時仍強制覆寫（會毀掉註解與手調欄寬）")
    p.add_argument("--break-levels", default="2,3",
                   help="哪些標題層級要另起新頁（逗號分隔，預設 2,3）。"
                        "案例型報告（上百個 H3）建議用 2，避免每案一頁")
    args = p.parse_args()

    global _PAGE_BREAK_LEVELS
    _PAGE_BREAK_LEVELS = {int(x) for x in str(args.break_levels).split(",") if x.strip()}

    if args.file:
        convert_file(Path(args.file),
                     Path(args.out) if args.out else None,
                     force=args.force)
        return 0
    run_id = args.run_id or latest_run_id()
    convert_run(run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
