// ============================================================================
// UVM tests: a base test plus one thin test class per virtual sequence
// ============================================================================

class dma_base_test extends uvm_test;
  `uvm_component_utils(dma_base_test)
  dma_env        env;
  virtual dbg_if dbg;

  function new(string name, uvm_component parent); super.new(name, parent); endfunction

  function void build_phase(uvm_phase phase);
    env = dma_env::type_id::create("env", this);
    if (!uvm_config_db#(virtual dbg_if)::get(this, "", "dbg_vif", dbg)) `uvm_fatal("NOVIF", "dbg_vif")
  endfunction

  function void end_of_elaboration_phase(uvm_phase phase);
    uvm_top.set_timeout(200ms, 0);          // global hang guard
  endfunction

  virtual function uvm_sequence_base create_seq();
    return null;
  endfunction

  task run_phase(uvm_phase phase);
    uvm_sequence_base seq;
    phase.raise_objection(this);
    wait (dbg.rst_n === 1'b1);
    repeat (5) @(posedge dbg.clk);
    seq = create_seq();
    seq.start(env.vsqr);
    repeat (200) @(posedge dbg.clk);
    phase.drop_objection(this);
  endtask

  function void report_phase(uvm_phase phase);
    uvm_report_server svr = uvm_report_server::get_server();
    if (svr.get_severity_count(UVM_ERROR) + svr.get_severity_count(UVM_FATAL) == 0)
      `uvm_info("RESULT", $sformatf("*** TEST PASSED: %s ***", get_type_name()), UVM_NONE)
    else
      `uvm_info("RESULT", $sformatf("*** TEST FAILED: %s (%0d errors) ***", get_type_name(),
                svr.get_severity_count(UVM_ERROR) + svr.get_severity_count(UVM_FATAL)), UVM_NONE)
  endfunction
endclass

`define DMA_TEST(TNAME, SEQCLS) \
class TNAME extends dma_base_test; \
  `uvm_component_utils(TNAME) \
  function new(string name, uvm_component parent); super.new(name, parent); endfunction \
  virtual function uvm_sequence_base create_seq(); \
    SEQCLS s = SEQCLS::type_id::create("s"); \
    return s; \
  endfunction \
endclass

`DMA_TEST(dma_regs_test,          dma_regs_vseq)
`DMA_TEST(dma_smoke_test,         dma_smoke_vseq)
`DMA_TEST(dma_sensor_fusion_test, dma_sensor_fusion_vseq)
`DMA_TEST(dma_burst_sweep_test,   dma_burst_sweep_vseq)
`DMA_TEST(dma_priority_test,      dma_priority_vseq)
`DMA_TEST(dma_error_test,         dma_error_vseq)
`DMA_TEST(dma_cfg_err_test,       dma_cfg_err_vseq)
`DMA_TEST(dma_backpressure_test,  dma_backpressure_vseq)
`DMA_TEST(dma_random_test,        dma_random_vseq)
