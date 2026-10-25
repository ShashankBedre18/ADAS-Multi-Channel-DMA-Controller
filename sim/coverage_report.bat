@echo off
rem Merge coverage of every run in cov\ and write HTML reports to report\
call "%~dp0env.bat"
cd /d "%~dp0"
if exist report rmdir /s /q report
if exist merged rmdir /s /q merged
set ARGS=
for /d %%d in (cov\xsim.covdb\*) do call set ARGS=%%ARGS%% -cov_db_dir cov -cov_db_name %%~nxd
call xcrg -report_format html -report_dir report\functional -merge_dir merged -merge_db_name all_tests %ARGS% >nul 2>&1
call xcrg -report_format html -report_dir report\code -cov_db_dir work -cov_db_name tb_snap >nul 2>&1
echo Reports: sim\report\functional\functionalCoverageReport\dashboard.html and sim\report\code\codeCoverageReport\dashboard.html
