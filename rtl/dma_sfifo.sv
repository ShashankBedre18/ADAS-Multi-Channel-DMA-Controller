// Synchronous FIFO with first-word-fall-through read and synchronous flush.
module dma_sfifo #(
  parameter int W     = 32,
  parameter int DEPTH = 32
) (
  input  logic                     clk,
  input  logic                     rst_n,
  input  logic                     flush,
  input  logic                     wr_en,
  input  logic [W-1:0]             wdata,
  output logic                     full,
  input  logic                     rd_en,
  output logic [W-1:0]             rdata,
  output logic [$clog2(DEPTH):0]   count
);
  localparam int AW = $clog2(DEPTH);
  logic [W-1:0]  mem [DEPTH];
  logic [AW-1:0] wptr, rptr;

  assign full  = (count == DEPTH);
  assign rdata = mem[rptr];

  wire do_wr = wr_en && !full;
  wire do_rd = rd_en && (count != 0);

  // storage has no reset so that it can map onto LUT-RAM
  always_ff @(posedge clk) if (do_wr) mem[wptr] <= wdata;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      wptr  <= '0;
      rptr  <= '0;
      count <= '0;
    end else if (flush) begin
      wptr  <= '0;
      rptr  <= '0;
      count <= '0;
    end else begin
      if (do_wr) wptr <= wptr + 1'b1;
      if (do_rd) rptr <= rptr + 1'b1;
      count <= count + (do_wr ? 1 : 0) - (do_rd ? 1 : 0);
    end
  end
endmodule
