# JMeter 壓測腳本（活動報名情境）

> 一套可跨專案重用的 JMeter 壓測骨架：模擬「民眾瀏覽活動 → 取報名表單 → 送出報名」三段交易，
> 並附驗證腳本確認報名真的寫進資料庫（避免「全 200 但沒進 DB」的假成功）。
> **所有跟受測站有關的值都集中在 `shared\settings.bat`**，本目錄不含任何真實 host、活動 ID 或金鑰。

## 目錄結構（英文資料夾名，避免 bat 中文亂碼）

| 資料夾 | 中文對照 | 內容 |
|---|---|---|
| `shared\` | 共用參照 | `settings.bat`（**唯一要填的設定檔**）、`loadtest_150.jmx`（唯一測試計畫）、`sessions.csv`（場次 pkid 輪替清單）、`token.txt`（你貼 token 這裡，gitignored）、`tokens.csv`（run bat 自動產生，gitignored）、`ensure_limit.py` |
| `prod_150users\` | 150 人正式（客戶模型） | `run_150users.bat` |
| `prod_300users\` | 300 人壓力（2 倍模型，找天花板） | `run_300users.bat`（300 VU／10 分鐘，ramp 4 分鐘） |
| `trial_10users\` | 10 人試跑（1 VU → 150 VU 之間的放大驗證） | `trial_10users.bat`（10 VU／2 分鐘） |
| `rehearsal_1user\` | 1 人演練 | `rehearsal_1user.bat`（1 VU／90 秒） |
| `verify\` | 測試驗證／報名查詢 | `check_registrations.bat`、`list_events.bat`、`fix_limit_and_test.bat` 及對應 `.py`；輸出的 `*.txt` 為執行產物，不入版控 |
| `reports\` | 匯出報告 | 每次執行一個時間戳資料夾（`rehearsal_<時間>\`、`run150_<時間>\`），內含 `report\index.html` |

> ⚠️ 首次整理：若檔案還散在根目錄，先雙擊 `_reorganize_once.bat` 把散檔搬進上述資料夾（跑一次即可，之後可刪）。
> `token.txt` 只需放在 `shared\`，各種規模的執行共用同一份。

---

## 一、首次使用：填 `shared\settings.bat`

這是**唯一需要填的檔案**，把裡面的 `REPLACE_ME` 換成受測環境的實際值：

| 變數 | 意義 | 怎麼取得 |
|---|---|---|
| `HOST` | API 主機（不含 `https://`） | 與 `config/config.<env>.yaml` 的 `base_url` 同一台 |
| `MEDIA_HOST` | 圖片／檔案資源主機 | 若同一台就填與 `HOST` 相同 |
| `EVENT_ID` | 壓測目標活動 pkid | 後台開活動編輯頁看網址，或跑 `verify\list_events.bat` |
| `MEDIA_EVENT_ID` | 媒體清單查詢用的活動 pkid | 通常同 `EVENT_ID` |
| `BANNER_PC_ID` / `BANNER_MOBILE_ID` | 封面圖 FileResource pkid | DevTools Network 看活動頁載入的圖片網址尾碼 |
| `FORM_FIELD_ID` | 報名表單必填欄位 pkid | `GET /reventmodule/Basic/EVFormField?eVEventIds=<EVENT_ID>` |
| `APIM_KEY` | API Gateway 訂閱金鑰 | 受測站若不需要就留 `REPLACE_ME` |
| `JMETER_BIN` | JMeter 執行檔路徑 | 你本機的 `apache-jmeter-x.y.z\bin\jmeter.bat` |

另外把 `shared\sessions.csv` 的 `REPLACE_ME` 換成**實際場次 pkid**（一行一個）。
選場次的原則：**只挑名額足夠大的場次**——名額只有個位數的場次會在壓測中途擋掉報名，
造成大量 400，看起來像系統故障其實是測試資料設定問題。

> `settings.bat` 會把值同時轉成 JMeter 的 `-J` 屬性（給 `.jmx`）與環境變數（給 `verify\*.py`），
> 所以填一處、兩邊都生效；`.jmx` 內部一律寫 `${__P(名稱,REPLACE_ME)}`，不寫死任何值。

---

## 二、執行前準備：取 token

1. 瀏覽器登入受測站前台 → DevTools Console 執行：
   `JSON.parse(sessionStorage.getItem('logintoken')).access_token`
2. 把輸出貼進 `shared\token.txt`（覆蓋整行，不含引號）
3. **token 效期短，正式跑之前才取**——這步不能省

---

## 三、執行

| 情境 | 動作 |
|---|---|
| 演練 | 雙擊 `rehearsal_1user\rehearsal_1user.bat`（1 VU／90 秒） |
| 放大驗證 | 雙擊 `trial_10users\trial_10users.bat`（10 VU／2 分鐘） |
| 正式 | 雙擊 `prod_150users\run_150users.bat`（150 VU／10 分鐘，需輸入 `y`） |
| 找天花板 | 雙擊 `prod_300users\run_300users.bat`（300 VU／10 分鐘，需輸入 `y`） |

判讀：黑視窗出現 `Err: 0 (0.00%)` 即全部成功；HTML 報告會自動開啟。
查報名有沒有真的進資料庫：雙擊 `verify\check_registrations.bat` → 看同目錄產出的 `registrations.txt`。

執行中黑視窗每 30 秒印一行 `summary +`，盯兩個數字：

- `Err: N`——一直是 0 就是順的；若大量 401 代表 token 過期（中斷、換 token 重跑）
- `Avg:`——平均回應時間，越跑越大代表伺服器開始吃力（這是正常的觀測目標，不用中斷）

### 輸出檔案（每次執行獨立、不覆蓋）

每次執行都在 `reports\` 下建一個帶執行時間的資料夾（`rehearsal_<時間>\`、`run150_<時間>\`…），
內含 `result.jtl`（原始數據）、`jmeter.log`、`report\index.html`（圖表報告）。
報告的 **Transactions／Statistics** 頁籤可分別看 T1（含圖片）／T2／T3 三段的回應時間分布；
**Charts → Response Times Over Time** 用來看「圖片會不會越跑越慢」。

---

## 四、壓測模型對照（150 VU 計畫的設計依據）

計畫參數皆可用 `-J` 覆蓋，下表是預設值的由來：

| 客戶模型 | 計畫實作 |
|---|---|
| 1,500 人／4 小時 → 簡化成 150 併發、測 10 分鐘 | `THREADS=150`、`DURATION=600 秒`（可用 `-JTHREADS` / `-JDURATION` 覆蓋） |
| 流量平緩、無瞬時尖峰 | Ramp-up 120 秒逐步進場 |
| 每人操作約 5 分鐘 | 兩段思考時間：瀏覽內容 30～90 秒、填表 60～180 秒（`-JTHINK_*` 可調） |
| 取活動內容含圖片 | 交易 T1：活動資訊＋媒體清單＋兩張封面圖 |
| 取動態報名表單 | 交易 T2：`EVFormField` |
| 送出報名資料 | 交易 T3：`EVRegistration` POST（場次由 `sessions.csv` 輪替） |

---

## 五、已知限制與踩坑

- **「每人總報名上限」會擋住重複報名**：活動規則欄位 `perPersonTotalLimit`（每人可報名的總場次上限）
  若大於 0，同一個 token 報第二筆就會 400。各 run bat 開跑前會自動呼叫 `shared\ensure_limit.py`
  把它設為 0（＝停用），單一 token 即可跑完整併發壓測，**不需要準備 150 組帳號**。
  壓測結束後若要恢復，對 `/reventmodule/Entity/EVEventRule` PATCH 回原值即可。
- **場次名額不足會造成假故障**：見上文 `sessions.csv` 的選場原則。
- **token 效期有限**，跑之前才取；大量 401 就是它過期了。
- **圖片下載需帶 `ocp-apim-subscription-key` / `x-api-version` 標頭**（已內建在計畫的 T1 圖片 sampler，
  金鑰由 `APIM_KEY` 帶入）。
- **壓測會在資料庫留下大量報名記錄**（150 VU × 10 分鐘約數百筆），跑完依專案慣例決定是否清理；
  `verify\list_events.bat` 可列出活動並標記疑似自動化測試產物供人工審查。

---

## 六、異常對照表

| 症狀 | 原因 | 處置 |
|---|---|---|
| 全部 401 | token 過期／貼錯 | 重取 token → 重跑 |
| 全部 404 或連不上 | `settings.bat` 的 `HOST` 還是 `REPLACE_ME` | 先填 `shared\settings.bat` |
| T3 出現 400 | 報名規則「每人總上限」被改回大於 0 | run bat 開跑前已自動重設為 0（呼叫 `shared\ensure_limit.py`）；若仍 400，手動雙擊 `verify\fix_limit_and_test.bat` 診斷修復後重跑 |
| Connection refused／timeout 大量 | 伺服器扛不住或網路問題 | 這本身就是壓測發現，記下發生時間點，報告會呈現 |
| 黑視窗閃退 | `shared\token.txt` 不存在 | 先做 token 步驟 |
| 找不到檔案／路徑 | 還沒跑 `_reorganize_once.bat` 整理目錄 | 先雙擊根目錄 `_reorganize_once.bat` 一次 |

---

## 六支 API 一覽

| Task | 方法 | 端點（host 由 `HOST` / `MEDIA_HOST` 帶入） |
|---|---|---|
| T1-1 活動內容 | GET | `/reventmodule/Entity/EVEvent?ids=<EVENT_ID>&bindUserData=true` |
| T1-2 媒體清單 | GET | `/reventmodule/Basic/EVEventMedia?eVEventIds=<MEDIA_EVENT_ID>` |
| T1-3 封面圖（桌機版） | GET | `/rstorage/Extended/FileResource/<BANNER_PC_ID>` |
| T1-4 封面圖（行動版） | GET | `/rstorage/Extended/FileResource/<BANNER_MOBILE_ID>` |
| T2 報名表單欄位 | GET | `/reventmodule/Basic/EVFormField?eVEventIds=<EVENT_ID>&category=Registration` |
| T3 確認報名 | POST | `/reventmodule/Entity/EVRegistration` |
