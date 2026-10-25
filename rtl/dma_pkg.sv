// ============================================================================
// dma_pkg.sv  -  Global parameters, error codes and register map
// ADAS Multi-Channel DMA Controller Subsystem
// ============================================================================
package dma_pkg;

  // ---- compile-time configuration ------------------------------------------
  parameter int N_CH       = 4;        // number of DMA channels
  parameter int DATA_W     = 32;       // AXI / stream data width
  parameter int ADDR_W     = 32;
  parameter int MAX_BEATS  = 16;       // max beats per burst (AXI len <= 15)
  parameter int FIFO_DEPTH = 32;       // per-channel sensor stream FIFO (words)
  parameter int LEN_W      = 24;       // transfer length field (words)
  parameter logic [31:0] VERSION = 32'h0001_0000;

  // ---- error codes (CHx_STATUS.ERR_CODE) -------------------------------------
  typedef enum logic [2:0] {
    ERR_NONE    = 3'd0,
    ERR_SLVERR  = 3'd1,   // AXI SLVERR from the memory system
    ERR_DECERR  = 3'd2,   // AXI DECERR (unmapped address)
    ERR_CFG     = 3'd3    // illegal configuration at START
  } err_e;

  // ---- interrupt bit positions (INT_EN / INT_STAT) ---------------------------
  localparam int INT_DONE  = 0;   // transfer (frame) complete
  localparam int INT_ERR   = 1;   // error, see STATUS.ERR_CODE

  // ---- global register offsets ------------------------------------------------
  localparam logic [11:0] REG_GCTRL     = 12'h000;
  localparam logic [11:0] REG_GSTAT     = 12'h004;
  localparam logic [11:0] REG_IRQ_SUM   = 12'h008;
  localparam logic [11:0] REG_VERSION   = 12'h00C;

  // ---- per-channel window -------------------------------------------------------
  localparam logic [11:0] CH_BASE   = 12'h100;
  localparam logic [11:0] CH_STRIDE = 12'h040;
  // word offsets (paddr[5:2]) inside a channel window
  localparam logic [3:0] CH_CTRL     = 4'd0;
  localparam logic [3:0] CH_SRC      = 4'd1;
  localparam logic [3:0] CH_DST      = 4'd2;
  localparam logic [3:0] CH_LEN      = 4'd3;
  localparam logic [3:0] CH_INT_EN   = 4'd4;
  localparam logic [3:0] CH_INT_STAT = 4'd5;
  localparam logic [3:0] CH_STATUS   = 4'd6;
  localparam logic [3:0] CH_REMAIN   = 4'd7;
  localparam logic [3:0] CH_XFERRED  = 4'd8;
  localparam logic [3:0] CH_LAST     = CH_XFERRED;   // highest valid word offset

  // AXI constants
  localparam logic [1:0] AXI_OKAY   = 2'b00;
  localparam logic [1:0] AXI_SLVERR = 2'b10;
  localparam logic [1:0] AXI_DECERR = 2'b11;

endpackage
