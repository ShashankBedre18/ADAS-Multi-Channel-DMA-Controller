@echo off
rem Full regression: build, run all tests, merge coverage, write reports
call "%~dp0build.bat"
cd /d "%~dp0"
if exist logs rmdir /s /q logs
if exist cov rmdir /s /q cov
mkdir logs & mkdir cov
for %%t in (regs smoke sensor_fusion burst_sweep priority error cfg_err backpressure) do call "%~dp0run_test.bat" dma_%%t_test 1
for %%s in (11 12 13 14 15) do call "%~dp0run_test.bat" dma_random_test %%s 40
call "%~dp0coverage_report.bat"
