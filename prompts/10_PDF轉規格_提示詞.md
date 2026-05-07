# 10 — PDF 轉規格

## 使用時機
當週要新增測試的工項，需要先把 PDF 對應段落抽成 spec md 檔案。

## 必填參數
- **工項清單**：例 `2-2-2-A`、`2-2-2-B`、`2-2-2-C`、`2-2-2-D`
- **PDF 路徑**：預設 `需求規格.pdf`（位於專案根目錄；user 本機若用其他檔名請傳 `--pdf`）
- **WBS.md**：用於對應工項標題與父工項

## 期望輸出
每個工項一份 spec md，存放於 `specs/<父工項編號 父工項標題>/<工項編號 工項標題>.md`，外加一份父工項 `_index.md`。

## 標準流程

### 步驟 1：定位 PDF 頁碼
1. 跑 `python tools/extract_pdf_text.py --pages <range> --out .tmp_dump.txt` 把候選頁文字輸出
2. 用 grep 找工項對應段落：例如 `2-2 搜尋|主辦單位|重置`
3. 確認頁碼 + 段落字母（A/B/C/D...）

### 步驟 2：產出 spec md
依下列**標準骨架**寫入。所有區塊註解必須完整保留，**不要省略**任何 AI-MANAGED 標記。

```markdown
---
工項編號: <ID>
父工項: <父 ID> <父標題>
規格頁碼: <PDF 頁碼>
測試範圍: true|false
最後更新: <YYYY-MM-DD>
ai_generated_at: <YYYY-MM-DDTHH:MM:SS+08:00>
manual_edits: false
---

# <ID> <標題>

## 規格原文（PDF p.<頁碼>）
<!-- AI-MANAGED START: spec-original -->
（從 PDF 抽取的原文，逐字保留，不重寫）
<!-- AI-MANAGED END: spec-original -->

## 驗收條件 (AC)
<!-- AI-MANAGED START: acceptance-criteria -->
- **AC1**: ...
- **AC2**: ...
<!-- AI-MANAGED END: acceptance-criteria -->

## 待釐清
- [ ] ...

## 使用者註記
<!-- USER-EDIT START -->

<!-- USER-EDIT END -->

## 變更紀錄
<!-- AI-CHANGELOG START -->
- <YYYY-MM-DD> 初次生成（PDF p.<頁碼>，<段落>）
<!-- AI-CHANGELOG END -->
```

### 步驟 3：撰寫 AC 的原則
- AC 要可驗證、單一行為、有明確主詞與動詞
- 命名 `**AC<n>**：<行為與預期>`
- 推測性的 AC 必須在「待釐清」列出
- 屬於權限邊界、僅作為知識保留的工項，`測試範圍: false`，不寫 AC，改寫「解讀」區塊

### 步驟 4：寫 `_index.md`
父工項一份，列出所有子工項與測試範圍狀態，含 PDF 原文。

## 冪等性規則（修訂時）
- **AI-MANAGED START/END** 區塊：可由 AI 重生覆寫
- **USER-EDIT START/END** 區塊：永遠保留，AI 重生時跳過
- 修訂時：
  1. 對比新舊 AI-MANAGED 內容
  2. 若有變更，在 AI-CHANGELOG 加一行 `- <日期> 修訂：<摘要>`
  3. 更新 frontmatter 的 `最後更新` 與 `ai_generated_at`
  4. 不要動 frontmatter 的 `manual_edits`（由使用者手動標）

## 檔名規則
- `<工項編號> <中文標題>.md`
- 半形 `/` 一律以 `、` 取代（避免 Windows 檔名衝突）
- 全形括號保留、空格保留

## 已知踩坑
- pdfplumber 抽中文時引號可能變成 `"` `"`，**保留原貌**不要改成半形 `"`
- PowerShell stdout 中文亂碼是顯示問題，PDF 抽取的內容本身正確
- 跨頁的段落需要用 `--pages 17,18` 多頁合併
