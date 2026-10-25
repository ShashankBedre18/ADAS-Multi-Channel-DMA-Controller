// ============================================================================
// dma_arbiter.sv - priority arbiter with round-robin between equal priorities
//
//  * each requester carries a 2-bit priority (3 = most critical, e.g. radar)
//  * the highest priority requester wins
//  * equal priorities are served round-robin (starting after the last winner)
//  * arbitration happens once per burst (grant_fire), so a long low-priority
//    transfer can never block a critical sensor for more than one burst
// ============================================================================
module dma_arbiter
  import dma_pkg::*;
(
  input  logic                    clk,
  input  logic                    rst_n,
  input  logic [N_CH-1:0]         req,
  input  logic [N_CH-1:0][1:0]    prio,
  input  logic                    grant_fire,    // engine accepts the grant now
  output logic                    gnt_valid,
  output logic [$clog2(N_CH)-1:0] gnt_idx
);

  logic [$clog2(N_CH)-1:0] rr_ptr;

  // winner selection: highest priority, ties broken by round-robin order
  always_comb begin
    logic [1:0] best;
    int         idx;
    gnt_valid = 1'b0;
    gnt_idx   = '0;
    best      = '0;
    for (int i = 0; i < N_CH; i++) begin
      idx = (int'(rr_ptr) + i) % N_CH;
      if (req[idx] && (!gnt_valid || prio[idx] > best)) begin
        gnt_valid = 1'b1;
        gnt_idx   = idx[$clog2(N_CH)-1:0];
        best      = prio[idx];
      end
    end
  end

  // round-robin pointer: the next tie starts just after the last winner
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)          rr_ptr <= '0;
    else if (grant_fire) rr_ptr <= (gnt_idx == N_CH-1) ? '0 : gnt_idx + 1'b1;
  end

endmodule
