@echo off
set LOG=%~dp0delete_run.log
echo ==== bat started %DATE% %TIME% ==== > "%LOG%"
echo bat dir = %~dp0 >> "%LOG%"
cd /d %~dp0..
echo cwd after cd = %CD% >> "%LOG%"
echo ============================================================
echo  DELETE bucket A (automation test activities)
echo  Log: %LOG%
echo ============================================================
set /p GO=Confirm delete now? (y/N):
echo user typed = %GO% >> "%LOG%"
if /i not "%GO%"=="y" (
  echo aborted by user >> "%LOG%"
  echo Aborted.
  pause
  exit /b
)
if not exist ".venv\Scripts\python.exe" (
  echo [X] .venv python NOT found at %CD%\.venv\Scripts\python.exe >> "%LOG%"
  echo [X] .venv python not found. See %LOG%
  pause
  exit /b 1
)
echo python found, running script... >> "%LOG%"
.venv\Scripts\python.exe tools\delete_bucketA.py >> "%LOG%" 2>&1
echo ==== python exit code = %ERRORLEVEL% ==== >> "%LOG%"
echo.
echo === log content ===
type "%LOG%"
echo.
echo Done. Full log: %LOG%
pause
