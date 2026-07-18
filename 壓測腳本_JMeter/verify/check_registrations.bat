@echo off
cd /d %~dp0
if not exist "%~dp0..\shared\token.txt" (
  echo [X] token.txt not found in ..\shared. Paste your access_token there first.
  pause
  exit /b 1
)
python check_registrations.py
echo.
echo Done. registrations.txt written in this folder.
pause
