# ADAS Multi-Channel DMA Controller Subsystem

End-to-end ASIC/FPGA-style project: specification -> architecture -> synthesizable RTL ->
UVM verification (assertions, scoreboard, functional + code coverage) -> FPGA synthesis.

**Real-world problem.** An ADAS computer must continuously pull high-bandwidth data from a camera,
radar and LiDAR into memory without burning CPU time, while the latency-critical sensor (radar,
feeds emergency braking) is served first. This project is the DMA subsystem that solves it:
4 channels, sensor-stream or memory sources, AXI4 bursts, priority arbitration, interrupts, error handling.

## Results at a glance

| | |
|---|---|
| Regression | **13 / 13 runs pass** (8 directed tests + constrained-random x 5 seeds), 0 UVM errors, 0 assertion failures |
| Functional coverage | **100 %** (7 covergroups, merged) |
| RTL code coverage | statement 100 % on every module, branch 94-100 % |
| Mutation check | 4/4 injected RTL bugs caught by the testbench |
| Synthesis (xc7a100t, Vivado 2025.2, out-of-context) | 1660 LUT, 1065 FF, 0 BRAM, **100 MHz met** (WNS +1.74 ns, post-synthesis estimate) |
| ADAS scenario | camera 4608 + radar 256 + LiDAR 1024 + diag 512 words concurrently, all data verified; radar (priority 3) finishes first |

## What the design contains

| Required by the brief | Basic extras |
|---|---|
| 4 concurrent channels, APB configuration registers | sensor-stream input with a 32-word FIFO per channel (back-pressure, no data loss) |
| priority arbitration (2-bit priority per channel) | round-robin between channels of equal priority |
| AXI4 burst transfers (1-16 beats) | automatic 4 KB boundary splitting (AXI rule) |
| DONE / ERR interrupts (maskable, write-1-to-clear) + status registers | illegal-configuration detection |
| error handling: SLVERR / DECERR isolated to one channel, restart after error | |

## Folder map

```
ADAS_DMA_Subsystem/
├── docs/
│   ├── 01_problem_and_requirements.md   real-world problem, requirements
│   ├── 02_architecture.md               datapath, FSM, arbitration, timing decisions, limitations
│   ├── 03_register_map.md               APB registers + programming example
│   ├── 04_verification_plan.md          environment, assertions, coverage, tests, results
│   ├── ADAS_DMA_Milestones_Report.docx  the project report, milestone by milestone
│   ├── ADAS_DMA_Complete_Project_Flow.docx  complete flow: basics, design, verification, synthesis
│   ├── ADAS_DMA_Project_Status_Report.docx  status of every item the brief asked for
│   ├── ADAS_DMA_How_To_Run_And_Analyse.docx  step-by-step guide: run, read logs, coverage, waveforms
│   ├── block_diagram.svg
│   └── figures/                         diagrams, waveforms, regression table, coverage screenshots
├── rtl/                                 dma_pkg, dma_top, dma_channel, dma_arbiter, dma_engine, dma_sfifo
├── tb/
│   ├── if/dma_ifs.sv                    APB / AXI / sensor-stream / debug interfaces
│   ├── sva/dma_sva.sv                   assertions (bound to the DUT)
│   ├── uvm/                             items, agents, scoreboard, coverage, env, sequences, tests
│   └── tb_top.sv
├── scripts/                             figure generators (waveforms, diagrams) and the report builder
├── sim/                                 build / run / regression / coverage scripts (.sh and .bat)
│   ├── logs/                            logs of the last regression
│   └── report/                          HTML functional + code coverage reports
└── synth/                               Vivado synthesis script, utilization and timing reports
```

## How to run (needs Vivado/xsim; edit the path in `sim/env.bat` or `sim/*.sh` if not `D:\Vivado\2025.2`)

Windows (cmd or PowerShell):

```
sim\regress.bat                          :: build, run all tests, coverage reports
sim\build.bat                            :: build only
sim\run_test.bat dma_sensor_fusion_test  :: one test  (args: test [seed] [random_iterations])
sim\run_gui.bat dma_priority_test        :: open one test in the Vivado simulator GUI with waveforms
```

Git Bash: `sim/regress.sh`, `sim/build.sh`, `sim/run_test.sh dma_random_test 42 100`.

Open `sim/report/functional/functionalCoverageReport/dashboard.html` and
`sim/report/code/codeCoverageReport/dashboard.html` for coverage.
Synthesis: `cd synth && vivado -mode batch -source synth.tcl`.
Vivado GUI project: in Vivado choose Tools > Run Tcl Script and select `scripts/create_vivado_project.tcl` (creates `vivado_proj/adas_dma.xpr` with the RTL, the UVM testbench and the simulation settings).
Waveforms: add `-testplusarg WAVES` to the xsim command (writes `dma.vcd`); `python scripts/vcd2svg.py` turns a VCD into the figures in `docs/figures/`.

## How the milestones are covered

| Milestone | Deliverable |
|---|---|
| 1 Requirements and architecture | `docs/01..03`, `docs/block_diagram.svg` (channel registers, arbitration scheme, datapath + controller, block diagram) |
| 2 RTL | `rtl/` - channel controller, arbitration logic, transfer FSM, interrupt/status registers; RTL simulation through `sim/` |
| 3 Verification | `tb/` - SystemVerilog transaction-based testbench, UVM agents and sequences, scoreboarding/checking, SVA protocol assertions, functional and code coverage reports |

## Known limits

Single outstanding burst (no read/write overlap), 32-bit INCR only, register-based setup (no descriptors),
strict priority (a long high-priority job delays lower priorities), no bus watchdog, no formal verification /
UVM RAL, xsim ignores `cover property` (so assertion cover points are documentation only), synthesis numbers
are pre-route. See `docs/02_architecture.md` section 2.9 and `docs/04_verification_plan.md` section 4.8.
