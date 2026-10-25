# Out-of-context synthesis of the DMA subsystem (utilisation + timing estimate)
#   vivado -mode batch -source synth.tcl
set part  xc7a100tcsg324-1
set rtl   [file normalize ../rtl]
read_verilog -sv [list $rtl/dma_pkg.sv $rtl/dma_sfifo.sv $rtl/dma_channel.sv $rtl/dma_arbiter.sv $rtl/dma_engine.sv $rtl/dma_top.sv]
synth_design -top dma_top -part $part -mode out_of_context
create_clock -name clk -period 10.0 [get_ports clk]
report_utilization    -file utilization_synth.rpt
report_timing_summary -file timing_synth.rpt -max_paths 5
puts "SYNTHESIS DONE"
