---
title: POC 自動化測試 — 2-2-2 搜尋功能收斂報告
tagline: 把「人工 selector + AI 寫測試」黑箱流程跑通
date: YYYY-MM-DD  # 收斂當日填
author: Golden
duration_minutes: 15
audience: 內部技術分享
---

> **使用方式**：本檔為 `make-pptx` 素材範本。P4 (2-2-2-B) 全綠 + P5 部分啟動時，
> 複製為 `YYYYMMDD-poc-2-2-2-收斂.md`（用實際日期替換），把每個 `{{...}}` 占位符填好，
> 再呼叫 `make-pptx` skill 產簡報。**不要直接編輯本檔**（保持為乾淨範本）。

## 1. 專案簡介

- 受測系統：高雄數位市民活動模組 dev-maas.foxconn.com
- 技術棧：Python + Playwright + pytest（黑箱）
- 範圍：WBS 工項 2-2-2 搜尋功能（A/B/C/D 中 B/C/D 完成、A 因權限工項排除）
- 期程：{{YYYY-MM-DD}} ～ {{YYYY-MM-DD}}

## 2. 初始 Prompt

> 引自 `prompts/00_初始提示詞.md`（或對應檔）：
>
> {{貼上驅動本次 POC 的最初指令；保留原話、不縮寫}}

## 3. 過程 Prompt 摘要（重要轉折點，最多 5 個）

引自 `prompts/99_重點經驗.md`：

1. **2026-04-30 token 教訓**：AI selector trial-and-error → 改人工 codegen 優先
2. **2026-04-30 DOM 是唯一事實**：`Components.STFilter.Apply` i18n vs DOM 文字差異案例
3. **2026-04-30 PrimeVue 動態 ID 規避**：改用語意 selector / 語意 class
4. **2026-04-30 Playwright 1.48 sessionStorage workaround**：`add_init_script` 還原
5. **2026-05-05 STATUS.md + harness scaffold**：跨 session 進度錨點落地

> 收斂時請依實際情況增刪、補充新轉折點。

## 4. 套件依賴

引自 `requirements.txt`（摘錄重點）：

```
{{playwright==1.48.x}}
{{pytest==x.x.x}}
{{pytest-playwright==x.x.x}}
{{...}}
```

## 5. Skill 依賴

- `harness-engineer`：建立本次的 plan.md / STATUS.md / CLAUDE.md / docs / notes 鷹架（2026-05-05 init）
- `make-pptx`：本檔產簡報的 skill
- {{若有用到其他 skill 在此補充}}

## 6. 成效數據

- **測試覆蓋工項**：{{覆蓋 X 個工項 / Y 個 case}}
- **每場節省人工分鐘**：{{原 X 分鐘 → 自動化 Y 分鐘}}
- **Token 用量**：
  - 改採人工 codegen 前：1 天額度跑完 4 case 即耗盡
  - 改採人工 codegen 後：{{X tokens / case}}（節省 ~Y%）
- **執行穩定度**：連續 {{N}} 次 nightly run，failure rate {{Z%}}

## 7. 關鍵截圖

放在 `notes/assets/` 下：

- `assets/{{YYYYMMDD}}-2-2-2-B-綠燈.png`
- `assets/{{YYYYMMDD}}-report-markdown.png`
- `assets/{{YYYYMMDD}}-trace-zip-screenshot.png`

> 截圖檔名建議含日期，便於後續追溯。

## 8. 後續展望

- **P5 補齊 2-2-2-C/D + nightly schedule**
- **P6 前端配合加 `data-testid`**：取消 selector 維護成本
- **P7 推廣到第二個活動站驗證可複製性**
- **CI 整合（可選）**：見 `plan.md` Q3，視協作者人數決定
