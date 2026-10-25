// ============================================================================
// tb_top.sv - clock/reset, DUT, interfaces, assertion binds, UVM start
// ============================================================================
`timescale 1ns/1ps

// assertion modules are attached to the DUT without touching RTL
bind dma_top     dma_sva    u_sva    (.*);
bind dma_channel dma_ch_sva u_ch_sva (.*);

module tb_top;
  import uvm_pkg::*;
  import dma_pkg::*;
  import dma_tb_pkg::*;

  logic clk = 0;
  logic rst_n;
  always #5 clk = ~clk;                     // 100 MHz

  initial begin
    rst_n = 0;
    repeat (10) @(posedge clk);
    #1 rst_n = 1;
  end

  apb_if  apb  (clk, rst_n);
  axi_if  axi  (clk, rst_n);
  strm_if strm [N_CH] (clk, rst_n);
  dbg_if  #(N_CH) dbg (clk, rst_n);

  logic [N_CH-1:0]             s_valid, s_ready;
  logic [N_CH-1:0][DATA_W-1:0] s_data;
  logic [N_CH-1:0]             irq_ch;
  logic                        irq;

  for (genvar c = 0; c < N_CH; c++) begin : g_strm
    assign s_valid[c]       = strm[c].valid;
    assign s_data[c]        = strm[c].data;
    assign strm[c].ready    = s_ready[c];
  end

  dma_top dut (
    .clk, .rst_n,
    .psel(apb.psel), .penable(apb.penable), .pwrite(apb.pwrite), .paddr(apb.paddr),
    .pwdata(apb.pwdata), .prdata(apb.prdata), .pready(apb.pready), .pslverr(apb.pslverr),
    .s_valid, .s_data, .s_ready,
    .awaddr(axi.awaddr), .awlen(axi.awlen), .awsize(axi.awsize), .awburst(axi.awburst),
    .awvalid(axi.awvalid), .awready(axi.awready),
    .wdata(axi.wdata), .wstrb(axi.wstrb), .wlast(axi.wlast), .wvalid(axi.wvalid), .wready(axi.wready),
    .bresp(axi.bresp), .bvalid(axi.bvalid), .bready(axi.bready),
    .araddr(axi.araddr), .arlen(axi.arlen), .arsize(axi.arsize), .arburst(axi.arburst),
    .arvalid(axi.arvalid), .arready(axi.arready),
    .rdata(axi.rdata), .rresp(axi.rresp), .rlast(axi.rlast), .rvalid(axi.rvalid), .rready(axi.rready),
    .irq_ch, .irq
  );

  // internal observation points
  assign dbg.req        = dut.req;
  assign dbg.irq_ch     = irq_ch;
  assign dbg.active     = dut.active;
  assign dbg.prio       = dut.prio;
  assign dbg.gnt_valid  = dut.gnt_valid;
  assign dbg.grant_fire = dut.grant_fire;
  assign dbg.eng_busy   = dut.eng_busy;
  assign dbg.gnt_idx    = dut.gnt_idx;
  for (genvar c = 0; c < N_CH; c++) begin : g_dbg
    assign dbg.fifo_cnt[c] = dut.g_ch[c].u_ch.fifo_cnt;
  end

  initial begin
    uvm_config_db#(virtual apb_if)::set(null, "uvm_test_top.env.apb*", "apb_vif", apb);
    uvm_config_db#(virtual axi_if)::set(null, "uvm_test_top.env.axi*", "axi_vif", axi);
    uvm_config_db#(virtual dbg_if#(N_CH))::set(null, "*", "dbg_vif", dbg);
    uvm_config_db#(virtual strm_if)::set(null, "uvm_test_top.env.strm0*", "strm_vif", strm[0]);
    uvm_config_db#(virtual strm_if)::set(null, "uvm_test_top.env.strm1*", "strm_vif", strm[1]);
    uvm_config_db#(virtual strm_if)::set(null, "uvm_test_top.env.strm2*", "strm_vif", strm[2]);
    uvm_config_db#(virtual strm_if)::set(null, "uvm_test_top.env.strm3*", "strm_vif", strm[3]);
    run_test();
  end

  // optional waveform dump:  xsim ... -testplusarg WAVES
  initial if ($test$plusargs("WAVES")) begin
    $dumpfile("dma.vcd");
    $dumpvars(0, tb_top);
  end
endmodule
