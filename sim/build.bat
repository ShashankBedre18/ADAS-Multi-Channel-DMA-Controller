@echo off
rem Compile + elaborate DUT and UVM testbench (xsim), with code coverage
call "%~dp0env.bat"
cd /d "%~dp0"
if exist work rmdir /s /q work
mkdir work & cd work
set R=..\..\rtl
set T=..\..\tb
call xvlog -sv -L uvm -i %T%\uvm %R%\dma_pkg.sv %R%\dma_sfifo.sv %R%\dma_channel.sv %R%\dma_arbiter.sv %R%\dma_engine.sv %R%\dma_top.sv %T%\if\dma_ifs.sv %T%\sva\dma_sva.sv %T%\uvm\dma_tb_pkg.sv %T%\tb_top.sv
if errorlevel 1 exit /b 1
call xelab -L uvm tb_top -s tb_snap -debug typical -timescale 1ns/1ps -cc_type sbct
