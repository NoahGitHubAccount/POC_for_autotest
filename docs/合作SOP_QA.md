# 合作 SOP — Q&A

> 對象：Golden ↔ Claude（POC_for_autotest 專案）
> 用途：每週測試任務的**人機互動 SOP**；新 session 也能依此接手。
> 與 `prompts/README.md` 分工：本檔是「人怎麼跟 AI 講話」；`prompts/README.md` 是「AI 動工時用哪些提示詞檔案」。
> 最後更新：2026-05-06

---

## Q1：每週你（Golden）要給我（Claude）什麼？

**A**：3–5 個 WBS ID + 各工項的「實作狀態」。

範例貼法：

```
本週工項：
- 2-2-4-A 活動編號：已實作（前後端都好，可測）
- 2-2-4-B 活動名稱：已實作
- 2-2-4-G 最近更新時間排序：已實作
- 2-2-3 活動列表預設排序：已實作
備註：2-2-4-H 還沒，下週再驗
```

最少資訊量：**WBS ID + 「可測 / 未實作 / 部分（誰擋住）」**。
有額外提示（特殊 fixture、測試帳號、邊界值等）也一併寫，沒有就不寫。

---

## Q2：我（Claude）每週給你什麼？

**A**：對每個工項依序產出 4 樣交付物：

1. **spec md**（若還沒展開）：`specs/<工項id>/<工項id> 標題.md`
2. **test 檔**：`tests/<父工項> <名>/test_<id>_*.py`
3. **pytest 結果**：你跑、你貼 short summary 給我
4. **docx 交付件**：`reports/<rid>_run/docx/<rid>_run_測試報告.docx`

---

## Q3：單一工項從 0 到交付的 motion path？

**A**：固定 5 步。

1. **spec 沒展開** → 我跑 `prompts/10_PDF轉規格_提示詞.md` 對該工項，產 spec md。**你 review**，把調整寫進 `<!-- USER-EDIT START -->` 區塊。
2. **寫 test** → 我參考 spec + `lib/selectors.py`，產 `test_<id>_*.py`。標清 xfail / skip 的理由（spec/impl 衝突？元件未解碼？外部依賴？）。
3. **跑 pytest** → 你執行：
   ```powershell
   pytest "tests/<父工項> <名>/" -v
   ```
   把 short summary 貼回給我。
4. **紅了 → 4 步流程修 selector**（CLAUDE.md 第 1 條）：
   - ①解碼 src（讀對應 view + entity model + STFilter）
   - ②修 `lib/selectors.py`
   - ③再跑 pytest
   - ④還紅 → 你 dump 一頁 HTML（`/entry/<path>` 載入後）給我，我對著真實 DOM 改。**最多 3 輪**。
5. **全綠 → 交付**：
   ```powershell
   pytest "tests/<父工項> <名>/" -v --shot=always
   python tools/md_to_docx.py
   ```
   docx 在 `reports/<rid>_run/docx/`。

---

## Q4：截圖模式怎麼選？

**A**：兩種模式：

| 階段 | 命令 | 行為 |
|---|---|---|
| **收斂中** | `pytest ...`（不加 flag） | `--shot=failed_only`（預設）：只失敗時拍，省檔案量 |
| **最終交付** | `pytest ... --shot=always` | 每個 test 都拍，docx 內每個 case 都有畫面 |

完全不需要時：`--shot=off`。

---

## Q5：我（Claude）跨 session 怎麼接得回上次進度？

**A**：每次 session 開場我先讀 `STATUS.md`。session 結束若有實作或決議異動就寫回去。

`STATUS.md` 三段最重要：
- **WBS 進度表**：誰在跑 / 誰阻塞
- **最近決議**：最新在上、保留 ~10 條
- **下一步**：你看這段就知道我打算做什麼

純 read-only Q&A 我**不**動 STATUS.md。

---

## Q6：你（Golden）想直接看現在做到哪？

**A**：開 `STATUS.md` 看「目前焦點」+「下一步」兩段。其餘段落是支撐資訊。

---

## Q7：spec 與實作衝突時怎麼處理？

**A**：

- **小衝突（按鈕文字、欄位順序、提示語等）**：以 DOM 為準（CLAUDE.md 第 3 條），測試對齊實作；spec md 加註記「實作為 X，規格為 Y，已採 X」。
- **大衝突（spec 要求的行為實作直接擋掉，例：D-AC2 disabled gate）**：標 xfail + reason 引到「待業務方確認」；同時記到 STATUS.md「待解問題」。**不擅自改 spec**，不擅自把測試搞綠。

---

## Q8：可以一次給我多週的工項嗎？

**A**：可以，但建議一週批一次跑。理由：
- 開發狀態變化快，跨週的工項實作狀態可能變
- 你的 review 容量有限，一次太多會卡在 (1)spec review
- pytest 紅了要回頭 dump HTML，連續工項並行只會拉長 cycle time

**例外**：同一父工項下的子工項（如 2-2-4-A~G）屬於同一輪，可一次給。

---

## Q9：我跑 pytest 紅了 + 你說要 dump HTML，怎麼 dump？

**A**：兩個工具，看狀況挑。

**輕量探查（先試這個）**：
```powershell
python tools/explore_page.py /entry/<path>
```
列出該頁所有 button 文字、placeholder、heading、data-testid。**90% 的 selector 失敗用這個就能解**（如「按鈕到底叫什麼名字」）。

**完整 HTML dump（探查不夠時用）**：
```powershell
python tools/dump_runtime_storage.py   # 或類似 dump 工具，必要時我會臨時生
```

把輸出貼回，或檔案路徑告訴我。

---

## Q10：我可以用什麼一句話啟動本週的工作？

**A**：貼 Q1 範例那種格式，後面加一句「**動工**」。例：

```
本週工項：
- 2-2-4-A 活動編號：已實作
- 2-2-4-B 活動名稱：已實作
- ...
動工
```

我會：
1. 先跑 spec 展開（prompts/10_）→ 產 spec md
2. spec 給你 review
3. review 後寫 tests
4. 你跑 pytest，貼 summary
5. 全綠 → docx 交付
