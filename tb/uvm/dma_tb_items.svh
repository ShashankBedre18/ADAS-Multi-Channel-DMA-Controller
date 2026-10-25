// ============================================================================
// Transaction items, memory model, slave configuration
// ============================================================================

// ---------------------------------------------------------------- APB
class apb_item extends uvm_sequence_item;
  rand bit          write;
  rand bit [11:0]   addr;
  rand bit [31:0]   data;
  rand int unsigned delay;
  bit [31:0]        rdata;
  bit               slverr;

  constraint c_delay { delay dist {0 := 70, [1:3] := 30}; }

  `uvm_object_utils(apb_item)
  function new(string name = "apb_item"); super.new(name); endfunction
  function string convert2string();
    return $sformatf("APB %s addr=0x%03h %s=0x%08h%s", write ? "WR" : "RD", addr,
                     write ? "wdata" : "rdata", write ? data : rdata, slverr ? " SLVERR" : "");
  endfunction
endclass

// ---------------------------------------------------------------- sensor stream
class strm_item extends uvm_sequence_item;
  rand int unsigned nwords;
  rand int unsigned gap_pct;       // % of cycles the sensor pauses between words
  rand int unsigned start_delay;
  bit [31:0]        data[$];

  constraint c_n { nwords inside {[1:8192]}; gap_pct inside {[0:80]}; start_delay inside {[0:20]}; }

  `uvm_object_utils(strm_item)
  function new(string name = "strm_item"); super.new(name); endfunction
  function void post_randomize();
    data.delete();
    repeat (nwords) data.push_back($urandom());
  endfunction
endclass

typedef enum {STRM_WORD, STRM_STALL} strm_kind_e;
class strm_mon_item extends uvm_object;
  int          ch;
  strm_kind_e  kind;
  bit [31:0]   data;
  `uvm_object_utils(strm_mon_item)
  function new(string name = "strm_mon_item"); super.new(name); endfunction
endclass

// ---------------------------------------------------------------- AXI burst (observed)
class axi_item extends uvm_object;
  bit          is_write;
  bit [31:0]   addr;
  int unsigned beats;
  bit [31:0]   data[$];
  bit [1:0]    resp;
  int unsigned latency;            // address handshake to last beat/response (cycles)
  `uvm_object_utils(axi_item)
  function new(string name = "axi_item"); super.new(name); endfunction
  function string convert2string();
    return $sformatf("AXI %s addr=0x%08h beats=%0d resp=%0d", is_write ? "WR" : "RD", addr, beats, resp);
  endfunction
endclass

// ---------------------------------------------------------------- arbitration snapshot
class arb_item extends uvm_object;
  bit [N_CH-1:0]       req;
  bit [N_CH-1:0][1:0]  prio;
  int                  winner;
  `uvm_object_utils(arb_item)
  function new(string name = "arb_item"); super.new(name); endfunction
endclass

// ---------------------------------------------------------------- memory model
class axi_mem extends uvm_object;
  bit [31:0] mem [bit [31:0]];
  `uvm_object_utils(axi_mem)
  function new(string name = "axi_mem"); super.new(name); endfunction

  // deterministic content for never-written locations
  function bit [31:0] pattern(bit [31:0] a);
    return ((a ^ 32'hA5A5_1234) * 32'h9E37_79B1) + (a >> 2);
  endfunction
  function bit [31:0] read(bit [31:0] a);
    a[1:0] = 2'b00;
    return mem.exists(a) ? mem[a] : pattern(a);
  endfunction
  function void write(bit [31:0] a, bit [31:0] d, bit [3:0] strb = 4'hF);
    bit [31:0] old;
    a[1:0] = 2'b00;
    old = read(a);
    for (int b = 0; b < 4; b++) if (strb[b]) old[8*b +: 8] = d[8*b +: 8];
    mem[a] = old;
  endfunction
  function void fill_random(bit [31:0] base, int unsigned nwords);
    for (int unsigned i = 0; i < nwords; i++) mem[base + 4*i] = $urandom();
  endfunction
endclass

// ---------------------------------------------------------------- slave behaviour knobs
class axi_slave_cfg extends uvm_object;
  // percent of cycles the corresponding ready is high
  int unsigned ar_rdy_pct = 100, aw_rdy_pct = 100, w_rdy_pct = 100;
  int unsigned r_lat_min = 1, r_lat_max = 3;      // cycles from AR to first R beat
  int unsigned r_gap_pct = 0;                      // chance of a bubble between R beats
  int unsigned b_lat_min = 1, b_lat_max = 3;

  typedef struct { bit [31:0] lo, hi; bit [1:0] resp; bit on_read, on_write; } err_region_t;
  err_region_t err_regions[$];

  `uvm_object_utils(axi_slave_cfg)
  function new(string name = "axi_slave_cfg"); super.new(name); endfunction

  function void add_error(bit [31:0] lo, bit [31:0] hi, bit [1:0] resp, bit on_read, bit on_write);
    err_region_t e;
    e.lo = lo; e.hi = hi; e.resp = resp; e.on_read = on_read; e.on_write = on_write;
    err_regions.push_back(e);
  endfunction
  function void clear_errors(); err_regions.delete(); endfunction

  function bit [1:0] resp_for(bit [31:0] addr, bit is_write);
    foreach (err_regions[i])
      if (addr >= err_regions[i].lo && addr < err_regions[i].hi &&
          (is_write ? err_regions[i].on_write : err_regions[i].on_read))
        return err_regions[i].resp;
    return 2'b00;
  endfunction

  function void set_fast();
    ar_rdy_pct = 100; aw_rdy_pct = 100; w_rdy_pct = 100;
    r_lat_min = 1; r_lat_max = 2; r_gap_pct = 0; b_lat_min = 1; b_lat_max = 2;
  endfunction
  function void set_slow();
    ar_rdy_pct = 30; aw_rdy_pct = 30; w_rdy_pct = 40;
    r_lat_min = 8; r_lat_max = 20; r_gap_pct = 40; b_lat_min = 6; b_lat_max = 16;
  endfunction
  function void set_random();
    ar_rdy_pct = $urandom_range(20, 100); aw_rdy_pct = $urandom_range(20, 100);
    w_rdy_pct  = $urandom_range(20, 100);
    r_lat_min  = $urandom_range(1, 4);  r_lat_max = r_lat_min + $urandom_range(0, 10);
    r_gap_pct  = $urandom_range(0, 50);
    b_lat_min  = $urandom_range(1, 4);  b_lat_max = b_lat_min + $urandom_range(0, 8);
  endfunction
endclass
