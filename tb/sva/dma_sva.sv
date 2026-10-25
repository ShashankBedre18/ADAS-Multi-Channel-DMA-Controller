// ============================================================================
// dma_sva.sv - protocol and design assertions, bound into the DUT
// ============================================================================
`timescale 1ns/1ps

module dma_sva
  import dma_pkg::*;
(
  input logic                         clk, rst_n,
  // APB
  input logic                         psel, penable, pwrite, pready, pslverr,
  input logic [11:0]                  paddr,
  input logic [31:0]                  pwdata,
  // AXI
  input logic [31:0]                  awaddr, araddr, wdata,
  input logic [7:0]                   awlen, arlen,
  input logic [2:0]                   awsize, arsize,
  input logic [1:0]                   awburst, arburst,
  input logic [3:0]                   wstrb,
  input logic                         awvalid, awready, wvalid, wready, wlast,
  input logic                         bvalid, bready, arvalid, arready,
  input logic                         rvalid, rready, rlast,
  // arbitration
  input logic [N_CH-1:0]              req,
  input logic [N_CH-1:0][1:0]         prio,
  input logic                         gnt_valid, grant_fire,
  input logic [$clog2(N_CH)-1:0]      gnt_idx,
  input logic [N_CH-1:0]              irq_ch,
  input logic                         irq
);
  default clocking cb @(posedge clk); endclocking

  // ------------------------------------------------------------------ APB
  a_apb_access_follows_setup : assert property (disable iff (!rst_n) psel && !penable |=> psel && penable)
    else $error("APB: access phase must follow setup phase");
  a_apb_stable_in_setup      : assert property (disable iff (!rst_n) psel && !penable |=> $stable(paddr) && $stable(pwrite) && $stable(pwdata))
    else $error("APB: control signals changed between setup and access");
  a_apb_pready               : assert property (disable iff (!rst_n) psel && penable |-> pready)
    else $error("APB: slave must be ready (zero wait state design)");
  a_apb_slverr_phase         : assert property (disable iff (!rst_n) pslverr |-> psel && penable)
    else $error("APB: PSLVERR outside access phase");

  // ------------------------------------------------------------------ AXI handshake stability
  a_aw_stable : assert property (disable iff (!rst_n)
      awvalid && !awready |=> awvalid && $stable(awaddr) && $stable(awlen))
    else $error("AXI: AW changed/dropped before AWREADY");
  a_ar_stable : assert property (disable iff (!rst_n)
      arvalid && !arready |=> arvalid && $stable(araddr) && $stable(arlen))
    else $error("AXI: AR changed/dropped before ARREADY");
  a_w_stable  : assert property (disable iff (!rst_n)
      wvalid && !wready |=> wvalid && $stable(wdata) && $stable(wlast) && $stable(wstrb))
    else $error("AXI: W changed/dropped before WREADY");

  // ------------------------------------------------------------------ AXI payload legality
  a_aw_attr : assert property (disable iff (!rst_n) awvalid |-> awsize == 3'd2 && awburst == 2'b01 && awaddr[1:0] == 2'b00
                                         && awlen <= MAX_BEATS-1)
    else $error("AXI: illegal AW attributes");
  a_ar_attr : assert property (disable iff (!rst_n) arvalid |-> arsize == 3'd2 && arburst == 2'b01 && araddr[1:0] == 2'b00
                                         && arlen <= MAX_BEATS-1)
    else $error("AXI: illegal AR attributes");
  a_aw_4k   : assert property (disable iff (!rst_n) awvalid |-> ({1'b0, awaddr[11:0]} + ((13'(awlen) + 13'd1) << 2)) <= 13'd4096)
    else $error("AXI: write burst crosses a 4KB boundary");
  a_ar_4k   : assert property (disable iff (!rst_n) arvalid |-> ({1'b0, araddr[11:0]} + ((13'(arlen) + 13'd1) << 2)) <= 13'd4096)
    else $error("AXI: read burst crosses a 4KB boundary");

  // WLAST must be on exactly the AWLEN+1'th beat
  logic [8:0] wcnt;
  logic [7:0] awlen_q;
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin wcnt <= '0; awlen_q <= '0; end
    else begin
      if (awvalid && awready) awlen_q <= awlen;
      if (wvalid && wready)   wcnt <= wlast ? 9'd0 : wcnt + 9'd1;
    end
  end
  a_wlast_pos : assert property (disable iff (!rst_n) wvalid && wready |-> (wlast == (wcnt == 9'(awlen_q))))
    else $error("AXI: WLAST not on final beat");

  // one phase at a time (single outstanding burst design)
  a_one_phase : assert property (disable iff (!rst_n) $onehot0({awvalid, wvalid, arvalid, bready, rready}))
    else $error("Engine: more than one AXI phase active at once");

  // ------------------------------------------------------------------ arbitration
  a_gnt_is_req  : assert property (disable iff (!rst_n) gnt_valid |-> req[gnt_idx])
    else $error("Arbiter: grant to a non-requesting channel");
  a_fire_has_gnt: assert property (disable iff (!rst_n) grant_fire |-> gnt_valid)
    else $error("Arbiter: fire without valid grant");

  // the winner always has the highest priority among requesters
  for (genvar i = 0; i < N_CH; i++) begin : g_prio
    a_prio_order : assert property (disable iff (!rst_n) grant_fire && req[i] |-> prio[gnt_idx] >= prio[i])
      else $error("Arbiter: channel %0d bypassed by a lower priority winner", i);
  end

  // ------------------------------------------------------------------ interrupts
  a_irq_or : assert property (disable iff (!rst_n) irq == |irq_ch)
    else $error("IRQ: global irq is not OR of channel irqs");

  // ------------------------------------------------------------------ cover points
  c_multi_req    : cover property (disable iff (!rst_n) grant_fire && $countones(req) >= 2);
  c_all_req      : cover property (disable iff (!rst_n) grant_fire && (&req));
  c_full_burst   : cover property (disable iff (!rst_n) awvalid && awlen == MAX_BEATS-1);
  c_single_beat  : cover property (disable iff (!rst_n) awvalid && awlen == 0);
endmodule

// -------------------------------------------------------------------------------
// per-channel checker, bound into every dma_channel
// -------------------------------------------------------------------------------
module dma_ch_sva
  import dma_pkg::*;
(
  input logic                         clk, rst_n,
  input logic                         s_ready, active, src_stream, fifo_pop, upd,
  input logic                         inflight, req, en, irq, start_bad,
  input logic [5:0]                   fifo_cnt,
  input logic [1:0]                   int_stat, int_en,
  input logic [4:0]                   next_beats
);
  default clocking cb @(posedge clk); endclocking

  a_sready_only_active : assert property (disable iff (!rst_n) s_ready |-> active && src_stream)
    else $error("CH: accepting sensor data while inactive");
  a_no_underflow       : assert property (disable iff (!rst_n) fifo_pop |-> fifo_cnt != 0)
    else $error("CH: FIFO underflow");
  a_fifo_bound         : assert property (disable iff (!rst_n) fifo_cnt <= FIFO_DEPTH)
    else $error("CH: FIFO overflow");
  a_upd_needs_inflight : assert property (disable iff (!rst_n) upd |-> inflight)
    else $error("CH: completion for a channel that is not in flight");
  a_req_legal          : assert property (disable iff (!rst_n) req |-> active && en)
    else $error("CH: request from inactive channel");
  a_irq_def            : assert property (disable iff (!rst_n) irq == |(int_stat & int_en))
    else $error("CH: irq != |(INT_STAT & INT_EN)");
  a_bad_start_inactive : assert property (disable iff (!rst_n) start_bad |=> !active)
    else $error("CH: illegal start activated channel");
  a_beats_range        : assert property (disable iff (!rst_n) req |-> next_beats >= 1 && next_beats <= MAX_BEATS)
    else $error("CH: next_beats out of range");
  c_stall              : cover property (disable iff (!rst_n) !s_ready && active && src_stream && fifo_cnt == FIFO_DEPTH);
  c_bad_start          : cover property (disable iff (!rst_n) start_bad);
endmodule
