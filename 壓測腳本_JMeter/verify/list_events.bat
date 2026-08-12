@echo off
cd /d %~dp0
rem 載入共用設定（受測站 host / 資料 ID）
call "%~dp0..\shared\settings.bat"
if not exist "%~dp0..\shared\token.txt" (
  echo [X] token.txt not found in ..\shared.
  pause
  exit /b 1
)
python list_events.py
echo.
echo Done. events.txt written in this folder.
pause
