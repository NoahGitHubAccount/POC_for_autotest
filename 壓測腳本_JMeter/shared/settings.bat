@echo off
rem ============================================================
rem  壓測共用設定（唯一需要填的檔案）
rem
rem  本檔集中所有「跟受測站有關」的值，讓 .jmx / .py / 各 run bat
rem  都不必寫死 host 與資料 ID，也不會把真實值帶進版控。
rem  使用方式：把下列 REPLACE_ME 換成受測環境的實際值。
rem
rem  ⚠ 本檔以「全部 REPLACE_ME」的範本狀態入版控（同 config/config.example.yaml 的角色）。
rem    填入真實 host 與 ID 後請勿 commit——需要長期保存實際值時，
rem    請改用環境變數或另存一份不入版控的副本。
rem ============================================================

rem --- 受測站 ---------------------------------------------------
rem HOST       ：API 主機（不含 https://）
rem MEDIA_HOST ：圖片／檔案資源主機（若同一台，填與 HOST 相同）
set HOST=REPLACE_ME
set MEDIA_HOST=REPLACE_ME

rem --- 壓測目標資料 ---------------------------------------------
rem EVENT_ID       ：壓測目標活動 pkid
rem MEDIA_EVENT_ID ：媒體清單查詢用的活動 pkid（通常同 EVENT_ID）
rem BANNER_PC_ID   ：桌機版封面圖 FileResource pkid
rem BANNER_MOBILE_ID：行動版封面圖 FileResource pkid
rem FORM_FIELD_ID  ：報名表單必填欄位 pkid（送出報名時帶值）
set EVENT_ID=REPLACE_ME
set MEDIA_EVENT_ID=REPLACE_ME
set BANNER_PC_ID=REPLACE_ME
set BANNER_MOBILE_ID=REPLACE_ME
set FORM_FIELD_ID=REPLACE_ME

rem --- API Gateway 訂閱金鑰（若受測站不需要，留 REPLACE_ME 即可）---
set APIM_KEY=REPLACE_ME

rem --- JMeter 安裝位置 -------------------------------------------
set JMETER_BIN=C:\Tools\apache-jmeter-5.6.3\bin\jmeter.bat

rem ============================================================
rem  以下由腳本自動組裝，不需修改
rem ============================================================

rem 傳給 JMeter 的 -J 屬性（.jmx 內以 ${__P(名稱,REPLACE_ME)} 取用）
set JPROPS=-JHOST=%HOST% -JMEDIA_HOST=%MEDIA_HOST% -JEVENT_ID=%EVENT_ID% -JMEDIA_EVENT_ID=%MEDIA_EVENT_ID% -JBANNER_PC_ID=%BANNER_PC_ID% -JBANNER_MOBILE_ID=%BANNER_MOBILE_ID% -JFORM_FIELD_ID=%FORM_FIELD_ID% -JAPIM_KEY=%APIM_KEY%

rem 傳給 verify/*.py 與 shared/ensure_limit.py 的環境變數
set LOADTEST_BASE_URL=https://%HOST%
set LOADTEST_EVENT_PKID=%EVENT_ID%
set LOADTEST_FORM_FIELD_PKID=%FORM_FIELD_ID%

rem 場次 pkid：僅 fix_limit_and_test.py 試報一筆時用；預設取 sessions.csv 第 2 行
for /f "usebackq skip=1 delims=" %%s in ("%~dp0sessions.csv") do (
  if not defined LOADTEST_SESSION_PKID set LOADTEST_SESSION_PKID=%%s
)

rem 不可誤刪的活動 pkid（逗號分隔，供 verify/list_events.py 標記「留存」）
set LOADTEST_KEEP_PKIDS=%EVENT_ID%
