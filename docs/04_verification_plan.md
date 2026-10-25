# 4. Verification plan and results

Simulator: Vivado xsim 2025.2 (UVM 1.2, SVA, covergroups, code coverage).

## 4.1 Environment (`tb/`)

```
tb_top ── DUT (dma_top) ── bound SVA (dma_sva, dma_ch_sva)
  │
  └─ uvm_test_top (dma_*_test)
       └─ dma_env
            ├─ apb_agent      driver / monitor / sequencer      register programming
            ├─ strm_agent x4  driver / monitor / sequencer      camera, radar, LiDAR, diag sensor streams
            ├─ axi_agent      reactive memory slave + monitor   random latency, back-pressure, error injection
            ├─ arb_monitor    observes arbiter requests/grants  (hierarchical probe through dbg_if)
            ├─ dma_scoreboard reference model + checkers
            ├─ dma_coverage   7 covergroups
            └─ dma_vsqr       virtual sequencer -> 9 virtual sequences (the scenarios)
```

### Scoreboard (`dma_scoreboard`)

An independent model of each channel is built **only from the observed APB writes**. It checks, for every AXI burst:

* **address sequence** - each read/write burst starts where the model says it should,
* **burst length** - re-derives `min(BLEN+1, remaining, 4KB page space...)` independently of the RTL,
* **data integrity** - every written word equals the memory snapshot taken at START (memory source) or the word the sensor really sent, in order (stream source); writing a word the sensor never sent, or beyond LEN, is an error,
* **stray traffic** - any burst outside all programmed windows,
* **interrupt sanity** - DONE only after all words were written; ERR only when an error was injected / an illegal config was made,
* **completeness** at end of test (all words of every non-failed channel moved).

## 4.2 Assertions (`tb/sva/dma_sva.sv`, bound without touching RTL)

25 properties, 52 instances (the channel checker is bound into all 4 channels, the priority check is generated per channel).

| Group | Assertions |
|---|---|
| APB | access follows setup, controls stable in setup, PREADY, PSLVERR only in access phase |
| AXI handshake | AW / AR / W payload stable while VALID && !READY |
| AXI legality | size = 4 B, INCR, aligned, `len <= 15`, **no 4 KB crossing** (read and write), WLAST on exactly beat AWLEN+1, one phase at a time |
| Arbitration | grant only to a requester, **winner has the highest priority** (per channel instance), fire implies valid grant |
| Channel (`dma_ch_sva`, 4 instances) | `s_ready` only when active stream, no FIFO under/overflow, completion only for the in-flight channel, `req` only from an enabled active channel, `irq == |(INT_STAT & INT_EN)`, illegal START never activates, burst size in 1..16 |
| IRQ | global irq is the OR of channel irqs |

`cover property` statements are in the source as documentation, but xsim 2025.2 does not support
them ("Cover is not supported yet for simulation" warning) so they are ignored; the equivalent
scenarios are covered by the covergroups below.

## 4.3 Functional coverage (`dma_coverage`)

| Covergroup | What it measures |
|---|---|
| `cg_cfg` | channel x mode (mem2mem/sensor) x priority x burst length x transfer length, with crosses |
| `cg_axi` | direction x burst length x response (OKAY/SLVERR/DECERR) x "burst ends on 4 KB boundary" |
| `cg_arb` | number of simultaneous requesters x winner, winner priority x best other priority |
| `cg_irq` | channel x interrupt cause seen by software (DONE / ERR) |
| `cg_err` | channel x error code (none / SLVERR / DECERR / illegal config) |
| `cg_sensor` | channel x sensor accepted vs back-pressured |
| `cg_apb` | register region (global / channel / unmapped) x read/write x PSLVERR |

## 4.4 Test list

| Test | Scenario | Checks that matter |
|---|---|---|
| `dma_regs_test` | reset values, RW/RO behaviour, 24-bit LEN mask, unmapped -> PSLVERR, W1C | register spec |
| `dma_smoke_test` | one mem2mem and one sensor transfer | bring-up |
| `dma_sensor_fusion_test` | **the ADAS scenario**: camera 4608 words, radar 256 (bursty), LiDAR 1024, diag copy 512, all at once | all data correct, radar finishes first |
| `dma_burst_sweep_test` | every BLEN 0..15 x random lengths x addresses a few words below a 4 KB page | burst partitioning, 4 KB rule |
| `dma_priority_test` | strict priority order {3,2,1,0}; high-priority long job before low-priority short job; equal priority | priority order, round-robin rotation of grants |
| `dma_error_test` | SLVERR read, DECERR write, SLVERR on a sensor channel, in parallel with a healthy channel; recovery; 4x4 error matrix | isolation, error codes, restart |
| `dma_cfg_err_test` | zero length, unaligned src/dst, START without EN, START while busy | no bus traffic, ERR_CFG |
| `dma_backpressure_test` | very slow memory, three fast sensors | FIFOs fill, sensors are held off, no data loss |
| `dma_random_test` | constrained-random mix (channels, modes, sizes, burst lengths, priorities, slave timing, sensor gaps) | everything, 5 seeds x 40 iterations in the regression |

## 4.5 Results (last regression, `sim/logs/`)

* **13 / 13 test runs pass** (8 directed + random with 5 seeds), 0 UVM errors, 0 assertion failures.
* **Functional coverage 100 %** (all 7 covergroups, merged over all runs).
* Equal-priority grant sequence observed in `dma_priority_test`: `1,2,3,0,1,2,3,0,...` (perfect round-robin).
* **Code coverage of the RTL** (statement / branch / condition / toggle):

| Module | Stmt | Branch | Cond | Toggle |
|---|---|---|---|---|
| dma_top | 100 | 94.1 | 83.3 | 71.6 |
| dma_channel | 100 | 100 | 97.2 | 54.6 |
| dma_sfifo | 100 | 100 | 100 | 99.5 |
| dma_arbiter | 100 | 100 | 100 | 100 |
| dma_engine | 100 | 100 | 97.9 | 92.0 |

  Toggle coverage is lower in `dma_top`/`dma_channel` because the high bits of the 32-bit address
  and length registers never change in a small-memory testbench.

## 4.6 "Does the testbench really catch bugs?" - mutation check

Four deliberate RTL bugs were injected one at a time into a copy of the final RTL; each was caught by the intended test:

| Injected bug | Test | Caught by |
|---|---|---|
| data bit flipped on beat 5 of a burst | `dma_smoke_test` | scoreboard `DATA MISMATCH word 5` |
| arbiter ignores priority | `dma_priority_test` | priority order check (`strict priority order wrong`) |
| 4 KB splitting removed | `dma_burst_sweep_test` | scoreboard burst-length check (`read burst len 2 expected 1`) |
| DECERR reported as SLVERR | `dma_error_test` | error-code check (`err code: got 1 expected 2`) |

## 4.7 Running it

```
sim/regress.sh                      # build + all tests + coverage reports
sim/build.sh                        # build only
sim/run_test.sh dma_random_test 42 100   # one test, seed 42, 100 random iterations
sim/coverage_report.sh              # (re)generate reports from existing runs
```

(`sim/*.bat` equivalents are provided for Windows `cmd`.)

## 4.8 Not done / honest limits

* No formal verification and no UVM RAL model (registers are checked by directed sequences).
* xsim has no assertion cover support (see 4.2).
* Synthesis numbers are post-synthesis estimates, not place-and-route.
* Code coverage includes testbench modules in the xcrg totals; the table above lists the RTL modules only.
