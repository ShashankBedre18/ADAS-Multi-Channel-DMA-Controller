# create_vivado_project.tcl - builds a Vivado GUI project from the project sources.
#
#   Vivado:  Tools > Run Tcl Script...  and choose this file
#   or cmd:  vivado -mode batch -source scripts/create_vivado_project.tcl
#
# Result: <project>/vivado_proj/adas_dma.xpr
#   Design Sources     : rtl/*.sv            (top = dma_top)
#   Simulation Sources : tb/ (UVM testbench) (top = tb_top)
# Change the test in Settings > Simulation > Simulation > xsim.more_options (UVM_TESTNAME=...).

set root     [file normalize [file join [file dirname [info script]] ..]]
set proj_dir [file join $root vivado_proj]

create_project adas_dma $proj_dir -part xc7a100tcsg324-1 -force
set_property target_language Verilog [current_project]

# ---- design sources (synthesizable RTL)
set rtl {dma_pkg.sv dma_sfifo.sv dma_channel.sv dma_arbiter.sv dma_engine.sv dma_top.sv}
foreach f $rtl { add_files -fileset sources_1 [file join $root rtl $f] }
set_property top dma_top [get_filesets sources_1]

# ---- constraint: 100 MHz clock (same as synth/synth.tcl)
set xdc [file join $proj_dir clock.xdc]
set fh [open $xdc w]; puts $fh "create_clock -name clk -period 10.000 \[get_ports clk\]"; close $fh
add_files -fileset constrs_1 $xdc

# ---- simulation sources (UVM testbench + assertions)
add_files -fileset sim_1 [list \
    [file join $root tb if dma_ifs.sv] \
    [file join $root tb sva dma_sva.sv] \
    [file join $root tb uvm dma_tb_pkg.sv] \
    [file join $root tb tb_top.sv]]
add_files -fileset sim_1 [glob [file join $root tb uvm *.svh]]
set_property include_dirs [list [file join $root tb uvm]] [get_filesets sim_1]
set_property top tb_top [get_filesets sim_1]
set_property top_lib xil_defaultlib [get_filesets sim_1]

# ---- simulator settings: UVM library, timescale, test name, run to the end
set sim [get_filesets sim_1]
set_property -name {xsim.compile.xvlog.more_options}   -value {-L uvm}                         -objects $sim
set_property -name {xsim.elaborate.xelab.more_options} -value {-L uvm -timescale 1ns/1ps}      -objects $sim
set_property -name {xsim.simulate.xsim.more_options}   -value {-testplusarg UVM_TESTNAME=dma_smoke_test} -objects $sim
set_property -name {xsim.simulate.runtime}             -value {all}                            -objects $sim
set_property -name {xsim.simulate.log_all_signals}     -value {true}                           -objects $sim

update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
puts "Created [file join $proj_dir adas_dma.xpr]"
