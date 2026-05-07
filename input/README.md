# input/ — 人類輸入素材

> 此目錄收納「人類要統一填入」的輸入物，AI 會從這裡讀取啟動週期化工作流。
> **跨專案重用時，這裡是你最該替換的內容。**

## 必填內容

| 檔案 | 說明 | 是否進 git |
|---|---|---|
| `WBS.md` | 工項階層清單（驅動測試的索引） | ✅ |
| `需求規格.pdf` | 規格來源 PDF（user 本機放，不入 git） | ❌（gitignored） |

## 與其他目錄的關係

```
input/                    （人類輸入）
  ├── WBS.md             →  AI 讀取，依工項挑出當週要做的子項
  └── 需求規格.pdf        →  AI 跑 prompts/10_PDF轉規格 抽段落
                              ↓
specs/<wbs>/<id>.md       （AI 產出 spec md）
                              ↓ 人類 review
tests/<wbs>/test_*.py     （AI 寫 pytest）
                              ↓ 人類跑 pytest
reports/<rid>_run/         （產出）
                              ↓ tools/md_to_docx.py
reports/<rid>_run/docx/    （Word 交付件）
```

## 跨專案使用 input/

當你把這套骨架複製到別的專案時：

1. **替換 `WBS.md`** 為新專案的工項階層
2. **把新專案的需求 PDF 放這裡**，命名 `需求規格.pdf`（或在 `tools/extract_pdf_text.py --pdf` 指定其他檔名）
3. 其餘骨架（`lib/` `tools/` `prompts/` `docs/`）原樣保留

詳見 `docs/技術架構.md` §7「跨專案重用 checklist」。
