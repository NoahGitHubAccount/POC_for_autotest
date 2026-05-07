# POC_for_autotest — 高雄數位市民活動模組自動化測試

依工項編號（WBS）驅動的網站黑箱自動化測試，搭配 AI 協作的規格轉化、案例展開、夜間排程執行與 Markdown 報告。

## 快速開始（Win11）

```powershell
# 1. 建虛擬環境並安裝依賴
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium

# 2. 建立本機設定（含帳密；不會被 git 追蹤）
copy config\config.example.yaml config\config.local.yaml
# 用編輯器填入 username / password / bound_organizers

# 3. 冒煙測試（P1 完成後可用）
python tools\run.py --smoke

# 4. 跑指定工項（P5 完成後可用）
python tools\run.py --wbs 2-2-2-A
```

## 目錄結構

```
POC_for_autotest/
├── config/          設定範例與本機設定
├── specs/           需求規格 md（從 PDF 展開，依工項分目錄）
├── tests/           pytest 測試案例（依工項分目錄）
├── reports/         測試報告（每次執行一個 run 目錄，含 docx 整併版）
├── lib/             共用模組（auth/config/md_reporter/selectors）
├── tools/           CLI 入口與一次性工具（run/extract_pdf/md_to_docx/explore_page/warm_login）
├── prompts/         工程化提示詞庫（可跨專案重用）
├── docs/            人類向延伸文件（工具指令集、合作SOP）
├── notes/           簡報素材庫（餵 make-pptx skill）
└── .auth/           登入態儲存（gitignored）
```

## 文件導讀

- `STATUS.md` — **session 開場先看這份**：當前進度、最近決議、下一步
- `WBS.md` — 工項階層清單（驅動測試的索引）
- `plan.md` — 階段化任務計畫
- `CLAUDE.md` — Agent 地圖（行為約束、子文件指向）
- `docs/工具指令集.md` — **CLI 速查**（產 word 報告、跑測試、warm-login、explore_page）
- `docs/合作SOP_QA.md` — 人機合作 SOP（每週工作流、跨 session 接手）
- `prompts/README.md` — 提示詞工具庫導覽（00_專案發起 → 99_重點經驗）
- `prompts/99_重點經驗.md` — 持續累積的踩坑筆記
- `高雄數位市民活動模組需求.pdf` — 規格來源

## 階段進度

> 詳細展開見 `plan.md`；當前進度的 WBS 級別見 `STATUS.md`。

- [x] P0 環境初始化
- [x] P1 登入骨架（warm-login + storageState + sessionStorage）
- [x] P2 報告器與 Runner（`lib/md_reporter.py` + `tools/run.py`）
- [x] P3 規格展開試點（2-2-2 A–D 4 份 spec）
- [x] P4 案例試點（2-2-2-B：12 PASS / 2 XFAIL / 1 SKIP）
- [x] P5 補齊 2-2-2-C/D（C 5/4 + D 5/3，xfail 含 multiselect 互動）
- [x] P5.5 報告交付（截圖 + docx 整併）
- [ ] P4.5 工項擴展（2-2-3 / 2-2-4 / 2-2-5-A / 2-2-5-B / 2-3-13）
- [ ] P5.7 夜間排程（Windows 工作排程器）
- [ ] P6 前端 meta 同步（待前端加 data-testid）
- [ ] P7 工程化文件 + Skills 上架
