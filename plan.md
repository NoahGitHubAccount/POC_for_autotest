# POC_for_autotest 任務計畫

> 建立日期：2026-05-05
> 作者：Golden
> 變動高頻欄位請改 `STATUS.md`；本檔只放階段化大方向。

## 目標

為高雄數位市民活動模組（dev-maas.foxconn.com）建構一套以 WBS 工項為驅動單位、可夜間排程、輸出 Markdown 報告的黑箱自動化測試 POC，驗證後續可推廣到其他類似活動站。

## 驗收條件

- [x] **P0 環境初始化**：venv、依賴、Playwright Chromium、`config.local.yaml` 範本可運作
- [x] **P1 登入骨架**：warm-login + storageState + sessionStorage workaround 已上線
- [x] **P2 報告器與 Runner**：`tools/run.py --smoke/--warm-login` + `lib/md_reporter.py` Markdown 報告
- [x] **P3 規格展開試點**：`specs/2-2-2 搜尋功能/` A–D 4 份 + `_index.md` 完成
- [x] **P4 案例試點**：2-2-2-B 12 PASS / 2 XFAIL / 1 SKIP（共 15 case）
- [ ] **P4.5 工項擴展**：2-2-3 ✅ / 2-2-4 ✅（重跑驗 xfail 中）/ 2-2-5-A ✅（待跑）/ 2-2-5-B ✅（待跑）/ 2-3-13 ✅（待跑）；2-3-1、2-2-4-H 排除
- [x] **P5 補齊 2-2-2-C/D**：C 4 PASS + 1 XFAIL；D 3 PASS + 1 XFAIL + 1 SKIP（夜間排程拆到 P5.7）
- [x] **P5.5 報告交付能力**：`--shot=failed_only|always|off` + `tools/md_to_docx.py` 整併版 docx
- [ ] **P5.7 夜間排程**（從 P5 拆出）：Windows 工作排程器啟動 nightly run；待 P4.5 全部跑完才接
- [ ] **P6 前端 meta 同步**：自動抽 `data-testid` / route / i18n 表（待前端配合加 testid）
- [ ] **P7 工程化沉澱**：`prompts/` 完整化（✅ 00/10/20/30/40/99 全到位 2026-05-08）、`docs/技術架構.md` ✅、`notes/` 第一份素材 ✅；待：push 到 NoahGitHubAccount

---

## Phase P3 / P4 / P5 / P5.5 — 已完成

歷史展開細節壓縮，狀態與當下動作見 `STATUS.md`。重點：
- P3：specs/2-2-2 4 份完成
- P4：2-2-2-B 試點通過（含 4 步 selector 流程沉澱）
- P5：2-2-2-C/D 補齊（C 5/4，D 5/3）
- P5.5：截圖能力 + docx 整併輸出已驗證

## Phase P4.5 — 工項擴展（進行中）

- **本批工項**：2-2-3 / 2-2-4 / **2-2-5-A** / 2-2-5-B / 2-3-13
- **跳過**：2-3-1 時間格式（ROI 低）、2-2-4-H（前置 2-3-2/2-3-11 未完）、2-2-5-A-e/g（待業務確認）
- **狀態**：所有 spec + test 已產出；2-2-3 / 2-2-4 已跑（待重跑驗 xfail），2-2-5-A / 2-2-5-B / 2-3-13 已跑（user 整理結果中）
- **新依賴**：`openpyxl==3.1.5`（已加入 requirements.txt，使用者授權）
- **重要決議（2026-05-07）**：
  1. 本機 src 是舊版，30 個原 SKIP-pending 改 xfail(strict=False) 先跑；XPASS 即「測試機已實作、可解 xfail」訊號
  2. 日期輸入目前僅支援 `yyyy/mm/dd`，`-` 待前端支援；2-2-2-B AC8 / 2-3-13-G1 AC4 補格式相容測試（slash + dash xfail）；同時揭露 AC5 寬鬆斷言可能造成的偽綠
- **詳細進度**：見 `STATUS.md` WBS 進度表 + 待解問題

## Phase P5.7 — 夜間排程（未啟動）

- **產出物**：Windows 工作排程器腳本，nightly run 自動觸發
- **預估工時**：3h
- **前置**：P4.5 全部跑完（含 2-2-5-A/B、2-3-13）；warm-login 流程穩定
- **狀態**：⏳ 等 P4.5 全綠

## Phase P6 — 前端 meta 同步（未啟動）

P6 高度依賴前端工程師加 `data-testid`，目前無時程承諾。

## Phase P7 — 工程化沉澱（部分完成 2026-05-08）

- ✅ **prompts/ 完整化**：00 專案發起 / 10 PDF 轉規格 / **20 生成測試案例**（新）/ **30 審查與修訂**（新）/ **40 執行測試與排錯**（新）/ 99 重點經驗
- ✅ **docs/技術架構.md**：含目錄樹、模組分層 mermaid、週循環資料流 mermaid、跨專案重用 checklist
- ✅ **notes/ 第一份素材**：`20260508-poc-2-2-2-收斂.md`，可餵 `make-pptx` skill 產簡報
- ⏳ **push 到 NoahGitHubAccount**：待初版穩定後執行（人類動作）

---

## 範圍排除（已決議）

- **2-2-2-A 等純權限工項排除**：Why — 採單一 admin 帳號、最大權限、不驗證權限邊界（見 memory `poc_autotest_decisions.md`）
- **後端可能擋的 CAPTCHA**：預設不繞過；config 預留 `captcha.mode: bypass` 開關，後端配合時一行切換

---

## 已決議事項（曾為未決問題；2026-05-07 收斂）

> 進行中 / 阻塞中的問題請見 `STATUS.md` 第 3 段「待解問題 / Blockers」。
> 本段保留「P5 啟動前的三個結構性決定」做歷史索引；revisit 觸發條件達成時可重新討論。

| 編號 | 問題 | 決議 | 理由 | Revisit 觸發 |
|---|---|---|---|---|
| Q1 | STATUS.md 是否進 git？ | ❌ 不進，已 `.gitignore` | 個人狀態錨點；團隊共享走 `WBS.md` + `reports/` | 第二位協作者加入 / PR review 帶進度 |
| Q2 | 後端 CAPTCHA bypass 是否支援？ | ✅ 走 warm-login，bypass 不在 POC 範圍 | dev-maas 後端由其他團隊管，本團隊無協調權；warm-login 已驗證 | 後端團隊主動配合改動（config 已留 `captcha.mode` 開關） |
| Q3 | 是否需要 CI 整合？ | ❌ POC 階段不上 CI | 範圍小、單一 admin、單機 Windows；ROI 不正 | POC 通過推廣到 ≥ 2 站 / 出現第二位執行者 |

## 變更紀錄

- 2026-05-05 初版建立（追溯既有 P0–P7 框架，補入決議與 blocker）
- 2026-05-07 「未決問題」收斂為「已決議事項」表（Q1/Q2/Q3 皆已落地）；補 P4.5 日期格式相容（2-2-2-B AC8、2-3-13-G1 AC4）
