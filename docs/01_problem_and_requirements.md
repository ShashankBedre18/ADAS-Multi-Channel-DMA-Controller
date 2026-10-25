# 1. Problem statement and requirements

## 1.1 The real-world problem

A modern ADAS (Advanced Driver Assistance System) computer ingests data from several sensors at the same time:

| Sensor | Behaviour | What matters |
|---|---|---|
| Front camera | very high bandwidth, continuous frames | throughput, never lose pixels |
| Radar | small bursty packets | **latency** - it feeds emergency braking |
| LiDAR | medium bandwidth point-cloud packets | throughput + bounded latency |
| Diagnostics / logging | bulk memory-to-memory copies | must not disturb the sensors |

If the CPU copies this data (processor-centric movement) it burns cycles, adds jitter and, under
load, causes exactly the bottleneck that makes a perception pipeline miss its deadline.

**Solution:** a configurable multi-channel DMA subsystem that moves sensor data straight into
memory, arbitrates between the streams by criticality, and reports status/errors by interrupt, so the
CPU only programs registers and handles completions.

## 1.2 Brief from the course (and where each item is delivered)

| Item in the brief | Delivered in |
|---|---|
| Multiple concurrent data streams | 4 channels, shared burst engine (`rtl/dma_channel.sv`, `dma_engine.sv`) |
| Prioritise critical sensor transfers | 2-bit priority per channel + `dma_arbiter.sv` |
| Burst transactions | AXI4 INCR bursts of 1-16 beats |
| Status interrupts | per-channel `DONE / ERR` + global irq |
| Reliable error handling | AXI SLVERR/DECERR capture, illegal-configuration check, error isolated to one channel, restart |
| M1: channel configuration registers, arbitration, datapath/controller architecture, block diagram | `docs/02_architecture.md`, `docs/03_register_map.md`, `docs/block_diagram.svg` |
| M2: channel controller, arbitration, transfer FSM, interrupt/status registers, RTL simulation | `rtl/` + `sim/` |
| M3: SV testbench, UVM agents + sequences, scoreboard, assertions, functional + code coverage | `tb/`, `sim/report/` |

## 1.3 Basic extra features (small, but needed to make the design correct and useful)

1. **Sensor-stream source** (valid/ready port + 32-word FIFO per channel) in addition to memory-to-memory,
   because the brief is about camera / radar / LiDAR data. A full FIFO back-pressures the sensor, so no data is lost.
2. **Round-robin between channels of equal priority**, so equal channels share the bus fairly.
3. **4 KB boundary splitting** - bursts never cross a 4 KB page (an AXI rule), done automatically.
4. **Illegal configuration detection** (zero length, unaligned address, START without EN).

## 1.4 Functional requirements

| ID | Requirement |
|---|---|
| R1 | The subsystem shall provide 4 independent channels, each configurable for memory-to-memory or sensor-stream-to-memory transfers. |
| R2 | The memory interface shall be AXI4 (32-bit data/address, INCR bursts up to 16 beats). No burst may cross a 4 KB boundary. |
| R3 | Channels shall be configured through an APB register interface. |
| R4 | A channel with a higher priority shall be served before lower-priority channels at every burst boundary. |
| R5 | Equal-priority channels shall share the bus fairly (round-robin). |
| R6 | The subsystem shall raise a per-channel interrupt on completion and on error. Interrupts are write-1-to-clear and maskable. |
| R7 | AXI SLVERR/DECERR on any beat shall stop only the affected channel, record the cause and raise `ERR`; other channels shall continue. |
| R8 | Illegal configurations shall be rejected at START with `ERR_CFG` and shall generate no bus traffic. |
| R9 | After an error a channel shall be restartable by software. |
| R10 | Data shall never be lost or reordered: a sensor that cannot be accepted is back-pressured. |

## 1.5 Non-functional goals

* Synthesizable, single clock, asynchronous active-low reset.
* Meets 100 MHz on a 7-series FPGA at synthesis level (results in `README.md`).
* All parameters (channels, FIFO depth, burst size) are constants in `rtl/dma_pkg.sv`.
