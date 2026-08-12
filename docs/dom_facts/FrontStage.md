# DOM 事實:前台(公民端活動報名)

> 2026-07-11 spike 確立。**一般瀏覽器可瀏覽**,訪客(guestToken)不登入即可看;行動版型(建議 viewport 480×900)。
> SPA 對不存在路由渲染空白頁殼(勿誤判成「WebView 專用」——曾因 `gome` 誤植路由誤判,已翻案)。

## 路由

| 頁 | 路徑 | 未登入可視 | 驗證日期 |
|---|---|---|---|
| 首頁 | `/entry/Home` | ✅(熱門活動卡片、立即探索) | 2026-07-11 |
| 所有活動 | `/entry/allActivities` | ✅(話題最熱+活動卡片列表) | 2026-07-11 |
| 活動資訊頁 | `/entry/ActivityInfo?evEventId=<pkid>` | ✅(日期/地點/簡介/報名方式/活動須知 tabs) | 2026-07-11 |
| 活動票夾 | `/entry/tickerBoard` | ✅(未登入:已報名(0)/歷史/取消+「登入」鈕) | 2026-07-11 |
| 報名填寫頁 | `/entry/ActivityReservationForm?evEventId=<pkid>&sessionId=<場次id>` | 需登入(從資訊頁「立即報名」進入;多場次每場一顆按鈕) | 2026-07-11 |
| 報名成功頁 | `/entry/activityregistrationsuccess?evEventId=<pkid>` | 確認報名後落點(「報名成功!」+參與人數+報到時間) | 2026-07-11 |
| 報名資料/憑證頁 | `/entry/ActivityReservationView?evEventId=<pkid>&sessionId=<場次id>` | 已報名後資訊頁按鈕「查看報名資料」進入 | 2026-07-11 |
| 關於我們 | `/entry/aboutUs` | — | 2026-07-11 |

## 行為事實

- 訪客首開頁面 sessionStorage 自動寫入 `guestToken`;登入態 token key 待實登後回填。
- **卡片結構（2026-07-11 IT-09 實測更正）**：`a[href*='evEventId=']` **只是卡上「報名及查詢」按鈕、不是整卡**；pre_open 卡片**無 `<a>` 按鈕**、按鈕區顯示「<民國時間> 開放報名」純文字。整卡容器＝以活動名稱 `get_by_text(exact)` 動態爬層（第一個文字量 <250 的祖先；再上一層是整個卡片格線）。點卡片標題可導航到資訊頁。
- 未登入+開放報名 → 按鈕「報名及查詢」；點選（資訊頁上）轉跳公民端登入頁。
- **「報名及查詢」DOM 因頁而異（2026-07-18 no208a 實測）**：列表頁卡片＝`a[href*='evEventId=']`；**資訊頁場次卡＝`<button>`（無 href，`get_by_role("button", name="報名及查詢")`）**；資訊頁預設只露前 3 張場次卡（「查看全部 X 場」展開為 modal，會攔截後續點擊）。
- **實作差異**：docx「報名按鈕 disable」→ 實作為**按鈕不渲染**（卡片與資訊頁皆然），以顯示開放時間替代；語意達成，斷言用「開放報名字樣存在＋報名按鈕不存在」。
- 後台造的測試活動(已啟用+曝光中)**會上前台列表**(IT08_ 複製品已出現在所有活動頁)——測試資料會污染前台,跑批後必清。
- 前台顯示條件=已啟用+曝光時間內(`make_stage_event` 預設曝光窗涵蓋 now,故各 stage 複製品可直開 `ActivityInfo?evEventId=<pkid>` 驗證)。
- **滿意度回饋 modal(2026-07-12 IT-12 實測)**:公民帳號**首次成功報名**後於報名成功頁跳出 `.modal-overlay`(header「滿意度回饋」,含 1-5 分 emoji、tag 標籤、textarea「歡迎提供更多建議 : )」),**後續報名不再出現**;會攔截後續點擊(「查看報名資料」)。關閉鈕:行動版型可見=`button.mobile-cancel-btn`(取消),桌面版=`button.close-btn`(×,行動版 `hidden`)。測試助手須先關 modal 再點下一步(見 `test_it12_前台憑證頁.py::_dismiss_feedback_modal`)。

## 入場憑證頁(ActivityReservationView)顯示欄位(2026-07-12 IT-12 實測)

- 標題「入場憑證」→ 場次名稱 → 報名序號(格式化如 `00001`) → 憑證備註文字(credentialNote 系統預設「請於報到時出示此憑證,以便工作人員核對。憑證僅限本人使用…」) → 活動名稱 → 報名梯次(時間) → 報到地點(開啟地圖) → 報名人資訊(參與人數) → 須知與注意事項 → 按鈕「查看報名紀錄/取消報名/查看活動簡介」。
- 核銷 QR/條碼=`img[src^="data:image/png;base64,"]`(頁面有 2 張大 PNG;無 canvas)。
- entity API(`/reventmodule/Entity/EVEvent/{id}`)**未直接暴露** credentialNote/checkinNotice(藏 ticket 設定,key-value 參照);場次名可取 `evEventNodes[0].name`。憑證備註採 dom_facts 記錄之系統預設文案比對。

## 手動登入(公民帳號)——2026-07-11 成功流程

- **定案流程＝信號檔版** scratchpad `citizen_manual_login_v3.py`:開有頭視窗→使用者登入(第三方身分驗證,鏈路會跳出受測站網域)→使用者口頭告知→AI 建 `citizen_login_done.flag`→腳本存 `.auth/citizen(.session).json`。**勿用 DOM 偵測**(guestToken 誤觸發、第三方網域誤觸發、evaluate 卡死三種翻車都發生過)。
- **登入態 sessionStorage keys**:`logintoken`(會員 token)＋`guestToken`/`permissions`/`permissionsLoaded` 等;localStorage `UserProfilePreferenceStore`。
- 重放已驗:storage_state+session init script 開票夾=「<使用者暱稱>的活動票夾」+「登出帳戶」。token 效期未知,失效徵兆=頁面出現「登入查看專屬活動票夾」→ 需使用者重登(手機認證,無法自動化)。
