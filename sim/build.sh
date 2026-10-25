#!/bin/bash
# Compile + elaborate the DUT and UVM testbench with Vivado xsim (run from anywhere).
# Code coverage (statement/branch/condition/toggle) is compiled in.
export PATH="$PATH:/d/Vivado/2025.2/Vivado/bin"
cd "$(dirname "$0")"; rm -rf work; mkdir work; cd work
R=../../rtl; T=../../tb
xvlog.bat -sv -L uvm -i $T/uvm $R/dma_pkg.sv $R/dma_sfifo.sv $R/dma_channel.sv $R/dma_arbiter.sv \
  $R/dma_engine.sv $R/dma_top.sv $T/if/dma_ifs.sv $T/sva/dma_sva.sv $T/uvm/dma_tb_pkg.sv $T/tb_top.sv | grep -v "^INFO"
xelab.bat -L uvm tb_top -s tb_snap -debug typical -timescale 1ns/1ps -cc_type sbct | grep -v "^INFO"
