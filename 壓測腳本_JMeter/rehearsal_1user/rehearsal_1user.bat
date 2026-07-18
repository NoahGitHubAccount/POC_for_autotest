@echo off
cd /d %~dp0
set SHARE=%~dp0..\shared
set REPORTS=%~dp0..\reports
echo ============================================================
echo  REHEARSAL: 1 user / 90 sec (same plan as the real 150 run)
echo ============================================================
if not exist "%SHARE%\token.txt" (
  echo [X] token.txt not found in ..\shared. Paste your access_token there first.
  pause
  exit /b 1
)
echo TOKEN> "%SHARE%\tokens.csv"
for /f "usebackq delims=" %%a in ("%SHARE%\token.txt") do echo %%a>> "%SHARE%\tokens.csv"
echo Ensuring registration limit disabled...
python "%SHARE%\ensure_limit.py"
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TS=%%i
set OUTDIR=%REPORTS%\rehearsal_%TS%
mkdir "%OUTDIR%" 2>nul
call "C:\Tools\apache-jmeter-5.6.3\bin\jmeter.bat" -n -t "%SHARE%\loadtest_150.jmx" -JTHREADS=1 -JRAMP=0 -JDURATION=90 -JTHINK_BROWSE=2000 -JTHINK_BROWSE_R=3000 -JTHINK_FORM=3000 -JTHINK_FORM_R=5000 -l "%OUTDIR%\result.jtl" -j "%OUTDIR%\jmeter.log" -e -o "%OUTDIR%\report"
echo.
echo ============================================================
echo  DONE. Check "summary =" above:  Err: 0 (0.00%%) = all OK
echo  Output: %OUTDIR%
echo ============================================================
start "" "%OUTDIR%\report\index.html"
pause
