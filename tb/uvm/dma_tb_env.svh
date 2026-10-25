// ============================================================================
// Scoreboard, functional coverage, environment, virtual sequencer
// ============================================================================
`uvm_analysis_imp_decl(_apb)
`uvm_analysis_imp_decl(_axi)
`uvm_analysis_imp_decl(_strm)
`uvm_analysis_imp_decl(_arb)

// ---------------------------------------------------------------------------
// per-channel reference model state
// ---------------------------------------------------------------------------
class ch_model;
  // programmed register shadows
  bit          en, strm;
  bit [1:0]    prio;
  bit [3:0]    blen;
  bit [31:0]   src, dst;
  int unsigned len;
  // snapshot taken at START
  bit          started, active, err_seen, cfg_err;
  bit          strm_run;
  int unsigned blen_run, len_run;
  bit [31:0]   src_run, dst_run;
  longint unsigned wk, rk;          // words written / read so far in this run
  bit [31:0]   snap[];              // expected data (memory-to-memory)
  bit [31:0]   sdata[$];            // words accepted from the sensor
  int unsigned total_wr;            // all words ever written for this channel
endclass

// ---------------------------------------------------------------------------
class dma_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(dma_scoreboard)

  uvm_analysis_imp_apb  #(apb_item,      dma_scoreboard) apb_imp;
  uvm_analysis_imp_axi  #(axi_item,      dma_scoreboard) axi_imp;
  uvm_analysis_imp_strm #(strm_mon_item, dma_scoreboard) strm_imp;
  uvm_analysis_imp_arb  #(arb_item,      dma_scoreboard) arb_imp;

  axi_mem      mem;
  ch_model     m[N_CH];
  int unsigned n_wr_bursts, n_rd_bursts, n_wr_beats, n_apb, n_arb;
  int unsigned n_checks, n_stray;
  int unsigned arb_win[N_CH];

  function new(string name, uvm_component parent);
    super.new(name, parent);
    apb_imp  = new("apb_imp", this);
    axi_imp  = new("axi_imp", this);
    strm_imp = new("strm_imp", this);
    arb_imp  = new("arb_imp", this);
    foreach (m[i]) m[i] = new();
  endfunction

  function void build_phase(uvm_phase phase);
    if (!uvm_config_db#(axi_mem)::get(this, "", "mem", mem)) `uvm_fatal("NOCFG", "mem")
  endfunction

  // ---------------- APB: track programming, START, status reads
  function void write_apb(apb_item t);
    int c, off;
    n_apb++;
    if (t.addr < CH_BASE || t.addr >= CH_BASE + N_CH * CH_STRIDE) return;
    c   = (t.addr - CH_BASE) / CH_STRIDE;
    off = ((t.addr - CH_BASE) % CH_STRIDE) >> 2;
    if (t.slverr) return;
    if (t.write) begin
      case (off)
        CH_CTRL: begin
          m[c].en = t.data[0]; m[c].strm = t.data[2];
          m[c].prio = t.data[5:4]; m[c].blen = t.data[11:8];
          if (t.data[1]) model_start(c);
        end
        CH_SRC: m[c].src = t.data;
        CH_DST: m[c].dst = t.data;
        CH_LEN: m[c].len = t.data[23:0];
        default: ;
      endcase
    end else begin
      if (off == CH_INT_STAT) check_int_stat(c, t.rdata[1:0]);
    end
  endfunction

  function void model_start(int c);
    bit bad;
    ch_model h = m[c];
    bad = !h.en || h.len == 0 || h.dst[1:0] != 0 || (!h.strm && h.src[1:0] != 0);
    if (h.active) return;                          // START while busy is ignored
    if (bad) begin h.cfg_err = 1; return; end
    h.started = 1; h.active = 1; h.err_seen = 0; h.cfg_err = 0;
    h.strm_run = h.strm; h.blen_run = h.blen + 1; h.len_run = h.len;
    h.src_run = h.src; h.dst_run = h.dst; h.wk = 0; h.rk = 0;
    h.sdata.delete();
    if (!h.strm) begin
      h.snap = new[h.len];
      for (int i = 0; i < h.len; i++) h.snap[i] = mem.read(h.src + 4*i);
    end
  endfunction

  function void check_int_stat(int c, bit [1:0] v);
    ch_model h = m[c];
    n_checks++;
    if (v[INT_DONE] && h.wk < h.len_run)
      `uvm_error("SCB", $sformatf("CH%0d reports DONE but only %0d of %0d words were written", c, h.wk, h.len_run))
    if (v[INT_ERR]) h.active = 0;
    if (v[INT_ERR] && !(h.err_seen || h.cfg_err))
      `uvm_error("SCB", $sformatf("CH%0d reports ERR but no error was injected / illegal config made", c))
  endfunction

  // ---------------- sensor words
  function void write_strm(strm_mon_item t);
    if (t.kind == STRM_WORD) m[t.ch].sdata.push_back(t.data);
  endfunction

  // ---------------- arbitration statistics
  function void write_arb(arb_item t);
    n_arb++;
    arb_win[t.winner]++;
  endfunction

  // expected burst size, mirrors the RTL sizing rules independently
  function int exp_beats(ch_model h, longint unsigned idx);
    longint unsigned pos = idx;
    bit [31:0] da = h.dst_run + 4*pos;
    bit [31:0] sa = h.src_run + 4*pos;
    int b = h.blen_run;
    int rem    = h.len_run - pos;
    int room_d = (4096 - da[11:0]) / 4;
    int room_s = (4096 - sa[11:0]) / 4;
    if (rem < b)    b = rem;
    if (room_d < b) b = room_d;
    if (!h.strm_run && room_s < b) b = room_s;
    return b;
  endfunction

  // ---------------- AXI bursts
  function void write_axi(axi_item t);
    if (t.is_write) check_write(t); else check_read(t);
  endfunction

  function int find_wr(bit [31:0] addr);
    for (int c = 0; c < N_CH; c++)
      if (m[c].started && addr >= m[c].dst_run && addr < m[c].dst_run + 4*m[c].len_run) return c;
    return -1;
  endfunction
  function int find_rd(bit [31:0] addr);
    for (int c = 0; c < N_CH; c++)
      if (m[c].started && !m[c].strm_run && addr >= m[c].src_run && addr < m[c].src_run + 4*m[c].len_run) return c;
    return -1;
  endfunction

  function void check_read(axi_item t);
    int c = find_rd(t.addr);
    ch_model h;
    n_rd_bursts++;
    if (c < 0) begin
      n_stray++;
      `uvm_error("SCB", $sformatf("stray read burst %s", t.convert2string()))
      return;
    end
    h = m[c];
    if (t.resp != 0) begin h.err_seen = 1; h.active = 0; end   // the DUT stops the channel on a bus error
    begin
      longint unsigned pos = h.rk;
      bit [31:0] exp_addr = h.src_run + 4*pos;
      n_checks++;
      if (t.addr != exp_addr)
        `uvm_error("SCB", $sformatf("CH%0d read addr 0x%08h expected 0x%08h", c, t.addr, exp_addr))
      if (t.beats != exp_beats(h, h.rk))
        `uvm_error("SCB", $sformatf("CH%0d read burst len %0d expected %0d (addr 0x%08h)", c, t.beats, exp_beats(h, h.rk), t.addr))
    end
    h.rk += t.beats;
  endfunction

  function void check_write(axi_item t);
    int c = find_wr(t.addr);
    ch_model h;
    n_wr_bursts++;
    if (c < 0) begin
      n_stray++;
      `uvm_error("SCB", $sformatf("stray write burst %s", t.convert2string()))
      return;
    end
    h = m[c];
    if (t.resp != 0) begin h.err_seen = 1; h.active = 0; end   // the DUT stops the channel on a bus error
    begin
      longint unsigned pos = h.wk;
      bit [31:0] exp_addr = h.dst_run + 4*pos;
      n_checks++;
      if (t.addr != exp_addr)
        `uvm_error("SCB", $sformatf("CH%0d write addr 0x%08h expected 0x%08h", c, t.addr, exp_addr))
      if (t.beats != exp_beats(h, h.wk))
        `uvm_error("SCB", $sformatf("CH%0d write burst len %0d expected %0d (addr 0x%08h)", c, t.beats, exp_beats(h, h.wk), t.addr))
      foreach (t.data[i]) begin
        bit [31:0] exp;
        longint unsigned k = h.wk + i;
        n_checks++;
        if (h.strm_run) begin
          if (k >= h.sdata.size()) begin
            `uvm_error("SCB", $sformatf("CH%0d wrote word %0d which the sensor never sent", c, k))
            continue;
          end
          exp = h.sdata[k];
        end else begin
          if (k >= h.len_run) begin
            `uvm_error("SCB", $sformatf("CH%0d wrote beyond LEN (word %0d)", c, k))
            continue;
          end
          exp = h.snap[k];
        end
        if (t.data[i] !== exp)
          `uvm_error("SCB", $sformatf("CH%0d DATA MISMATCH word %0d addr 0x%08h: got 0x%08h exp 0x%08h",
                                       c, k, t.addr + 4*i, t.data[i], exp))
      end
    end
    h.wk       += t.beats;
    h.total_wr += t.beats;
    n_wr_beats += t.beats;
    if (h.wk >= h.len_run) h.active = 0;
  endfunction

  function void check_phase(uvm_phase phase);
    for (int c = 0; c < N_CH; c++) begin
      ch_model h = m[c];
      if (h.started && !h.err_seen) begin
        if (h.wk < h.len_run)
          `uvm_error("SCB", $sformatf("CH%0d incomplete: %0d of %0d words written", c, h.wk, h.len_run))
      end
    end
  endfunction

  function void report_phase(uvm_phase phase);
    `uvm_info("SCB", $sformatf("checks=%0d  rd_bursts=%0d wr_bursts=%0d wr_beats=%0d  apb=%0d  arbitrations=%0d (wins %0d/%0d/%0d/%0d)",
              n_checks, n_rd_bursts, n_wr_bursts, n_wr_beats, n_apb, n_arb,
              arb_win[0], arb_win[1], arb_win[2], arb_win[3]), UVM_LOW)
  endfunction
endclass

// ---------------------------------------------------------------------------
// functional coverage
// ---------------------------------------------------------------------------
class dma_coverage extends uvm_component;
  `uvm_component_utils(dma_coverage)

  uvm_analysis_imp_apb  #(apb_item,      dma_coverage) apb_imp;
  uvm_analysis_imp_axi  #(axi_item,      dma_coverage) axi_imp;
  uvm_analysis_imp_strm #(strm_mon_item, dma_coverage) strm_imp;
  uvm_analysis_imp_arb  #(arb_item,      dma_coverage) arb_imp;

  // scratch variables used for sampling
  int          s_ch, s_len, s_nreq, s_win, s_wprio, s_oprio, s_off;
  bit          s_strm, s_wr, s_slv, s_rw, s_4k;
  bit [1:0]    s_prio, s_resp;
  bit [3:0]    s_blen;
  bit [1:0]    s_stat;
  bit [2:0]    s_err;
  int          s_beats, s_region;

  // ---- channel configuration space
  covergroup cg_cfg;
    option.per_instance = 1;
    cp_ch   : coverpoint s_ch   { bins ch[] = {[0:N_CH-1]}; }
    cp_mode : coverpoint s_strm { bins mem2mem = {0}; bins sensor = {1}; }
    cp_prio : coverpoint s_prio { bins p[] = {[0:3]}; }
    cp_blen : coverpoint s_blen { bins b1 = {0}; bins b2 = {1}; bins b4 = {3}; bins b8 = {7}; bins b16 = {15};
                                  bins other = {[2:2], [4:6], [8:14]}; }
    cp_len  : coverpoint s_len  { bins tiny = {[1:3]}; bins short_len = {[4:16]}; bins mid_len = {[17:256]};
                                  bins long_len = {[257:4096]}; bins huge = {[4097:$]}; }
    x_ch_mode   : cross cp_ch, cp_mode;
    x_prio_mode : cross cp_prio, cp_mode;
    x_blen_mode : cross cp_blen, cp_mode;
  endgroup

  // ---- AXI bursts
  covergroup cg_axi;
    option.per_instance = 1;
    cp_dir   : coverpoint s_wr  { bins read = {0}; bins write = {1}; }
    cp_beats : coverpoint s_beats { bins b1 = {1}; bins b2_4 = {[2:4]}; bins b5_8 = {[5:8]};
                                    bins b9_15 = {[9:15]}; bins b16 = {16}; }
    cp_resp  : coverpoint s_resp { bins okay = {0}; bins slverr = {2}; bins decerr = {3}; }
    cp_4k    : coverpoint s_4k   { bins inside_page = {0}; bins ends_on_4k_boundary = {1}; }
    x_dir_beats : cross cp_dir, cp_beats;
    x_dir_resp  : cross cp_dir, cp_resp;
    x_dir_4k    : cross cp_dir, cp_4k;
  endgroup

  // ---- arbitration
  covergroup cg_arb;
    option.per_instance = 1;
    cp_nreq   : coverpoint s_nreq  { bins n1 = {1}; bins n2 = {2}; bins n3 = {3}; bins n4 = {4}; }
    cp_winner : coverpoint s_win   { bins ch[] = {[0:N_CH-1]}; }
    cp_wprio  : coverpoint s_wprio { bins p[] = {[0:3]}; }
    cp_oprio  : coverpoint s_oprio { bins none = {-1}; bins p[] = {[0:3]}; }
    x_nreq_win   : cross cp_nreq, cp_winner;
    // winner priority vs best competing priority (equal = round-robin tie)
    x_prio_other : cross cp_wprio, cp_oprio {
      // impossible by design: the winner never has lower priority than another requester
      ignore_bins no_inversion =
          ((binsof(cp_wprio) intersect {0} && binsof(cp_oprio) intersect {[1:3]}) ||
           (binsof(cp_wprio) intersect {1} && binsof(cp_oprio) intersect {[2:3]}) ||
           (binsof(cp_wprio) intersect {2} && binsof(cp_oprio) intersect {3}));
    }
  endgroup

  // ---- interrupts / status as seen by software
  covergroup cg_irq;
    option.per_instance = 1;
    cp_ch   : coverpoint s_ch   { bins ch[] = {[0:N_CH-1]}; }
    cp_stat : coverpoint s_stat { bins done = {2'b01}; bins err = {2'b10}; }
    x_ch_stat : cross cp_ch, cp_stat;
  endgroup

  covergroup cg_err;
    option.per_instance = 1;
    cp_ch   : coverpoint s_ch  { bins ch[] = {[0:N_CH-1]}; }
    cp_code : coverpoint s_err { bins none = {0}; bins slverr = {1}; bins decerr = {2};
                                 bins cfg = {3}; }
    x_ch_code : cross cp_ch, cp_code;
  endgroup

  // ---- sensor backpressure and FIFO level seen at grant time
  covergroup cg_sensor;
    option.per_instance = 1;
    cp_ch    : coverpoint s_ch { bins ch[] = {[0:N_CH-1]}; }
    cp_stall : coverpoint s_slv { bins accepted = {0}; bins backpressured = {1}; }
    x_ch_stall : cross cp_ch, cp_stall;
  endgroup

  // ---- APB register space
  covergroup cg_apb;
    option.per_instance = 1;
    cp_region : coverpoint s_region { bins global_regs = {0}; bins channel_window = {1}; bins unmapped = {2}; }
    cp_rw     : coverpoint s_rw     { bins read = {0}; bins write = {1}; }
    cp_err    : coverpoint s_slv    { bins okay = {0}; bins slverr = {1}; }
    x_all     : cross cp_region, cp_rw, cp_err {
      ignore_bins unmapped_ok = binsof(cp_region.unmapped) && binsof(cp_err.okay);
      ignore_bins mapped_err  = binsof(cp_err.slverr) && (binsof(cp_region.global_regs) || binsof(cp_region.channel_window));
    }
  endgroup

  function new(string name, uvm_component parent);
    super.new(name, parent);
    apb_imp = new("apb_imp", this); axi_imp = new("axi_imp", this);
    strm_imp = new("strm_imp", this); arb_imp = new("arb_imp", this);
    cg_cfg = new(); cg_axi = new(); cg_arb = new(); cg_irq = new();
    cg_err = new(); cg_sensor = new(); cg_apb = new();
  endfunction

  function void write_apb(apb_item t);
    int off;
    s_rw  = t.write;
    s_slv = t.slverr;
    if (t.addr >= CH_BASE && t.addr < CH_BASE + N_CH*CH_STRIDE &&
        (((t.addr - CH_BASE) % CH_STRIDE) >> 2) <= CH_LAST) s_region = 1;
    else if (t.addr[1:0] == 0 && t.addr <= REG_VERSION) s_region = 0;
    else s_region = 2;
    cg_apb.sample();
    if (s_region != 1 || t.slverr) return;
    s_ch  = (t.addr - CH_BASE) / CH_STRIDE;
    off   = ((t.addr - CH_BASE) % CH_STRIDE) >> 2;
    if (t.write && off == CH_CTRL && t.data[1]) begin
      s_strm = t.data[2]; s_prio = t.data[5:4]; s_blen = t.data[11:8];
      s_len  = cfg_len[s_ch];
      cg_cfg.sample();
    end else if (t.write && off == CH_LEN) begin
      cfg_len[s_ch] = t.data[23:0];
    end else if (!t.write && off == CH_INT_STAT && t.rdata[1:0] != 0) begin
      s_stat = t.rdata[1:0];
      cg_irq.sample();
    end else if (!t.write && off == CH_STATUS) begin
      s_err = t.rdata[4:2];
      cg_err.sample();
    end
  endfunction
  int cfg_len[N_CH];

  function void write_axi(axi_item t);
    s_wr    = t.is_write;
    s_beats = t.beats;
    s_resp  = t.resp;
    s_4k    = (t.addr[11:0] + 4*t.beats == 4096);
    cg_axi.sample();
  endfunction

  function void write_strm(strm_mon_item t);
    s_ch  = t.ch;
    s_slv = (t.kind == STRM_STALL);
    cg_sensor.sample();
  endfunction

  function void write_arb(arb_item t);
    int unsigned max_other = 0;
    bit found = 0;
    s_nreq = $countones(t.req);
    s_win  = t.winner;
    s_wprio = t.prio[t.winner];
    s_oprio = -1;
    for (int i = 0; i < N_CH; i++)
      if (i != t.winner && t.req[i]) begin
        if (!found || t.prio[i] > max_other) max_other = t.prio[i];
        found = 1;
      end
    if (found) s_oprio = max_other;
    cg_arb.sample();
  endfunction

  function void report_phase(uvm_phase phase);
    `uvm_info("COV", $sformatf("cfg=%.1f%% axi=%.1f%% arb=%.1f%% irq=%.1f%% err=%.1f%% sensor=%.1f%% apb=%.1f%%",
      cg_cfg.get_inst_coverage(), cg_axi.get_inst_coverage(), cg_arb.get_inst_coverage(),
      cg_irq.get_inst_coverage(), cg_err.get_inst_coverage(), cg_sensor.get_inst_coverage(),
      cg_apb.get_inst_coverage()), UVM_LOW)
  endfunction
endclass

// ---------------------------------------------------------------------------
class dma_vsqr extends uvm_sequencer;
  `uvm_component_utils(dma_vsqr)
  uvm_sequencer #(apb_item)  apb_sqr;
  uvm_sequencer #(strm_item) strm_sqr[N_CH];
  axi_mem                    mem;
  axi_slave_cfg              scfg;
  dma_scoreboard             scb;
  axi_monitor                axi_mon;
  virtual dbg_if             dbg;
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
endclass

// ---------------------------------------------------------------------------
class dma_env extends uvm_env;
  `uvm_component_utils(dma_env)
  apb_agent        apb;
  strm_agent       strm[N_CH];
  axi_agent        axi;
  arb_monitor      arbm;
  dma_scoreboard   scb;
  dma_coverage     cov;
  dma_vsqr         vsqr;
  axi_mem          mem;
  axi_slave_cfg    scfg;

  function new(string name, uvm_component parent); super.new(name, parent); endfunction

  function void build_phase(uvm_phase phase);
    mem  = axi_mem::type_id::create("mem");
    scfg = axi_slave_cfg::type_id::create("scfg");
    uvm_config_db#(axi_mem)::set(this, "*", "mem", mem);
    uvm_config_db#(axi_slave_cfg)::set(this, "*", "scfg", scfg);
    apb  = apb_agent::type_id::create("apb", this);
    axi  = axi_agent::type_id::create("axi", this);
    arbm = arb_monitor::type_id::create("arbm", this);
    scb  = dma_scoreboard::type_id::create("scb", this);
    cov  = dma_coverage::type_id::create("cov", this);
    vsqr = dma_vsqr::type_id::create("vsqr", this);
    for (int c = 0; c < N_CH; c++) begin
      strm[c] = strm_agent::type_id::create($sformatf("strm%0d", c), this);
      strm[c].ch = c;
    end
  endfunction

  function void connect_phase(uvm_phase phase);
    apb.mon.ap.connect(scb.apb_imp);   apb.mon.ap.connect(cov.apb_imp);
    axi.mon.ap.connect(scb.axi_imp);   axi.mon.ap.connect(cov.axi_imp);
    arbm.ap.connect(scb.arb_imp);      arbm.ap.connect(cov.arb_imp);
    for (int c = 0; c < N_CH; c++) begin
      strm[c].mon.ap.connect(scb.strm_imp);
      strm[c].mon.ap.connect(cov.strm_imp);
      vsqr.strm_sqr[c] = strm[c].sqr;
    end
    vsqr.apb_sqr = apb.sqr;
    vsqr.mem = mem; vsqr.scfg = scfg; vsqr.scb = scb; vsqr.axi_mon = axi.mon;
    if (!uvm_config_db#(virtual dbg_if)::get(this, "", "dbg_vif", vsqr.dbg)) `uvm_fatal("NOVIF", "dbg_vif")
  endfunction
endclass
