# waves.tcl - used by run_gui.bat: records all DUT signals, shows the important ones, runs the test.
# (add_wave only works in the GUI; in batch mode those lines are skipped)
log_wave -recursive /tb_top/dut

proc show {sig} { catch {add_wave $sig} }
proc divider {name} { catch {add_wave_divider $name} }

divider "Clock / interrupts"
show /tb_top/dut/clk
show /tb_top/dut/rst_n
show /tb_top/dut/irq_ch
show /tb_top/dut/irq
divider "Arbiter"
show /tb_top/dut/req
show /tb_top/dut/prio
show /tb_top/dut/grant_fire
show /tb_top/dut/gnt_idx
show /tb_top/dut/u_arb/rr_ptr
divider "Engine FSM"
show /tb_top/dut/u_eng/state
show /tb_top/dut/u_eng/beats
show /tb_top/dut/u_eng/err
divider "AXI read"
show /tb_top/dut/arvalid
show /tb_top/dut/arready
show /tb_top/dut/araddr
show /tb_top/dut/arlen
show /tb_top/dut/rvalid
show /tb_top/dut/rdata
show /tb_top/dut/rresp
show /tb_top/dut/rlast
divider "AXI write"
show /tb_top/dut/awvalid
show /tb_top/dut/awready
show /tb_top/dut/awaddr
show /tb_top/dut/awlen
show /tb_top/dut/wvalid
show /tb_top/dut/wready
show /tb_top/dut/wdata
show /tb_top/dut/wlast
show /tb_top/dut/bvalid
show /tb_top/dut/bresp
divider "Sensor streams"
show /tb_top/dut/s_valid
show /tb_top/dut/s_ready
divider "APB"
show /tb_top/dut/psel
show /tb_top/dut/penable
show /tb_top/dut/pwrite
show /tb_top/dut/paddr
show /tb_top/dut/pwdata
show /tb_top/dut/prdata
show /tb_top/dut/pslverr

run all
