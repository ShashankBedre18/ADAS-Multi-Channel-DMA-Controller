@echo off
rem Open one test in the Vivado simulator GUI with the important signals already in the waveform window.
rem Usage: run_gui.bat <test_name> [seed]      (run build.bat once before)
call "%~dp0env.bat"
cd /d "%~dp0work"
set T=%1
if "%T%"=="" set T=dma_smoke_test
set SEED=%2
if "%SEED%"=="" set SEED=1
(
echo -testplusarg UVM_TESTNAME=%T%
echo -testplusarg ITER=5
echo -sv_seed %SEED%
echo -log ../logs/gui_%T%.log
echo -wdb gui_%T%.wdb
echo -t ../waves.tcl
) > args_gui.txt
call xsim tb_snap -gui -f args_gui.txt
