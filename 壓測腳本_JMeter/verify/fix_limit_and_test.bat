@echo off
cd /d %~dp0
if not exist "%~dp0..\shared\token.txt" (
  echo [X] token.txt not found in ..\shared.
  pause
  exit /b 1
)
python fix_limit_and_test.py
echo.
echo Done. diag.txt written in this folder.
pause
