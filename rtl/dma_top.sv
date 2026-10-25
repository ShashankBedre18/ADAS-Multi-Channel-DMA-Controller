// ============================================================================
// dma_top.sv - ADAS multi-channel DMA subsystem top level
//
//   APB slave  : control/status registers (see docs/03_register_map.md)
//   AXI4 master: memory side (single outstanding INCR burst, 32-bit)
//   Sensor ports: N_CH valid/ready word streams (camera, radar, lidar, ...)
//   Interrupts : one per channel + global OR
// ============================================================================
module dma_top
  import dma_pkg::*;
(
  input  logic                          clk,
  input  logic                          rst_n,

  // APB slave
  input  logic                          psel,
  input  logic                          penable,
  input  logic                          pwrite,
  input  logic [11:0]                   paddr,
  input  logic [31:0]                   pwdata,
  output logic [31:0]                   prdata,
  output logic                          pready,
  output logic                          pslverr,

  // sensor streams
  input  logic [N_CH-1:0]               s_valid,
  input  logic [N_CH-1:0][DATA_W-1:0]   s_data,
  output logic [N_CH-1:0]               s_ready,

  // AXI4 master
  output logic [ADDR_W-1:0]             awaddr,
  output logic [7:0]                    awlen,
  output logic [2:0]                    awsize,
  output logic [1:0]                    awburst,
  output logic                          awvalid,
  input  logic                          awready,
  output logic [DATA_W-1:0]             wdata,
  output logic [DATA_W/8-1:0]           wstrb,
  output logic                          wlast,
  output logic                          wvalid,
  input  logic                          wready,
  input  logic [1:0]                    bresp,
  input  logic                          bvalid,
  output logic                          bready,
  output logic [ADDR_W-1:0]             araddr,
  output logic [7:0]                    arlen,
  output logic [2:0]                    arsize,
  output logic [1:0]                    arburst,
  output logic                          arvalid,
  input  logic                          arready,
  input  logic [DATA_W-1:0]             rdata,
  input  logic [1:0]                    rresp,
  input  logic                          rlast,
  input  logic                          rvalid,
  output logic                          rready,

  // interrupts
  output logic [N_CH-1:0]               irq_ch,
  output logic                          irq
);

  // ---- global registers -----------------------------------------------------------
  logic        gl_en;

  // ---- APB access decode ------------------------------------------------------------
  wire apb_acc = psel && penable;
  wire apb_wr  = apb_acc && pwrite;
  assign pready = 1'b1;

  wire        in_ch_win = (paddr >= CH_BASE) && (paddr < CH_BASE + 12'(N_CH) * CH_STRIDE);
  wire [11:0] ch_off    = paddr - CH_BASE;
  wire [3:0]  ch_sel_w  = ch_off[9:6];            // stride is 0x40
  wire [3:0]  ch_word   = ch_off[5:2];
  wire        ch_word_ok = (ch_word <= CH_LAST);

  logic        glob_ok;
  always_comb begin
    case (paddr)
      REG_GCTRL, REG_GSTAT, REG_IRQ_SUM, REG_VERSION: glob_ok = 1'b1;
      default: glob_ok = 1'b0;
    endcase
  end
  assign pslverr = apb_acc && !((in_ch_win && ch_word_ok) || (!in_ch_win && glob_ok));

  // ---- channel instances -------------------------------------------------------------
  logic [N_CH-1:0]              req, src_stream, inflight, fifo_pop, upd, active;
  logic [N_CH-1:0][1:0]         prio;
  logic [N_CH-1:0][4:0]         next_beats;
  logic [N_CH-1:0][ADDR_W-1:0]  src_addr, dst_addr;
  logic [N_CH-1:0][DATA_W-1:0]  fifo_rdata;
  logic [N_CH-1:0][31:0]        ch_rdata;
  logic [4:0]                   upd_beats;
  logic [2:0]                   upd_err;

  for (genvar c = 0; c < N_CH; c++) begin : g_ch
    dma_channel u_ch (
      .clk, .rst_n, .gl_en,
      .reg_wr    (apb_wr && in_ch_win && ch_word_ok && (ch_sel_w == c)),
      .reg_waddr (ch_word),
      .reg_wdata (pwdata),
      .reg_raddr (ch_word),
      .reg_rdata (ch_rdata[c]),
      .s_valid   (s_valid[c]),
      .s_data    (s_data[c]),
      .s_ready   (s_ready[c]),
      .req       (req[c]),
      .prio      (prio[c]),
      .next_beats(next_beats[c]),
      .src_addr  (src_addr[c]),
      .dst_addr  (dst_addr[c]),
      .src_stream(src_stream[c]),
      .inflight  (inflight[c]),
      .fifo_pop  (fifo_pop[c]),
      .fifo_rdata(fifo_rdata[c]),
      .upd       (upd[c]),
      .upd_beats,
      .upd_err,
      .irq       (irq_ch[c]),
      .active_o  (active[c])
    );
  end

  // ---- arbiter + engine -------------------------------------------------------------------
  logic                      gnt_valid, grant_fire, eng_busy;
  logic [$clog2(N_CH)-1:0]   gnt_idx;

  dma_arbiter u_arb (
    .clk, .rst_n, .req, .prio,
    .grant_fire, .gnt_valid, .gnt_idx
  );

  dma_engine u_eng (
    .clk, .rst_n,
    .gnt_valid, .gnt_idx, .grant_fire,
    .next_beats, .src_addr, .dst_addr, .src_stream, .fifo_rdata,
    .fifo_pop, .inflight, .upd, .upd_beats, .upd_err,
    .awaddr, .awlen, .awsize, .awburst, .awvalid, .awready,
    .wdata, .wstrb, .wlast, .wvalid, .wready,
    .bresp, .bvalid, .bready,
    .araddr, .arlen, .arsize, .arburst, .arvalid, .arready,
    .rdata, .rresp, .rlast, .rvalid, .rready,
    .busy(eng_busy)
  );

  // ---- global registers ------------------------------------------------------------------------
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)                              gl_en <= 1'b0;
    else if (apb_wr && paddr == REG_GCTRL)   gl_en <= pwdata[0];
  end

  // ---- APB read mux ---------------------------------------------------------------------------------
  always_comb begin
    prdata = '0;
    if (in_ch_win) begin
      if (ch_sel_w < N_CH) prdata = ch_rdata[ch_sel_w[$clog2(N_CH)-1:0]];
    end else begin
      case (paddr)
        REG_GCTRL:     prdata = {31'd0, gl_en};
        REG_GSTAT:     prdata = 32'(active) | (32'(eng_busy) << 8);
        REG_IRQ_SUM:   prdata = 32'(irq_ch);
        REG_VERSION:   prdata = VERSION;
        default:       prdata = '0;
      endcase
    end
  end

  assign irq = |irq_ch;

endmodule
