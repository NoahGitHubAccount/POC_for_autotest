# JMeter 壓測腳本（已通過端到端自測）

> 2026-07-13 21:31 AI 已無頭實測：**6 支 API 全部 200、0 錯誤**，且資料庫確認新增報名記錄（id `34186560800512000`），非假成功。

## 目錄結構（英文資料夾名，避免 bat 中文亂碼）
| 資料夾 | 中文對照 | 內容 |
|---|---|---|
| `shared\` | 共用參照 | `loadtest_150.jmx`（唯一計畫）、`sessions.csv`（場次）、`token.txt`（你貼 token 這裡）、`tokens.csv`（自動產生） |
| `prod_150users\` | 150人正式（業主模型） | `run_150users.bat` |
| `prod_300users\` | 300人壓力（2x模型，找天花板） | `run_300users.bat`（300人/10分鐘，ramp 4分） |
| `trial_10users\` | 10人試跑（1→150 之間的放大驗證） | `trial_10users.bat`（10人/2分鐘） |
| `rehearsal_1user\` | 1人演練 | `rehearsal_1user.bat` |
| `verify\` | 測試驗證/報名查詢 | `check_registrations.bat`、`.py`、`registrations.txt`（**報名紀錄保留這**） |
| `reports\` | 匯出報告 | 每次執行一個時間戳資料夾（`rehearsal_<時間>\`、`run150_<時間>\`），內含 `report\index.html` |

> ⚠️ 首次整理：先雙擊根目錄的 `_reorganize_once.bat` 把散檔搬進上述資料夾（跑一次即可，之後可刪掉它）。
> token.txt 只需放在 `shared\`，1人演練與150人正式共用同一份。

## 大港閱兵壓測模型對照（150用戶計畫的設計依據）
| 業主模型 | 計畫實作 |
|---|---|
| 1500人/4hr → 簡化 150 併發、測 10 分鐘 | Thread=150、Duration=600s（可用 `-JTHREADS`/`-JDURATION` 覆蓋） |
| 流量平緩、無瞬時尖峰 | Ramp-up 120 秒逐步進場 |
| 每人操作約 5 分鐘 | 兩段思考時間：瀏覽內容 30~90 秒、填表 60~180 秒（`-JTHINK_*` 可調） |
| 4.1 取活動內容含圖片 | 交易 T1：活動資訊＋媒體清單＋兩張封面圖 |
| 4.2 取動態表單 | 交易 T2：EVFormField |
| 4.3 送出資料 | 交易 T3：EVRegistration POST（場次由 sessions.csv 輪替） |

## ✅ 重複報名限制已解除（2026-07-13，單一 token 可無限循環）

後台原始碼查證＋實測結果：

- **每人總場次上限**是活動規則欄位 `perPersonTotalLimit`（原值 1），**已用 API PATCH 成 0＝停用**（規則 id `34185325524500480`）。原始碼 `EVRegistrationLogic.cs` 的檢核寫法是 `if(limit > 0)`，0 就跳過。
- 「同個場次不可重複報名」雖寫死在程式裡，但它只計算 `Confirmed` 狀態的報名——本活動新報名非該狀態，**實測同場次連續報名皆 200**。
- 20 秒結構驗證（規則解除後）：**103 樣本 100% 成功，T3 送出全部 200（88~230ms）**。
- 結論：**單一 token 即可跑完整 150 併發壓測，不需要準備 150 組帳號**。tokens.csv 放一組即可（多帳號仍是更貼近真實的選項，留待正式壓測環境決定）。
- 還原方式（壓測結束後如需恢復）：對 `/reventmodule/Entity/EVEventRule` PATCH `{"id":"34185325524500480","perPersonTotalLimit":1}`。

⚠️ **150 併發前必要準備**：
1. `token.txt`/`tokens.csv` 放入當下有效的 token（效期短，跑前才取）
2. 業主說要先升級伺服器資源——執行前跟環境負責人約定時間
3. 報告看 `report_html\index.html`：Transactions 頁籤可分別看 T1（含圖片）/T2/T3 三段的回應時間分布
4. 每次成功報名都會在 DB 新增一筆記錄（150VU×10min 約產生數百筆），QA 測試資料依慣例不需清理

## 快速開始
1. 瀏覽器登入 QA 前台 → DevTools Console 執行：
   `JSON.parse(sessionStorage.getItem('logintoken')).access_token`
2. 把輸出貼進 `shared\token.txt`（覆蓋整行，不含引號）
3. 演練：雙擊 `rehearsal_1user\rehearsal_1user.bat`（1人90秒）
   正式：雙擊 `prod_150users\run_150users.bat`（150人10分鐘，需輸入 y）
4. 看黑視窗 `Err: 0 (0.00%)` 即成功；HTML 報告會自動開啟
5. 查報名有沒有進 DB：雙擊 `verify\check_registrations.bat` → 看 `verify\registrations.txt`

## 輸出檔案（每次執行獨立、不覆蓋）
每次執行都在 `reports\` 下建一個帶執行時間的資料夾：
- 演練：`reports\rehearsal_<時間>\`
- 正式：`reports\run150_<時間>\`
每個資料夾內含 `result.jtl`（原始數據）、`jmeter.log`、`report\index.html`（圖表報告）。

## 場次名額（2026-07-14 10:52 實查，重要）
`sessions.csv` **只保留 3 個 1500 名額的場次**輪替，總容量 4500，足夠 150VU×10min（約 300 筆）多次重跑：

| 場次 | 名額 | 是否在 sessions.csv |
|---|---|---|
| 雞蛋糕 `34185325525745666` | 1500 | ✅ |
| 布蕾 `34185325525745667` | 1500 | ✅ |
| 小時候乳酪冰 `34185325525811201` | 1500 | ✅ |
| 乳酪包 `34185325525745664` | **1** | ❌ 已移除（名額只有 1，會擋報名） |
| 禮盒組 `34185325525745665` | **1** | ❌ 已移除（名額只有 1） |
| 活動節目表 `34185325525680128` / 無糖 Smoothie `34185325525811200` | — | ❌ 未列入 |

> 若要用滿 5 個場次，需先把乳酪包/禮盒組的 maxAttendees 調高（後台或 API PATCH EVEventNode），但 3 場已足夠，不必動。

## 其他已知限制
- **每人總報名上限已解除**（規則 id `34185325524500480` 的 `perPersonTotalLimit` 已設 0），單一 token 可重複報名 → 150 併發只需一組 token。
- token 效期有限，跑之前才取。
- 圖片下載需帶 `ocp-apim-subscription-key`/`x-api-version`（已內建在計畫的 T1 圖片 sampler）。

## 6 支 API 一覽
| Task | 方法 | 端點 | 實測 |
|---|---|---|---|
| Task1 活動內容 | GET | qa-khcg-ai…/Entity/EVEvent?ids=34185325523320832 | 200 |
| Task2 媒體清單 | GET | qa-khcg-ai…/Basic/EVEventMedia?eVEventIds=34123425668794368 | 200 |
| Task2b 封面圖PC(213KB) | GET | qa-citygpt…/FileResource/34184848690100224 | 200 |
| Task2c 封面圖行動(82KB) | GET | qa-citygpt…/FileResource/34184848895096832 | 200 |
| Task3 報名表單欄位 | GET | qa-khcg-ai…/Basic/EVFormField?eVEventIds=34185325523320832 | 200 |
| Task4 確認報名 | POST | qa-khcg-ai…/Entity/EVRegistration | 200＋DB實證 |
