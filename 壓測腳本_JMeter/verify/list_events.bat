@echo off
cd /d %~dp0
if not exist "%~dp0..\shared\token.txt" (
  echo [X] token.txt not found in ..\shared.
  pause
  exit /b 1
)
python list_events.py
echo.
echo Done. events.txt written in this folder.
pause
