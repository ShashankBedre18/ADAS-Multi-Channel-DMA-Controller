// ============================================================================
// Virtual sequences: the real stimulus (one per verification scenario)
//
// ADAS channel map used by the directed scenarios
//   CH0  front camera   - sensor stream, prio 1, highest bandwidth
//   CH1  radar          - sensor stream, prio 3, latency critical
//   CH2  LiDAR          - sensor stream, prio 2
//   CH3  diagnostics    - memory-to-memory log copy, prio 0 (background)
// ============================================================================

class dma_vseq_base extends uvm_sequence;
  `uvm_object_utils(dma_vseq_base)
  `uvm_declare_p_sequencer(dma_vsqr)

  function new(string name = "dma_vseq_base"); super.new(name); endfunction

  // ---------------------------------------------------------------- helpers
  function bit [11:0] chreg(int ch, bit [3:0] w);
    return 12'(CH_BASE + ch * CH_STRIDE + w * 4);
  endfunction
  function bit [31:0] src_of(int c); return 32'h0001_0000 * (c + 1);          endfunction
  function bit [31:0] dst_of(int c); return 32'h0010_0000 + 32'h0001_0000 * c; endfunction

  task wr(bit [11:0] a, bit [31:0] d);
    apb_item it = apb_item::type_id::create("wr");
    start_item(it, -1, p_sequencer.apb_sqr);
    if (!it.randomize() with { write == 1; addr == a; data == d; }) `uvm_fatal("RND", "apb wr")
    finish_item(it, -1);
  endtask

  task rd(bit [11:0] a, output bit [31:0] d, output bit err);
    apb_item it = apb_item::type_id::create("rd");
    start_item(it, -1, p_sequencer.apb_sqr);
    if (!it.randomize() with { write == 0; addr == a; }) `uvm_fatal("RND", "apb rd")
    finish_item(it, -1);
    d   = it.rdata;
    err = it.slverr;
  endtask

  task rd32(bit [11:0] a, output bit [31:0] d);
    bit e;
    rd(a, d, e);
  endtask

  function void expect32(string what, bit [31:0] got, bit [31:0] exp);
    if (got !== exp) `uvm_error("CHK", $sformatf("%s: got 0x%08h expected 0x%08h", what, got, exp))
  endfunction
  function void check(bit cond, string msg);
    if (!cond) `uvm_error("CHK", msg)
  endfunction

  task clk_wait(int n);
    repeat (n) @(posedge p_sequencer.dbg.clk);
  endtask

  // program a channel; start=1 launches it in the same CTRL write
  task cfg_ch(int ch, bit [31:0] src, bit [31:0] dst, int len, bit strm = 0,
              bit [1:0] prio = 0, bit [3:0] blen = 15, bit [1:0] ien = 2'b11, bit start = 1);
    wr(chreg(ch, CH_SRC),    src);
    wr(chreg(ch, CH_DST),    dst);
    wr(chreg(ch, CH_LEN),    len);
    wr(chreg(ch, CH_INT_EN), ien);
    wr(chreg(ch, CH_CTRL),   {20'd0, blen, 2'b00, prio, 1'b0, strm, start, 1'b1});
  endtask

  // wait for the channel irq line; returns timeout=1 if it never rose
  task wait_irq(int ch, int max_cycles, output bit tmo);
    int n = 0;
    while (!p_sequencer.dbg.irq_ch[ch] && n < max_cycles) begin
      @(posedge p_sequencer.dbg.clk);
      n++;
    end
    tmo = !p_sequencer.dbg.irq_ch[ch];
  endtask

  // read INT_STAT and clear what was read
  task ack_irq(int ch, output bit [31:0] stat);
    rd32(chreg(ch, CH_INT_STAT), stat);
    if (stat[1:0] != 0) wr(chreg(ch, CH_INT_STAT), {30'd0, stat[1:0]});
  endtask

  // wait until DONE or ERR is reported; returns the accumulated interrupt bits
  task wait_done(int ch, int max_cycles, output bit [31:0] acc);
    bit        tmo;
    bit [31:0] st;
    int        spent = 0;
    acc = 0;
    forever begin
      wait_irq(ch, max_cycles - spent, tmo);
      if (tmo) begin
        `uvm_error("TIMEOUT", $sformatf("CH%0d no completion irq within %0d cycles", ch, max_cycles))
        return;
      end
      ack_irq(ch, st);
      acc |= st;
      if (acc[INT_DONE] || acc[INT_ERR]) return;
      spent += 5;
      if (spent >= max_cycles) begin
        `uvm_error("TIMEOUT", $sformatf("CH%0d completion not reached", ch))
        return;
      end
    end
  endtask

  task send_stream(int ch, int n, int gap = 0, int sd = 0);
    strm_item it = strm_item::type_id::create("s");
    start_item(it, -1, p_sequencer.strm_sqr[ch]);
    if (!it.randomize() with { nwords == n; gap_pct == gap; start_delay == sd; }) `uvm_fatal("RND", "strm")
    finish_item(it, -1);
  endtask
  task send_stream_bg(int ch, int n, int gap = 0, int sd = 0);
    fork
      send_stream(ch, n, gap, sd);
    join_none
  endtask

  task gl_enable(bit en);
    wr(REG_GCTRL, {30'd0, 1'b0, en});
  endtask

  function bit [31:0] status_err(bit [31:0] st); return st[4:2]; endfunction
endclass

// ============================================================================
// 1. register interface
// ============================================================================
class dma_regs_vseq extends dma_vseq_base;
  `uvm_object_utils(dma_regs_vseq)
  function new(string name = "dma_regs_vseq"); super.new(name); endfunction
  task body();
    bit [31:0] v; bit e;
    // reset values
    rd32(REG_VERSION, v); expect32("VERSION", v, VERSION);
    rd32(REG_GCTRL,   v); expect32("GCTRL reset", v, 0);
    rd32(REG_GSTAT,   v); expect32("GSTAT reset", v, 0);
    for (int c = 0; c < N_CH; c++) begin
      rd32(chreg(c, CH_CTRL),   v); expect32($sformatf("CH%0d CTRL reset", c), v, 0);
      rd32(chreg(c, CH_INT_EN), v); expect32($sformatf("CH%0d INT_EN reset", c), v, 0);
      rd32(chreg(c, CH_STATUS), v); expect32($sformatf("CH%0d STATUS reset", c), v, 0);
    end
    // read/write registers
    for (int c = 0; c < N_CH; c++) begin
      wr(chreg(c, CH_SRC), 32'hDEAD_BEE0 + c);        rd32(chreg(c, CH_SRC), v); expect32("SRC rw", v, 32'hDEAD_BEE0 + c);
      wr(chreg(c, CH_DST), 32'hC0DE_0000 + 4 * c);    rd32(chreg(c, CH_DST), v); expect32("DST rw", v, 32'hC0DE_0000 + 4 * c);
      wr(chreg(c, CH_LEN), 32'hFFFF_FFFF);            rd32(chreg(c, CH_LEN), v); expect32("LEN 24-bit", v, 32'h00FF_FFFF);
      wr(chreg(c, CH_INT_EN), 32'hFFFF_FFFF);         rd32(chreg(c, CH_INT_EN), v); expect32("INT_EN 2-bit", v, 32'h3);
      wr(chreg(c, CH_INT_EN), 0);
      wr(chreg(c, CH_CTRL), 32'h0000_0A35);           rd32(chreg(c, CH_CTRL), v); expect32("CTRL rw", v, 32'h0000_0A35);
      wr(chreg(c, CH_CTRL), 0);
    end
    wr(REG_GCTRL, 32'hFFFF_FFFF);  rd32(REG_GCTRL, v);  expect32("GCTRL 1-bit", v, 1);
    wr(REG_GCTRL, 0);
    // read-only registers ignore writes
    wr(REG_VERSION, 32'h1);        rd32(REG_VERSION, v); expect32("VERSION is RO", v, VERSION);
    wr(chreg(0, CH_XFERRED), 32'h55); rd32(chreg(0, CH_XFERRED), v); expect32("XFERRED is RO", v, 0);
    // unmapped addresses give PSLVERR
    rd(12'h010, v, e); check(e, "global hole 0x010 must PSLVERR");
    rd(12'h0F0, v, e); check(e, "hole 0x0F0 must PSLVERR");
    rd(12'h300, v, e); check(e, "0x300 must PSLVERR");
    rd(12'h124, v, e); check(e, "channel word 9 must PSLVERR");
    rd(12'h200, v, e); check(e, "channel 4 window must PSLVERR");
    rd(12'h100, v, e); check(!e, "channel 0 CTRL must not PSLVERR");
    wr(12'h2F0, 32'h1);
    // interrupt: illegal start (len == 0) -> ERR_CFG, write-1-to-clear
    wr(chreg(0, CH_INT_EN), 2'b10);
    wr(chreg(0, CH_LEN), 0);
    wr(chreg(0, CH_CTRL), 32'h0000_0003);              // en + start
    clk_wait(3);
    rd32(chreg(0, CH_INT_STAT), v); expect32("INT_STAT after bad start", v, 2);
    rd32(chreg(0, CH_STATUS), v);   expect32("STATUS err code", status_err(v), ERR_CFG);
    check(p_sequencer.dbg.irq_ch[0] === 1'b1, "irq_ch[0] must be asserted");
    rd32(REG_IRQ_SUM, v); expect32("IRQ_SUM", v, 1);
    wr(chreg(0, CH_INT_STAT), 32'h1);                  // wrong bit: must not clear
    rd32(chreg(0, CH_INT_STAT), v); expect32("W1C wrong bit", v, 2);
    wr(chreg(0, CH_INT_STAT), 32'h2);
    rd32(chreg(0, CH_INT_STAT), v); expect32("W1C clear", v, 0);
    check(p_sequencer.dbg.irq_ch[0] === 1'b0, "irq_ch[0] must deassert");
    wr(chreg(0, CH_CTRL), 0);
  endtask
endclass

// ============================================================================
// 2. smoke
// ============================================================================
class dma_smoke_vseq extends dma_vseq_base;
  `uvm_object_utils(dma_smoke_vseq)
  function new(string name = "dma_smoke_vseq"); super.new(name); endfunction
  task body();
    bit [31:0] st, v;
    gl_enable(1);
    p_sequencer.mem.fill_random(src_of(0), 64);
    cfg_ch(0, src_of(0), dst_of(0), 64, 0, 1, 15);
    wait_done(0, 5000, st);
    check(st[INT_DONE] && !st[INT_ERR], "smoke: expected DONE only");
    rd32(chreg(0, CH_XFERRED), v); expect32("XFERRED", v, 64);
    rd32(chreg(0, CH_REMAIN), v);  expect32("REMAIN", v, 0);
    rd32(chreg(0, CH_STATUS), v);  expect32("STATUS idle", v[1:0], 0);
    // sensor stream channel too
    cfg_ch(1, 0, dst_of(1), 32, 1, 3, 7);
    send_stream(1, 32, 0, 2);
    wait_done(1, 5000, st);
    check(st[INT_DONE] && !st[INT_ERR], "smoke: stream expected DONE only");
  endtask
endclass

// ============================================================================
// 3. ADAS sensor fusion: all channels busy, mixed priorities
// ============================================================================
class dma_sensor_fusion_vseq extends dma_vseq_base;
  `uvm_object_utils(dma_sensor_fusion_vseq)
  function new(string name = "dma_sensor_fusion_vseq"); super.new(name); endfunction

  int unsigned len [N_CH] = '{4608, 256, 1024, 512};     // camera frame > 4096 words
  int unsigned done_cycle[N_CH];

  task body();
    bit [31:0] st [N_CH];
    bit [31:0] v;
    p_sequencer.mem.fill_random(src_of(3), len[3]);
    gl_enable(0);                                       // configure everything, then release together
    cfg_ch(0, 0,          dst_of(0), len[0], 1, 1, 15);   // camera
    cfg_ch(1, 0,          dst_of(1), len[1], 1, 3, 3);    // radar (critical)
    cfg_ch(2, 0,          dst_of(2), len[2], 1, 2, 7);    // lidar
    cfg_ch(3, src_of(3),  dst_of(3), len[3], 0, 0, 15);   // diagnostics log copy
    send_stream_bg(0, len[0], 0);
    send_stream_bg(1, len[1], 30);
    send_stream_bg(2, len[2], 10);
    gl_enable(1);
    // note completion order / latency
    begin
      bit seen[N_CH];
      int cyc_n = 0, n_seen = 0;
      while (n_seen < N_CH && cyc_n < 100000) begin
        @(posedge p_sequencer.dbg.clk);
        cyc_n++;
        for (int c = 0; c < N_CH; c++)
          if (!seen[c] && p_sequencer.dbg.irq_ch[c]) begin
            seen[c] = 1; n_seen++; done_cycle[c] = cyc_n;
          end
      end
      check(n_seen == N_CH, "sensor fusion: not all channels completed");
    end
    for (int c = 0; c < N_CH; c++) begin
      string nm[N_CH] = '{"camera", "radar", "lidar", "diagnostics"};
      wait_done(c, 20000, st[c]);
      check(st[c][INT_DONE] && !st[c][INT_ERR], $sformatf("CH%0d (%s) must finish cleanly", c, nm[c]));
      rd32(chreg(c, CH_XFERRED), v);
      expect32($sformatf("CH%0d XFERRED", c), v, len[c]);
      `uvm_info("FUSION", $sformatf("CH%0d %-11s %4d words done after %0d cycles",
                c, nm[c], len[c], done_cycle[c]), UVM_LOW)
    end
    check(done_cycle[1] < done_cycle[0] && done_cycle[1] < done_cycle[2] && done_cycle[1] < done_cycle[3],
          "radar (highest priority) must finish first");
  endtask
endclass

// ============================================================================
// 4. burst length sweep, with start addresses chosen close to 4KB boundaries
// ============================================================================
class dma_burst_sweep_vseq extends dma_vseq_base;
  `uvm_object_utils(dma_burst_sweep_vseq)
  function new(string name = "dma_burst_sweep_vseq"); super.new(name); endfunction
  task body();
    bit [31:0] st, v, s, d;
    int len;
    gl_enable(1);
    for (int blen = 0; blen < 16; blen++) begin
      for (int pass = 0; pass < 3; pass++) begin
        int c = (blen + pass) % N_CH;
        len = $urandom_range(1, 70);
        s   = src_of(c) + 4096 - 4 * $urandom_range(0, 24);       // may straddle a 4KB page
        d   = dst_of(c) + 4096 - 4 * $urandom_range(1, 24);
        if (pass == 0) begin s = src_of(c) + 4 * $urandom_range(0, 8); d = dst_of(c) + 4 * $urandom_range(0, 8); end
        p_sequencer.mem.fill_random(s, len);
        cfg_ch(c, s, d, len, 0, $urandom_range(0, 3), blen);
        wait_done(c, 20000, st);
        check(st[INT_DONE] && !st[INT_ERR], $sformatf("sweep blen=%0d len=%0d src=0x%08h dst=0x%08h", blen, len, s, d));
        rd32(chreg(c, CH_XFERRED), v); expect32("sweep XFERRED", v, len);
      end
    end
  endtask
endclass

// ============================================================================
// 5. priority order and round-robin between equal priorities
// ============================================================================
class dma_priority_vseq extends dma_vseq_base;
  `uvm_object_utils(dma_priority_vseq)
  function new(string name = "dma_priority_vseq"); super.new(name); endfunction

  // run n channels at once, return the order in which their irq lines rose
  int grants[$];                        // channel granted at every arbitration of the last group

  task run_group(int chans[$], int len[$], bit [1:0] prios[$], ref int order[$]);
    bit seen[N_CH];
    bit [31:0] st;
    int n = 0, cyc_n = 0;
    order.delete();
    grants.delete();
    gl_enable(0);
    foreach (chans[i]) begin
      p_sequencer.mem.fill_random(src_of(chans[i]), len[i]);
      cfg_ch(chans[i], src_of(chans[i]), dst_of(chans[i]), len[i], 0, prios[i], 15);
    end
    gl_enable(1);
    while (n < chans.size() && cyc_n < 50000) begin
      @(posedge p_sequencer.dbg.clk);
      cyc_n++;
      if (p_sequencer.dbg.grant_fire) grants.push_back(p_sequencer.dbg.gnt_idx);
      foreach (chans[i])
        if (!seen[chans[i]] && p_sequencer.dbg.irq_ch[chans[i]]) begin
          seen[chans[i]] = 1; n++; order.push_back(chans[i]);
        end
    end
    foreach (chans[i]) begin wait_done(chans[i], 2000, st); end
    gl_enable(0);
    clk_wait(10);
  endtask

  task body();
    int order[$];
    int e3210[$] = '{3, 2, 1, 0};
    int e30[$]   = '{3, 0};
    // strict priority: all four equal size, highest priority drains first
    run_group('{0, 1, 2, 3}, '{256, 256, 256, 256}, '{0, 1, 2, 3}, order);
    check(order == e3210, $sformatf("strict priority order wrong: %p", order));
    // a long high-priority job is served before a short low-priority one
    run_group('{0, 3}, '{64, 512}, '{0, 3}, order);
    check(order == e30, $sformatf("high priority ch3 should finish first: %p", order));
    // same priority: round-robin, every 4 consecutive grants serve all 4 channels
    run_group('{0, 1, 2, 3}, '{64, 64, 64, 64}, '{2, 2, 2, 2}, order);
    check(order.size() == 4, "equal priority group must complete");
    check(grants.size() == 16, $sformatf("expected 16 bursts, saw %0d", grants.size()));
    for (int g = 0; g + 4 <= grants.size(); g += 4) begin
      bit [N_CH-1:0] seen_w = 0;
      for (int k = 0; k < 4; k++) seen_w[grants[g + k]] = 1;
      check(seen_w == 4'hF, $sformatf("round-robin: grants %0d..%0d do not cover all channels", g, g + 3));
    end
    `uvm_info("PRIO", $sformatf("equal-priority grant sequence: %p", grants), UVM_LOW)
  endtask
endclass

// ============================================================================
// 6. error injection and recovery
// ============================================================================
class dma_error_vseq extends dma_vseq_base;
  `uvm_object_utils(dma_error_vseq)
  function new(string name = "dma_error_vseq"); super.new(name); endfunction
  task body();
    bit [31:0] st[N_CH], v;
    gl_enable(1);
    p_sequencer.scfg.add_error(src_of(0), src_of(0) + 32'h1000, AXI_SLVERR, 1, 0);   // CH0: read SLVERR
    p_sequencer.scfg.add_error(dst_of(1), dst_of(1) + 32'h1000, AXI_DECERR, 0, 1);   // CH1: write DECERR
    p_sequencer.scfg.add_error(dst_of(2), dst_of(2) + 32'h1000, AXI_SLVERR, 0, 1);   // CH2: sensor write SLVERR
    p_sequencer.mem.fill_random(src_of(1), 64);
    p_sequencer.mem.fill_random(src_of(3), 128);
    gl_enable(0);
    cfg_ch(0, src_of(0), dst_of(0), 64, 0, 1, 15);
    cfg_ch(1, src_of(1), dst_of(1), 64, 0, 1, 15);
    cfg_ch(2, 0,         dst_of(2), 64, 1, 1, 15);
    cfg_ch(3, src_of(3), dst_of(3), 128, 0, 0, 15);
    send_stream_bg(2, 16, 0);                          // one burst worth, then the channel dies
    gl_enable(1);
    for (int c = 0; c < N_CH; c++) wait_done(c, 20000, st[c]);
    check(st[0][INT_ERR] && !st[0][INT_DONE], "CH0 should report ERR only");
    check(st[1][INT_ERR] && !st[1][INT_DONE], "CH1 should report ERR only");
    check(st[2][INT_ERR] && !st[2][INT_DONE], "CH2 should report ERR only");
    check(st[3][INT_DONE] && !st[3][INT_ERR], "CH3 must be unaffected by the others' errors");
    rd32(chreg(0, CH_STATUS), v); expect32("CH0 err code", status_err(v), ERR_SLVERR); expect32("CH0 inactive", v[0], 0);
    rd32(chreg(1, CH_STATUS), v); expect32("CH1 err code", status_err(v), ERR_DECERR); expect32("CH1 inactive", v[0], 0);
    rd32(chreg(2, CH_STATUS), v); expect32("CH2 err code", status_err(v), ERR_SLVERR); expect32("CH2 inactive", v[0], 0);
    rd32(chreg(3, CH_STATUS), v); expect32("CH3 err code", status_err(v), ERR_NONE);
    // recovery: remove the faults and re-run the failed channels
    p_sequencer.scfg.clear_errors();
    p_sequencer.mem.fill_random(src_of(0), 64);
    cfg_ch(0, src_of(0), dst_of(0), 64, 0, 1, 15);
    cfg_ch(1, src_of(1), dst_of(1), 64, 0, 1, 15);
    cfg_ch(2, 0,         dst_of(2), 64, 1, 1, 15);
    send_stream_bg(2, 64, 5);
    for (int c = 0; c < 3; c++) begin
      wait_done(c, 20000, st[c]);
      check(st[c][INT_DONE] && !st[c][INT_ERR], $sformatf("CH%0d must recover after the fault is removed", c));
      rd32(chreg(c, CH_XFERRED), v); expect32("recovered XFERRED", v, 64);
    end
    // error matrix: every channel against every AXI error response, on read and on write
    for (int c = 0; c < N_CH; c++) begin
      for (int r = 0; r < 4; r++) begin
        bit [1:0] resp   = (r[0]) ? AXI_DECERR : AXI_SLVERR;
        bit       on_wr  = r[1];
        bit [2:0] expect_code = (r[0]) ? ERR_DECERR : ERR_SLVERR;
        p_sequencer.scfg.clear_errors();
        p_sequencer.mem.fill_random(src_of(c), 24);
        if (on_wr) p_sequencer.scfg.add_error(dst_of(c), dst_of(c) + 32'h1000, resp, 0, 1);
        else       p_sequencer.scfg.add_error(src_of(c), src_of(c) + 32'h1000, resp, 1, 0);
        cfg_ch(c, src_of(c), dst_of(c), 24, 0, c, 7);
        wait_done(c, 5000, st[c]);
        check(st[c][INT_ERR] && !st[c][INT_DONE], $sformatf("matrix CH%0d resp=%0d wr=%0d must report ERR", c, resp, on_wr));
        rd32(chreg(c, CH_STATUS), v);
        expect32($sformatf("matrix CH%0d err code", c), status_err(v), expect_code);
      end
    end
    p_sequencer.scfg.clear_errors();
  endtask
endclass

// ============================================================================
// 7. illegal configuration handling
// ============================================================================
class dma_cfg_err_vseq extends dma_vseq_base;
  `uvm_object_utils(dma_cfg_err_vseq)
  function new(string name = "dma_cfg_err_vseq"); super.new(name); endfunction
  task body();
    bit [31:0] v, st;
    int unsigned bursts_before;
    gl_enable(1);
    bursts_before = p_sequencer.axi_mon.n_rd + p_sequencer.axi_mon.n_wr;
    cfg_ch(0, src_of(0), dst_of(0), 0, 0, 0, 15);                       // zero length
    cfg_ch(1, src_of(1), dst_of(1) + 3, 8, 0, 0, 15);                   // unaligned destination
    cfg_ch(2, src_of(2) + 2, dst_of(2), 8, 0, 0, 15);                   // unaligned source
    wr(chreg(3, CH_SRC), src_of(3)); wr(chreg(3, CH_DST), dst_of(3));
    wr(chreg(3, CH_LEN), 8);         wr(chreg(3, CH_INT_EN), 2'b11);
    wr(chreg(3, CH_CTRL), 32'h0000_0F02);                               // START without EN
    clk_wait(20);
    for (int c = 0; c < N_CH; c++) begin
      rd32(chreg(c, CH_INT_STAT), v); expect32($sformatf("CH%0d INT_STAT", c), v, 2);
      rd32(chreg(c, CH_STATUS), v);   expect32($sformatf("CH%0d err code", c), status_err(v), ERR_CFG);
      expect32($sformatf("CH%0d must stay idle", c), v[0], 0);
      check(p_sequencer.dbg.irq_ch[c] === 1'b1, "cfg error must raise the channel irq");
      ack_irq(c, st);
    end
    clk_wait(50);
    check(p_sequencer.axi_mon.n_rd + p_sequencer.axi_mon.n_wr == bursts_before, "illegal config produced bus traffic");
    // a following legal start on the same channel works and clears the error code
    p_sequencer.mem.fill_random(src_of(0), 16);
    cfg_ch(0, src_of(0), dst_of(0), 16, 0, 0, 15);
    wait_done(0, 5000, st);
    check(st[INT_DONE] && !st[INT_ERR], "legal start after cfg error must succeed");
    rd32(chreg(0, CH_STATUS), v); expect32("err code cleared by new start", status_err(v), ERR_NONE);
    // START while the channel is busy is ignored
    p_sequencer.mem.fill_random(src_of(1), 256);
    cfg_ch(1, src_of(1), dst_of(1), 256, 0, 0, 15);
    clk_wait(15);
    wr(chreg(1, CH_CTRL), {20'd0, 4'd15, 2'b00, 2'd0, 1'b0, 1'b0, 1'b1, 1'b1});
    wait_done(1, 10000, st);
    check(st[INT_DONE] && !st[INT_ERR], "busy channel: second START must be ignored");
    rd32(chreg(1, CH_XFERRED), v); expect32("busy channel XFERRED", v, 256);
  endtask
endclass

// ============================================================================
// 9. slow memory: sensors outrun the bus, FIFOs fill, nothing is lost
// ============================================================================
class dma_backpressure_vseq extends dma_vseq_base;
  `uvm_object_utils(dma_backpressure_vseq)
  function new(string name = "dma_backpressure_vseq"); super.new(name); endfunction
  task body();
    bit [31:0] st[3], v;
    int  full_cycles = 0;
    bit  done = 0;
    p_sequencer.scfg.set_slow();
    gl_enable(0);
    for (int c = 0; c < 3; c++) cfg_ch(c, 0, dst_of(c), 512, 1, c, 15);
    for (int c = 0; c < 3; c++) send_stream_bg(c, 512, 0);
    gl_enable(1);
    fork                                   // count cycles in which a sensor FIFO was full (sensor held off)
      while (!done) begin
        @(posedge p_sequencer.dbg.clk);
        for (int c = 0; c < 3; c++)
          if (p_sequencer.dbg.fifo_cnt[c] == FIFO_DEPTH) full_cycles++;
      end
    join_none
    for (int c = 0; c < 3; c++) begin
      wait_done(c, 400000, st[c]);
      check(st[c][INT_DONE] && !st[c][INT_ERR], $sformatf("CH%0d must finish despite slow memory", c));
      rd32(chreg(c, CH_XFERRED), v); expect32("XFERRED", v, 512);
    end
    done = 1;
    check(full_cycles > 0, "slow memory must fill a sensor FIFO (back-pressure)");
    `uvm_info("BACKPRESSURE", $sformatf("cycles with a full sensor FIFO: %0d (no data lost)", full_cycles), UVM_LOW)
    p_sequencer.scfg.set_fast();
  endtask
endclass

// ============================================================================
// 12. constrained random regression
// ============================================================================
class dma_random_vseq extends dma_vseq_base;
  `uvm_object_utils(dma_random_vseq)
  int unsigned iterations = 25;
  function new(string name = "dma_random_vseq"); super.new(name); endfunction

  task body();
    bit [31:0] st, v;
    int  it_plus;
    if ($value$plusargs("ITER=%d", it_plus)) iterations = it_plus;
    for (int it = 0; it < iterations; it++) begin
      bit        active_c[N_CH], strm_c[N_CH];
      int        len_c[N_CH], gap_c[N_CH];
      int        n_act = 0;
      bit [31:0] s, d;
      // slave and arbiter personality for this iteration
      if ($urandom_range(0, 3) == 0) p_sequencer.scfg.set_fast(); else p_sequencer.scfg.set_random();
      gl_enable(0);
      for (int c = 0; c < N_CH; c++) begin
        active_c[c] = ($urandom_range(0, 9) < 8);
        if (c == 0 && n_act == 0 && !active_c[0]) active_c[0] = 1;
        if (!active_c[c]) continue;
        n_act++;
        strm_c[c] = ($urandom_range(0, 9) < 6);
        len_c[c]  = ($urandom_range(0, 4) == 0) ? $urandom_range(1, 4) : $urandom_range(1, 300);
        gap_c[c]  = $urandom_range(0, 60);
        s = src_of(c) + 4 * $urandom_range(0, 4000);
        d = dst_of(c) + 4 * $urandom_range(0, 4000);
        if ($urandom_range(0, 2) == 0) begin   // aim at a 4KB boundary
          s = src_of(c) + 4096 - 4 * $urandom_range(0, 15);
          d = dst_of(c) + 4096 - 4 * $urandom_range(1, 15);
        end
        if (!strm_c[c]) p_sequencer.mem.fill_random(s, len_c[c]);
        cfg_ch(c, s, d, len_c[c], strm_c[c], $urandom_range(0, 3), $urandom_range(0, 15));
        if (strm_c[c]) send_stream_bg(c, len_c[c], gap_c[c], $urandom_range(0, 10));
      end
      gl_enable(1);
      for (int c = 0; c < N_CH; c++) begin
        if (!active_c[c]) continue;
        wait_done(c, 200000, st);
        check(st[INT_DONE] && !st[INT_ERR], $sformatf("iter %0d CH%0d did not finish cleanly (stat=%0d)", it, c, st));
        rd32(chreg(c, CH_XFERRED), v); expect32($sformatf("iter %0d CH%0d XFERRED", it, c), v, len_c[c]);
      end
      gl_enable(0);
      clk_wait(5);
    end
    `uvm_info("RANDOM", $sformatf("%0d random iterations completed", iterations), UVM_LOW)
  endtask
endclass
