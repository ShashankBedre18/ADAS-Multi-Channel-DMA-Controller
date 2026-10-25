// ============================================================================
// Agents: APB master, sensor-stream source (x4), AXI4 memory slave
// ============================================================================

// ============================== APB ==========================================
class apb_driver extends uvm_driver #(apb_item);
  `uvm_component_utils(apb_driver)
  virtual apb_if vif;
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  function void build_phase(uvm_phase phase);
    if (!uvm_config_db#(virtual apb_if)::get(this, "", "apb_vif", vif)) `uvm_fatal("NOVIF", "apb_vif")
  endfunction
  task run_phase(uvm_phase phase);
    vif.drv_cb.psel <= 0; vif.drv_cb.penable <= 0; vif.drv_cb.pwrite <= 0;
    vif.drv_cb.paddr <= 0; vif.drv_cb.pwdata <= 0;
    wait (vif.rst_n === 1'b1);
    forever begin
      seq_item_port.get_next_item(req);
      drive(req);
      seq_item_port.item_done();
    end
  endtask
  task drive(apb_item t);
    repeat (t.delay) @(vif.drv_cb);
    vif.drv_cb.psel <= 1; vif.drv_cb.penable <= 0;
    vif.drv_cb.pwrite <= t.write; vif.drv_cb.paddr <= t.addr; vif.drv_cb.pwdata <= t.data;
    @(vif.drv_cb);
    vif.drv_cb.penable <= 1;
    @(vif.drv_cb);
    while (!vif.drv_cb.pready) @(vif.drv_cb);
    t.rdata  = vif.drv_cb.prdata;
    t.slverr = vif.drv_cb.pslverr;
    vif.drv_cb.psel <= 0; vif.drv_cb.penable <= 0;
  endtask
endclass

class apb_monitor extends uvm_monitor;
  `uvm_component_utils(apb_monitor)
  virtual apb_if vif;
  uvm_analysis_port #(apb_item) ap;
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  function void build_phase(uvm_phase phase);
    ap = new("ap", this);
    if (!uvm_config_db#(virtual apb_if)::get(this, "", "apb_vif", vif)) `uvm_fatal("NOVIF", "apb_vif")
  endfunction
  task run_phase(uvm_phase phase);
    forever begin
      @(vif.mon_cb);
      if (vif.mon_cb.psel && vif.mon_cb.penable && vif.mon_cb.pready) begin
        apb_item t = apb_item::type_id::create("t");
        t.write = vif.mon_cb.pwrite; t.addr = vif.mon_cb.paddr;
        t.data  = vif.mon_cb.pwdata; t.rdata = vif.mon_cb.prdata; t.slverr = vif.mon_cb.pslverr;
        ap.write(t);
      end
    end
  endtask
endclass

class apb_agent extends uvm_agent;
  `uvm_component_utils(apb_agent)
  apb_driver                    drv;
  apb_monitor                   mon;
  uvm_sequencer #(apb_item)     sqr;
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  function void build_phase(uvm_phase phase);
    mon = apb_monitor::type_id::create("mon", this);
    drv = apb_driver::type_id::create("drv", this);
    sqr = uvm_sequencer#(apb_item)::type_id::create("sqr", this);
  endfunction
  function void connect_phase(uvm_phase phase);
    drv.seq_item_port.connect(sqr.seq_item_export);
  endfunction
endclass

// ============================== sensor stream ================================
class strm_driver extends uvm_driver #(strm_item);
  `uvm_component_utils(strm_driver)
  virtual strm_if vif;
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  function void build_phase(uvm_phase phase);
    if (!uvm_config_db#(virtual strm_if)::get(this, "", "strm_vif", vif)) `uvm_fatal("NOVIF", "strm_vif")
  endfunction
  task run_phase(uvm_phase phase);
    vif.drv_cb.valid <= 0; vif.drv_cb.data <= 0;
    wait (vif.rst_n === 1'b1);
    forever begin
      seq_item_port.get_next_item(req);
      repeat (req.start_delay) @(vif.drv_cb);
      foreach (req.data[i]) begin
        while ($urandom_range(99) < req.gap_pct) begin
          vif.drv_cb.valid <= 0;
          @(vif.drv_cb);
        end
        vif.drv_cb.valid <= 1;
        vif.drv_cb.data  <= req.data[i];
        do @(vif.drv_cb); while (!vif.drv_cb.ready);
      end
      vif.drv_cb.valid <= 0;
      seq_item_port.item_done();
    end
  endtask
endclass

class strm_monitor extends uvm_monitor;
  `uvm_component_utils(strm_monitor)
  virtual strm_if vif;
  int ch;
  uvm_analysis_port #(strm_mon_item) ap;
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  function void build_phase(uvm_phase phase);
    ap = new("ap", this);
    if (!uvm_config_db#(virtual strm_if)::get(this, "", "strm_vif", vif)) `uvm_fatal("NOVIF", "strm_vif")
  endfunction
  task run_phase(uvm_phase phase);
    forever begin
      @(vif.mon_cb);
      if (vif.mon_cb.valid) begin
        strm_mon_item t = strm_mon_item::type_id::create("t");
        t.ch   = ch;
        t.data = vif.mon_cb.data;
        t.kind = vif.mon_cb.ready ? STRM_WORD : STRM_STALL;
        ap.write(t);
      end
    end
  endtask
endclass

class strm_agent extends uvm_agent;
  `uvm_component_utils(strm_agent)
  int ch;
  strm_driver                   drv;
  strm_monitor                  mon;
  uvm_sequencer #(strm_item)    sqr;
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  function void build_phase(uvm_phase phase);
    mon = strm_monitor::type_id::create("mon", this);
    drv = strm_driver::type_id::create("drv", this);
    sqr = uvm_sequencer#(strm_item)::type_id::create("sqr", this);
    mon.ch = ch;
  endfunction
  function void connect_phase(uvm_phase phase);
    drv.seq_item_port.connect(sqr.seq_item_export);
  endfunction
endclass

// ============================== AXI slave ====================================
class axi_slave_driver extends uvm_component;
  `uvm_component_utils(axi_slave_driver)
  virtual axi_if  vif;
  axi_mem         mem;
  axi_slave_cfg   cfg;

  typedef struct { bit [31:0] addr; int unsigned len; } cmd_t;
  cmd_t        ar_q[$], aw_q[$];
  bit [1:0]    b_q[$];
  bit          ar_rdy, aw_rdy, w_rdy;
  int unsigned wbeat;
  bit [1:0]    wresp;

  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  function void build_phase(uvm_phase phase);
    if (!uvm_config_db#(virtual axi_if)::get(this, "", "axi_vif", vif)) `uvm_fatal("NOVIF", "axi_vif")
    if (!uvm_config_db#(axi_mem)::get(this, "", "mem", mem))            `uvm_fatal("NOCFG", "mem")
    if (!uvm_config_db#(axi_slave_cfg)::get(this, "", "scfg", cfg))     `uvm_fatal("NOCFG", "scfg")
  endfunction

  task run_phase(uvm_phase phase);
    vif.slv_cb.arready <= 0; vif.slv_cb.awready <= 0; vif.slv_cb.wready <= 0;
    vif.slv_cb.rvalid  <= 0; vif.slv_cb.bvalid  <= 0;
    vif.slv_cb.rlast   <= 0; vif.slv_cb.rdata   <= 0; vif.slv_cb.rresp <= 0; vif.slv_cb.bresp <= 0;
    wait (vif.rst_n === 1'b1);
    fork
      addr_w_proc();
      r_proc();
      b_proc();
    join
  endtask

  // AR / AW / W acceptance (cycle based, random ready)
  task addr_w_proc();
    cmd_t c;
    bit [31:0] a;
    forever begin
      @(vif.slv_cb);
      if (vif.slv_cb.arvalid && ar_rdy) begin
        c.addr = vif.slv_cb.araddr; c.len = vif.slv_cb.arlen + 1;
        ar_q.push_back(c);
      end
      if (vif.slv_cb.awvalid && aw_rdy) begin
        c.addr = vif.slv_cb.awaddr; c.len = vif.slv_cb.awlen + 1;
        aw_q.push_back(c);
      end
      if (vif.slv_cb.wvalid && w_rdy) begin
        c     = aw_q[0];
        a     = c.addr + 4 * wbeat;
        wresp = cfg.resp_for(c.addr, 1'b1);
        if (wresp == 2'b00) mem.write(a, vif.slv_cb.wdata, vif.slv_cb.wstrb);
        wbeat++;
        if (vif.slv_cb.wlast) begin
          if (wbeat != c.len) `uvm_error("AXI_SLV", $sformatf("WLAST after %0d beats, AWLEN+1=%0d", wbeat, c.len))
          void'(aw_q.pop_front());
          b_q.push_back(wresp);
          wbeat = 0;
        end else if (wbeat >= c.len) begin
          `uvm_error("AXI_SLV", "missing WLAST")
        end
      end
      ar_rdy = ($urandom_range(99) < cfg.ar_rdy_pct);
      aw_rdy = ($urandom_range(99) < cfg.aw_rdy_pct);
      w_rdy  = (aw_q.size() > 0) && ($urandom_range(99) < cfg.w_rdy_pct);
      vif.slv_cb.arready <= ar_rdy;
      vif.slv_cb.awready <= aw_rdy;
      vif.slv_cb.wready  <= w_rdy;
    end
  endtask

  task r_proc();
    cmd_t c;
    bit [1:0] resp;
    forever begin
      while (ar_q.size() == 0) @(vif.slv_cb);
      c    = ar_q.pop_front();
      resp = cfg.resp_for(c.addr, 1'b0);
      repeat ($urandom_range(cfg.r_lat_max, cfg.r_lat_min)) @(vif.slv_cb);
      for (int unsigned i = 0; i < c.len; i++) begin
        vif.slv_cb.rvalid <= 1;
        vif.slv_cb.rdata  <= mem.read(c.addr + 4*i);
        vif.slv_cb.rresp  <= resp;
        vif.slv_cb.rlast  <= (i == c.len - 1);
        do @(vif.slv_cb); while (!vif.slv_cb.rready);
        vif.slv_cb.rvalid <= 0;
        vif.slv_cb.rlast  <= 0;
        while ($urandom_range(99) < cfg.r_gap_pct) @(vif.slv_cb);
      end
    end
  endtask

  task b_proc();
    bit [1:0] resp;
    forever begin
      while (b_q.size() == 0) @(vif.slv_cb);
      resp = b_q.pop_front();
      repeat ($urandom_range(cfg.b_lat_max, cfg.b_lat_min)) @(vif.slv_cb);
      vif.slv_cb.bvalid <= 1;
      vif.slv_cb.bresp  <= resp;
      do @(vif.slv_cb); while (!vif.slv_cb.bready);
      vif.slv_cb.bvalid <= 0;
    end
  endtask
endclass

class axi_monitor extends uvm_monitor;
  `uvm_component_utils(axi_monitor)
  virtual axi_if vif;
  uvm_analysis_port #(axi_item) ap;

  axi_item rd_pend[$], wr_pend[$];
  int unsigned rd_age[$], wr_age[$];
  bit [31:0] w_beats[$];
  int unsigned cycle;
  int unsigned n_rd, n_wr;

  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  function void build_phase(uvm_phase phase);
    ap = new("ap", this);
    if (!uvm_config_db#(virtual axi_if)::get(this, "", "axi_vif", vif)) `uvm_fatal("NOVIF", "axi_vif")
  endfunction

  task run_phase(uvm_phase phase);
    axi_item t;
    forever begin
      @(vif.mon_cb);
      cycle++;
      if (vif.mon_cb.arvalid && vif.mon_cb.arready) begin
        t = axi_item::type_id::create("rd");
        t.is_write = 0; t.addr = vif.mon_cb.araddr; t.beats = vif.mon_cb.arlen + 1;
        rd_pend.push_back(t); rd_age.push_back(cycle);
      end
      if (vif.mon_cb.rvalid && vif.mon_cb.rready) begin
        rd_pend[0].data.push_back(vif.mon_cb.rdata);
        if (vif.mon_cb.rresp != 0) rd_pend[0].resp = vif.mon_cb.rresp;
        if (vif.mon_cb.rlast) begin
          t = rd_pend.pop_front();
          t.latency = cycle - rd_age.pop_front();
          n_rd++;
          ap.write(t);
        end
      end
      if (vif.mon_cb.awvalid && vif.mon_cb.awready) begin
        t = axi_item::type_id::create("wr");
        t.is_write = 1; t.addr = vif.mon_cb.awaddr; t.beats = vif.mon_cb.awlen + 1;
        wr_pend.push_back(t); wr_age.push_back(cycle);
      end
      if (vif.mon_cb.wvalid && vif.mon_cb.wready) begin
        if (wr_pend.size() == 0) `uvm_error("AXI_MON", "W beat before AW")
        else wr_pend[0].data.push_back(vif.mon_cb.wdata);
      end
      if (vif.mon_cb.bvalid && vif.mon_cb.bready) begin
        t = wr_pend.pop_front();
        t.resp    = vif.mon_cb.bresp;
        t.latency = cycle - wr_age.pop_front();
        n_wr++;
        ap.write(t);
      end
    end
  endtask
endclass

class axi_agent extends uvm_agent;
  `uvm_component_utils(axi_agent)
  axi_slave_driver drv;
  axi_monitor      mon;
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  function void build_phase(uvm_phase phase);
    mon = axi_monitor::type_id::create("mon", this);
    drv = axi_slave_driver::type_id::create("drv", this);
  endfunction
endclass

// ============================== arbitration monitor ==========================
class arb_monitor extends uvm_monitor;
  `uvm_component_utils(arb_monitor)
  virtual dbg_if vif;
  uvm_analysis_port #(arb_item) ap;
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  function void build_phase(uvm_phase phase);
    ap = new("ap", this);
    if (!uvm_config_db#(virtual dbg_if)::get(this, "", "dbg_vif", vif)) `uvm_fatal("NOVIF", "dbg_vif")
  endfunction
  task run_phase(uvm_phase phase);
    forever begin
      @(vif.mon_cb);
      if (vif.mon_cb.grant_fire) begin
        arb_item t = arb_item::type_id::create("t");
        t.req = vif.mon_cb.req; t.prio = vif.mon_cb.prio;
        t.winner = vif.mon_cb.gnt_idx;
        ap.write(t);
      end
    end
  endtask
endclass
