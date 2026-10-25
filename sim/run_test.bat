@echo off
rem Usage: run_test.bat <test_name> [seed] [random_iterations]
call "%~dp0env.bat"
cd /d "%~dp0work"
set T=%1
set SEED=%2
if "%SEED%"=="" set SEED=1
set ITER=%3
if "%ITER%"=="" set ITER=25
if not exist ..\logs mkdir ..\logs
if not exist ..\cov mkdir ..\cov
(
echo -testplusarg UVM_TESTNAME=%T%
echo -testplusarg ITER=%ITER%
echo -sv_seed %SEED%
echo -log ../logs/%T%_s%SEED%.log
echo -cov_db_dir ../cov
echo -cov_db_name %T%_s%SEED%
echo -R
) > args_%T%.txt
call xsim tb_snap -f args_%T%.txt >nul 2>&1
findstr /C:"TEST PASSED" /C:"TEST FAILED" ..\logs\%T%_s%SEED%.log
