@echo off
cd /d %~dp0
set SHARE=%~dp0..\shared
set REPORTS=%~dp0..\reports
rem 載入共用設定
call "%SHARE%\settings.bat"
echo ============================================================
echo  STRESS TEST: 300 users / 10 min (ramp-up 4 min)
echo  NOTE: 300 = 2x the business model (150). Ceiling-finding run.
echo  This generates 10 minutes of heavy traffic on QA.
echo ============================================================
if not exist "%SHARE%\token.txt" (
  echo [X] token.txt not found in ..\shared. Paste your access_token there first.
  pause
  exit /b 1
)
echo TOKEN> "%SHARE%\tokens.csv"
for /f "usebackq delims=" %%a in ("%SHARE%\token.txt") do echo %%a>> "%SHARE%\tokens.csv"
set /p GO=Start now? (y/N):
if /i not "%GO%"=="y" exit /b
echo Ensuring registration limit disabled...
python "%SHARE%\ensure_limit.py"
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TS=%%i
set OUTDIR=%REPORTS%\run300_%TS%
mkdir "%OUTDIR%" 2>nul
call "%JMETER_BIN%" -n -t "%SHARE%\loadtest_150.jmx" %JPROPS% -JTHREADS=300 -JRAMP=240 -JDURATION=600 -l "%OUTDIR%\result.jtl" -j "%OUTDIR%\jmeter.log" -e -o "%OUTDIR%\report"
echo.
echo ============================================================
echo  DONE. Output: %OUTDIR%
echo ============================================================
start "" "%OUTDIR%\report\index.html"
pause
