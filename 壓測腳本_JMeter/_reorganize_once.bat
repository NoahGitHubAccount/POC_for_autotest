@echo off
cd /d %~dp0
echo Reorganizing JMeter folder...

md shared 2>nul
md reports 2>nul
md verify 2>nul
md prod_150users 2>nul
md rehearsal_1user 2>nul

rem --- move shared reference files ---
if exist loadtest_150.jmx move /y loadtest_150.jmx shared\ >nul
if exist sessions.csv     move /y sessions.csv     shared\ >nul
if exist token.txt        move /y token.txt        shared\ >nul
if exist tokens.csv       move /y tokens.csv        shared\ >nul
if exist jm.properties    del /q jm.properties

rem --- move registration records into verify ---
if exist registrations.txt move /y registrations.txt verify\ >nul

rem --- move existing reports into reports\ ---
if exist runs (
  for /d %%d in (runs\*) do move "%%d" reports\ >nul 2>nul
  rd /s /q runs
)

rem --- clean old leftovers ---
if exist report_rehearsal      rd /s /q report_rehearsal
if exist result_rehearsal.jtl  del /q result_rehearsal.jtl
if exist jmeter_rehearsal.log  del /q jmeter_rehearsal.log

rem --- remove OLD top-level scripts (replaced by ones in subfolders) ---
if exist rehearsal_1user.bat     del /q rehearsal_1user.bat
if exist run_150users.bat        del /q run_150users.bat
if exist check_registrations.bat del /q check_registrations.bat
if exist check_registrations.py  del /q check_registrations.py

echo.
echo ============================================================
echo  Done. New structure:
echo    shared\          plan + sessions + token
echo    prod_150users\   run_150users.bat
echo    rehearsal_1user\ rehearsal_1user.bat
echo    verify\          check_registrations + registrations.txt
echo    reports\         exported HTML reports
echo  You can delete this _reorganize_once.bat afterwards.
echo ============================================================
pause
