// ============================================================================
// dma_channel.sv - one DMA channel: config registers, context, sensor FIFO
//
// A channel moves LEN words from SRC (memory or sensor stream) to DST (memory).
// The shared engine moves one burst at a time; after each burst it calls
// back with upd/upd_beats/upd_err and this module advances its context.
// ============================================================================
module dma_channel
  import dma_pkg::*;
(
  input  logic                clk,
  input  logic                rst_n,
  input  logic                gl_en,        // global DMA enable
  // register access (word offset inside the channel window)
  input  logic                reg_wr,
  input  logic [3:0]          reg_waddr,
  input  logic [31:0]         reg_wdata,
  input  logic [3:0]          reg_raddr,
  output logic [31:0]         reg_rdata,
  // sensor stream input
  input  logic                s_valid,
  input  logic [DATA_W-1:0]   s_data,
  output logic                s_ready,
  // arbiter / engine side
  output logic                req,          // wants a burst
  output logic [1:0]          prio,
  output logic [4:0]          next_beats,   // size of the next burst (1..16)
  output logic [ADDR_W-1:0]   src_addr,
  output logic [ADDR_W-1:0]   dst_addr,
  output logic                src_stream,
  input  logic                inflight,     // engine is serving this channel
  input  logic                fifo_pop,
  output logic [DATA_W-1:0]   fifo_rdata,
  input  logic                upd,          // burst finished
  input  logic [4:0]          upd_beats,    // beats actually moved (0 on error)
  input  logic [2:0]          upd_err,
  output logic                irq,
  output logic                active_o
);

  // ---- configuration registers ------------------------------------------------
  logic              en;
  logic [1:0]        prio_r;
  logic [3:0]        blen;                   // beats-1
  logic [ADDR_W-1:0] src_base, dst_base;
  logic [LEN_W-1:0]  len;
  logic [1:0]        int_en, int_stat;

  // ---- run-time context -----------------------------------------------------------
  logic              active;
  logic [ADDR_W-1:0] cur_src, cur_dst;
  logic [LEN_W-1:0]  remaining;
  logic [2:0]        err_code;
  logic [31:0]       xferred;

  assign prio       = prio_r;
  assign src_addr   = cur_src;
  assign dst_addr   = cur_dst;
  assign active_o   = active;
  assign irq        = |(int_stat & int_en);

  // ---- START decode -------------------------------------------------------------
  wire wr_ctrl   = reg_wr && (reg_waddr == CH_CTRL);
  wire start_w   = wr_ctrl && reg_wdata[1];
  wire new_en    = reg_wdata[0];
  wire new_strm  = reg_wdata[2];
  wire cfg_bad   = !new_en || (len == '0) ||
                   (dst_base[1:0] != 2'b00) ||
                   (!new_strm && src_base[1:0] != 2'b00);
  wire start_ok  = start_w && !active && !cfg_bad;
  wire start_bad = start_w && !active &&  cfg_bad;

  // ---- sensor stream FIFO -------------------------------------------------------
  // a full FIFO back-pressures the sensor (s_ready low), so no word is ever lost
  logic                       fifo_full;
  logic [$clog2(FIFO_DEPTH):0] fifo_cnt;

  assign s_ready = active && src_stream && !fifo_full;

  dma_sfifo #(.W(DATA_W), .DEPTH(FIFO_DEPTH)) u_fifo (
    .clk(clk), .rst_n(rst_n), .flush(start_ok),
    .wr_en(s_valid && s_ready), .wdata(s_data), .full(fifo_full),
    .rd_en(fifo_pop), .rdata(fifo_rdata), .count(fifo_cnt)
  );

  // ---- next burst sizing: burst cfg, remaining words, 4KB boundary --------------------
  // All quantities are saturated to 6 bits (max useful value 32), so the min() is small and fast.
  logic [5:0] b_c, rem6, rd6, rs6, m_c;
  logic [9:0] wd, ws;
  always_comb begin
    wd   = cur_dst[11:2];
    ws   = cur_src[11:2];
    b_c  = 6'(blen) + 6'd1;
    rem6 = (|remaining[LEN_W-1:5]) ? 6'd32 : {1'b0, remaining[4:0]};
    rd6  = (wd[9:5] == 5'h1F && wd[4:0] != 5'd0) ? {1'b0, 5'd0 - wd[4:0]} : 6'd32;   // words left in 4KB page
    rs6  = (ws[9:5] == 5'h1F && ws[4:0] != 5'd0) ? {1'b0, 5'd0 - ws[4:0]} : 6'd32;
    if (src_stream) rs6 = 6'd32;
    m_c  = b_c;
    if (rem6 < m_c) m_c = rem6;
    if (rd6  < m_c) m_c = rd6;
    if (rs6  < m_c) m_c = rs6;
  end

  // request is registered (timing); the engine waits one cycle after each burst so that
  // this register always reflects the updated context.  Level qualifiers stay combinational.
  logic       req_q;
  logic [4:0] nb_q;
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      req_q <= 1'b0;
      nb_q  <= 5'd1;
    end else begin
      nb_q  <= m_c[4:0];
      req_q <= active && (remaining != '0) && (!src_stream || (6'(fifo_cnt) >= m_c));
    end
  end
  assign next_beats = nb_q;
  assign req = req_q && gl_en && en && active;

  // ---- sequential state --------------------------------------------------------------
  logic [1:0] int_set;
  logic       done_now;
  assign done_now = upd && (upd_err == ERR_NONE) && (remaining == LEN_W'(upd_beats));
  assign int_set  = {(upd && upd_err != ERR_NONE) || start_bad,   // ERR
                     done_now};                                     // DONE

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      en <= 1'b0; src_stream <= 1'b0; prio_r <= '0; blen <= '0;
      src_base <= '0; dst_base <= '0; len <= '0; int_en <= '0; int_stat <= '0;
      active <= 1'b0;
      cur_src <= '0; cur_dst <= '0; remaining <= '0;
      err_code <= ERR_NONE; xferred <= '0;
    end else begin
      // ---------------- register writes
      if (reg_wr) begin
        case (reg_waddr)
          CH_CTRL: begin
            en <= reg_wdata[0]; src_stream <= reg_wdata[2];
            prio_r <= reg_wdata[5:4]; blen <= reg_wdata[11:8];
          end
          CH_SRC:    src_base <= reg_wdata;
          CH_DST:    dst_base <= reg_wdata;
          CH_LEN:    len      <= reg_wdata[LEN_W-1:0];
          CH_INT_EN: int_en   <= reg_wdata[1:0];
          default: ;
        endcase
      end

      // ---------------- interrupt status: set wins over write-1-clear
      int_stat <= (int_stat & ~((reg_wr && reg_waddr == CH_INT_STAT) ? reg_wdata[1:0] : 2'b00))
                  | int_set;

      // ---------------- start of a transfer
      if (start_ok) begin
        active    <= 1'b1;
        cur_src   <= src_base;
        cur_dst   <= dst_base;
        remaining <= len;
        err_code  <= ERR_NONE;
        xferred   <= '0;
      end else if (start_bad) begin
        err_code  <= ERR_CFG;
      end

      // ---------------- burst completion from the engine
      if (upd) begin
        cur_src   <= cur_src + (ADDR_W'(upd_beats) << 2);
        cur_dst   <= cur_dst + (ADDR_W'(upd_beats) << 2);
        remaining <= remaining - LEN_W'(upd_beats);
        xferred   <= xferred + 32'(upd_beats);
        if (upd_err != ERR_NONE) begin              // bus error: stop this channel only
          active   <= 1'b0;
          err_code <= upd_err;
        end else if (remaining == LEN_W'(upd_beats)) begin
          active   <= 1'b0;                         // last burst done
        end
      end
    end
  end

  // ---- register read mux --------------------------------------------------------------
  always_comb begin
    reg_rdata = '0;
    case (reg_raddr)
      CH_CTRL:     reg_rdata = {20'd0, blen, 2'b00, prio_r, 1'b0, src_stream, 1'b0, en};
      CH_SRC:      reg_rdata = src_base;
      CH_DST:      reg_rdata = dst_base;
      CH_LEN:      reg_rdata = 32'(len);
      CH_INT_EN:   reg_rdata = {30'd0, int_en};
      CH_INT_STAT: reg_rdata = {30'd0, int_stat};
      CH_STATUS:   reg_rdata = {16'd0, 2'd0, 6'(fifo_cnt), 3'd0, err_code, inflight, active};
      CH_REMAIN:   reg_rdata = 32'(remaining);
      CH_XFERRED:  reg_rdata = xferred;
      default:     reg_rdata = '0;
    endcase
  end

endmodule
