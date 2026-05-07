# POC_for_autotest Notes

> 此目錄為 **`make-pptx` skill 的素材源**。POC 收斂或里程碑達成時，在此建立一份 md 檔案，再呼叫 make-pptx 產出簡報。

## 命名規則

`YYYYMMDD-topic-slug.md`

範例：
- `20260601-poc-收斂報告.md`
- `20260615-自動化測試成效彙報.md`

## 必含 Schema

每份素材檔頭部必含 YAML frontmatter：

```yaml
---
title: 簡報主題
tagline: 一句話定位
date: YYYY-MM-DD
author: Golden
duration_minutes: 15
audience: 內部技術分享 / 客戶提案 / 主管彙報
---
```

主體必含區塊（依序）：

1. `## 1. 專案簡介`
2. `## 2. 初始 Prompt`（驅動專案的最初指令，引自 `prompts/00_專案發起_提示詞.md`）
3. `## 3. 過程 Prompt 摘要`（重要轉折點，最多 5 個；可引自 `prompts/99_重點經驗.md`）
4. `## 4. 套件依賴`（`requirements.txt` 摘錄）
5. `## 5. Skill 依賴`（用到哪些 `.claude/skills/`，例如 harness-engineer、make-pptx）
6. `## 6. 成效數據`（測試覆蓋工項數、節省人工分鐘 / 場、token 用量）
7. `## 7. 關鍵截圖`（指向 `notes/assets/` 下圖片）
8. `## 8. 後續展望`

## 與 make-pptx 對接

```
notes/YYYYMMDD-topic.md
       ↓
   make-pptx
       ↓
 Pandoc Markdown
       ↓
     PPTX
```

## 子目錄

- `assets/`：截圖、圖表（PNG / JPG）
- `archive/`：超過一年的舊素材歸檔

## 反模式

- ❌ 放零散筆記、未結構化（make-pptx 讀不到）
- ❌ 跳過 frontmatter（沒有標題頁）
- ❌ 截圖用外部 URL（離線無法生成）
- ❌ 單檔超過 1000 字（簡報塞不下）

## 目前狀態

P5 / P5.5 已完成（2-2-2 全工項綠燈 + docx 交付能力）。

| 檔案 | 日期 | 對應 milestone |
|---|---|---|
| `_template-poc-收斂.md` | — | 範本（不直接編輯） |
| `20260508-poc-2-2-2-收斂.md` | 2026-05-08 | 第一份素材：2-2-2 收斂 + 工程化骨架沉澱 |

下一份預計：P4.5 全部跑完後（2-2-5-A/B + 2-3-13 結果分析 + XPASS 解 xfail 完成），產 `YYYYMMDD-poc-P4.5-收尾.md`。
