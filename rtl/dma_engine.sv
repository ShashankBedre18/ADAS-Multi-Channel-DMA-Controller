// ============================================================================
// dma_engine.sv - shared burst engine + AXI4 master
//
// One burst at a time, store-and-forward through a 16-word burst buffer:
//   IDLE -> LATCH -> (RD_AR -> RD_DATA | STR_RD) -> WR_AW -> WR_W -> WR_B -> UPD -> SETTLE -> IDLE
// Source is either AXI memory (AR/R) or the channel's sensor FIFO.
// ============================================================================
module dma_engine
  import dma_pkg::*;
(
  input  logic                          clk,
  input  logic                          rst_n,

  // arbiter
  input  logic                          gnt_valid,
  input  logic [$clog2(N_CH)-1:0]       gnt_idx,
  output logic                          grant_fire,

  // per-channel context
  input  logic [N_CH-1:0][4:0]          next_beats,
  input  logic [N_CH-1:0][ADDR_W-1:0]   src_addr,
  input  logic [N_CH-1:0][ADDR_W-1:0]   dst_addr,
  input  logic [N_CH-1:0]               src_stream,
  input  logic [N_CH-1:0][DATA_W-1:0]   fifo_rdata,
  output logic [N_CH-1:0]               fifo_pop,
  output logic [N_CH-1:0]               inflight,
  output logic [N_CH-1:0]               upd,
  output logic [4:0]                    upd_beats,
  output logic [2:0]                    upd_err,

  // AXI4 master (single outstanding burst, INCR, 32-bit)
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

  // status
  output logic                          busy
);

  typedef enum logic [3:0] {
    S_IDLE, S_RD_AR, S_RD_DATA, S_STR_RD, S_WR_AW, S_WR_W, S_WR_B, S_UPD, S_SETTLE, S_LATCH
  } state_e;

  state_e                       state, nstate;
  logic [$clog2(N_CH)-1:0]      cur;
  logic [4:0]                   beats, cnt;
  logic [ADDR_W-1:0]            rd_addr, wr_addr;
  logic [2:0]                   err;
  logic [DATA_W-1:0]            bbuf [MAX_BEATS];

  function automatic logic [2:0] resp2err(input logic [1:0] r);
    case (r)
      AXI_SLVERR: return ERR_SLVERR;
      AXI_DECERR: return ERR_DECERR;
      default:    return ERR_NONE;
    endcase
  endfunction

  // ---- constant AXI attributes ----------------------------------------------------
  assign awsize  = 3'd2;
  assign arsize  = 3'd2;
  assign awburst = 2'b01;
  assign arburst = 2'b01;
  assign wstrb   = '1;

  assign awaddr  = wr_addr;
  assign awlen   = {3'd0, beats - 5'd1};
  assign araddr  = rd_addr;
  assign arlen   = {3'd0, beats - 5'd1};

  assign awvalid = (state == S_WR_AW);
  assign arvalid = (state == S_RD_AR);
  assign rready  = (state == S_RD_DATA);
  assign wvalid  = (state == S_WR_W);
  assign wdata   = bbuf[cnt[3:0]];
  assign wlast   = (state == S_WR_W) && (cnt == beats - 5'd1);
  assign bready  = (state == S_WR_B);

  assign busy       = (state != S_IDLE);
  assign grant_fire = (state == S_IDLE) && gnt_valid;

  always_comb begin
    inflight = '0;
    fifo_pop = '0;
    upd      = '0;
    if (state != S_IDLE) inflight[cur] = 1'b1;
    if (state == S_STR_RD) fifo_pop[cur] = 1'b1;
    if (state == S_UPD)    upd[cur]      = 1'b1;
  end
  assign upd_beats = (err != ERR_NONE) ? 5'd0 : beats;
  assign upd_err   = err;

  // burst buffer: no reset, written from the AXI read data or the sensor FIFO
  always_ff @(posedge clk) begin
    if (state == S_RD_DATA && rvalid) bbuf[cnt[3:0]] <= rdata;
    else if (state == S_STR_RD)       bbuf[cnt[3:0]] <= fifo_rdata[cur];
  end

  // ---- state machine ----------------------------------------------------------------------
  always_comb begin
    nstate = state;
    case (state)
      S_IDLE:    if (gnt_valid) nstate = S_LATCH;
      S_LATCH:   nstate = src_stream[cur] ? S_STR_RD : S_RD_AR;
      S_RD_AR:   if (arready) nstate = S_RD_DATA;
      S_RD_DATA: if (rvalid && rlast) nstate = (err != ERR_NONE || resp2err(rresp) != ERR_NONE)
                                               ? S_UPD : S_WR_AW;
      S_STR_RD:  if (cnt == beats - 5'd1) nstate = S_WR_AW;
      S_WR_AW:   if (awready) nstate = S_WR_W;
      S_WR_W:    if (wready && wlast) nstate = S_WR_B;
      S_WR_B:    if (bvalid) nstate = S_UPD;
      S_UPD:     nstate = S_SETTLE;    // channel context is updated; let its request register catch up
      S_SETTLE:  nstate = S_IDLE;
      default:   nstate = S_IDLE;
    endcase
  end

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= S_IDLE; cur <= '0; beats <= '0; cnt <= '0;
      rd_addr <= '0; wr_addr <= '0; err <= ERR_NONE;
    end else begin
      state     <= nstate;

      case (state)
        S_IDLE: if (gnt_valid) cur <= gnt_idx;
        S_LATCH: begin                       // capture the burst parameters of the granted channel
          beats   <= next_beats[cur];
          rd_addr <= src_addr[cur];
          wr_addr <= dst_addr[cur];
          cnt     <= '0;
          err     <= ERR_NONE;
        end
        S_RD_AR: if (arready) cnt <= '0;
        S_RD_DATA: if (rvalid) begin
          cnt            <= cnt + 5'd1;
          if (err == ERR_NONE) err <= resp2err(rresp);
          if (rlast) cnt <= '0;
        end
        S_STR_RD: begin
          cnt            <= (cnt == beats - 5'd1) ? 5'd0 : cnt + 5'd1;
        end
        S_WR_AW: if (awready) cnt <= '0;
        S_WR_W:  if (wready)  cnt <= wlast ? 5'd0 : cnt + 5'd1;
        S_WR_B:  if (bvalid && err == ERR_NONE) err <= resp2err(bresp);
        default: ;
      endcase
    end
  end

endmodule
