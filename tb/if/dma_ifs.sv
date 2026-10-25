// ============================================================================
// Testbench interfaces
// ============================================================================
`timescale 1ns/1ps

interface apb_if (input logic clk, input logic rst_n);
  logic        psel, penable, pwrite, pready, pslverr;
  logic [11:0] paddr;
  logic [31:0] pwdata, prdata;

  clocking drv_cb @(posedge clk);
    default input #1step output #1;
    output psel, penable, pwrite, paddr, pwdata;
    input  prdata, pready, pslverr;
  endclocking
  clocking mon_cb @(posedge clk);
    default input #1step;
    input psel, penable, pwrite, paddr, pwdata, prdata, pready, pslverr;
  endclocking
endinterface

interface axi_if (input logic clk, input logic rst_n);
  logic [31:0] awaddr, araddr, wdata, rdata;
  logic [7:0]  awlen, arlen;
  logic [2:0]  awsize, arsize;
  logic [1:0]  awburst, arburst, bresp, rresp;
  logic [3:0]  wstrb;
  logic        awvalid, awready, wvalid, wready, wlast, bvalid, bready;
  logic        arvalid, arready, rvalid, rready, rlast;

  // slave-side (responder) clocking block
  clocking slv_cb @(posedge clk);
    default input #1step output #1;
    input  awaddr, awlen, awsize, awburst, awvalid;
    output awready;
    input  wdata, wstrb, wlast, wvalid;
    output wready;
    output bresp, bvalid;
    input  bready;
    input  araddr, arlen, arsize, arburst, arvalid;
    output arready;
    output rdata, rresp, rlast, rvalid;
    input  rready;
  endclocking
  clocking mon_cb @(posedge clk);
    default input #1step;
    input awaddr, awlen, awvalid, awready, wdata, wstrb, wlast, wvalid, wready,
          bresp, bvalid, bready, araddr, arlen, arvalid, arready,
          rdata, rresp, rlast, rvalid, rready;
  endclocking
endinterface

// one sensor stream (instantiated once per channel)
interface strm_if (input logic clk, input logic rst_n);
  logic        valid, ready;
  logic [31:0] data;

  clocking drv_cb @(posedge clk);
    default input #1step output #1;
    output valid, data;
    input  ready;
  endclocking
  clocking mon_cb @(posedge clk);
    default input #1step;
    input valid, data, ready;
  endclocking
endinterface

// DUT-internal observation points for the arbitration monitor and coverage
interface dbg_if #(parameter int N = 4) (input logic clk, input logic rst_n);
  logic [N-1:0]       req, irq_ch, active;
  logic [N-1:0][1:0]  prio;
  logic               gnt_valid, grant_fire, eng_busy;
  logic [1:0]         gnt_idx;
  logic [N-1:0][5:0]  fifo_cnt;
  clocking mon_cb @(posedge clk);
    default input #1step;
    input req, irq_ch, prio, gnt_valid, grant_fire, eng_busy,
          gnt_idx, fifo_cnt, active;
  endclocking
endinterface
