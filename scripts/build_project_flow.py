"""
build_project_flow.py - writes docs/ADAS_DMA_Complete_Project_Flow.docx
(the complete project flow: basics -> requirements -> architecture -> RTL -> verification -> synthesis).
Shares its formatting helpers with build_milestone_report.py.  Needs: pip install python-docx
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = open(os.path.join(_HERE, "build_milestone_report.py"), encoding="utf8").read()
exec(_SRC[:_SRC.index("# ---------------------------------------------------------------- cover")])
OUT = os.path.join(ROOT, "docs", "ADAS_DMA_Complete_Project_Flow.docx")

# ---------------------------------------------------------------- cover
for _ in range(3):
    doc.add_paragraph()
p = P("L&T EduTech  |  VLSI Principles, RTL Design and Verification  |  Project 1", "c", 12); p.runs[0].font.color.rgb = GREY
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("ADAS Multi-Channel DMA Controller Subsystem"); r.font.size = Pt(26); r.bold = True; r.font.color.rgb = NAVY
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Complete project flow: from basic concepts to verification and synthesis"); r.font.size = Pt(15); r.font.color.rgb = BLUE
doc.add_paragraph()
for t in ("A real-world problem solved end to end", "Problem analysis and requirements", "Architecture and register map",
          "Synthesizable SystemVerilog RTL", "UVM verification with assertions, scoreboard and coverage",
          "Simulation regression and coverage closure", "FPGA synthesis and timing closure"):
    P(t, "c", 12, after=2)
doc.add_paragraph().paragraph_format.space_after = Pt(30)
T(["Item", "Details"], [
    ["Student name", ""], ["Registration / LMS ID", ""],
    ["Project folder", "Desktop\\LNT_ADAS_DMA_Subsystem\\ADAS_DMA_Subsystem"],
    ["Tools", "SystemVerilog, UVM 1.2, SVA, AMD Vivado 2025.2 (xsim, xcrg, synthesis)"],
    ["Final results", "13/13 test runs pass, 100 % functional coverage, 100 % RTL statement coverage, 100 MHz met"],
], [4.5, 11.5], zebra=False, size=10)
PAGEBREAK()

H("Contents", 1)
TOC_PAR = field(doc.add_paragraph(), 'TOC \\o "1-2" \\h \\z \\u')
P("(In Word: right-click the list and choose Update Field to add page numbers.)", size=9, italic=True)
TOC_ANCHOR = doc.paragraphs[-1]
PAGEBREAK()

# ================================================================ 1
H("1. What this project is (the big picture)", 1)
P("This project designs and verifies a **Multi-Channel DMA (Direct Memory Access) Controller Subsystem** for an automotive "
  "ADAS (Advanced Driver Assistance System) computer, exactly as asked in Project 1 of the course. It is a complete chip-design "
  "flow in miniature: the problem is analysed and turned into requirements, an architecture is designed, synthesizable RTL is "
  "written in SystemVerilog, the RTL is verified with a UVM testbench (assertions, scoreboard, coverage), and finally the "
  "design is synthesized for an FPGA to prove it is implementable.", "j")
H("1.1 One-paragraph explanation", 2)
P("A car carries a front camera, a radar and a LiDAR. Each continuously produces data, and that data must land in memory so the "
  "perception software can process it. If the CPU copies every word itself it becomes the bottleneck. A DMA controller is a "
  "small, dedicated hardware block that copies data on its own. The CPU only tells it what to copy, from where, to where, how "
  "much and how urgent it is, and the DMA interrupts the CPU when the job is done or something goes wrong. Our DMA has **four "
  "independent channels**, serves the **most critical sensor first**, moves data in **AXI4 bursts**, raises **status "
  "interrupts**, and **isolates errors** to the channel that caused them.", "j")
H("1.2 What the brief asks for, and what the project contains", 2)
T(["The brief asks for", "Delivered as"], [
    ["Multiple concurrent data streams", "4 independent channels sharing one burst engine"],
    ["Prioritise critical sensor transfers", "2-bit priority per channel; the arbiter always serves the highest priority first"],
    ["Burst transactions", "AXI4 INCR bursts of 1 to 16 beats"],
    ["Status interrupts", "DONE and ERR interrupt per channel (maskable, write-1-to-clear) + global irq"],
    ["Reliable error handling", "SLVERR / DECERR detection, illegal-configuration check, error isolated to one channel, restart"],
    ["SystemVerilog transaction-based testbench", "UVM environment with APB, sensor and AXI agents"],
    ["Assertions", "25 SVA properties (APB, AXI, arbitration, channel, interrupts)"],
    ["Covergroups and functional coverage reports", "7 covergroups, merged HTML reports, 100 %"],
], [6.0, 10.6], caption="The brief and the deliverables")
T(["Part", "What it is", "Where"], [
    ["Specification", "Problem, requirements, architecture, register map, block diagram", "docs/"],
    ["Design (RTL)", "6 SystemVerilog modules, about 690 lines, fully synthesizable", "rtl/"],
    ["Verification environment", "UVM testbench: 3 agent types, scoreboard, coverage, 9 scenarios, assertions", "tb/"],
    ["Simulation flow", "Scripts to compile, run 13 test runs, merge coverage, build HTML reports", "sim/"],
    ["Implementation flow", "Vivado synthesis script, utilization and timing reports", "synth/"],
], [3.6, 9.6, 3.4], caption="What the project folder contains")
H("1.3 The end-to-end flow at a glance", 2)
FIGURE("f_flow.png", "The order in which the project was built. Each step is explained in the following chapters.")
H("1.4 How to read this document", 2)
B(["Chapters 2 and 3 give the background (DMA, AXI, APB, FSM, UVM) and the real-world problem.",
   "Chapters 4 to 8 explain the design: the project flow, architecture, registers, every RTL module and cycle-by-cycle worked examples.",
   "Chapter 9 explains the key features; chapters 10 and 11 explain the verification environment, assertions, coverage and results.",
   "Chapters 12 to 14 cover running the flow, synthesis, problems found during development, final results, limits and future work.",
   "Appendices hold a glossary, a file list, typical viva questions and how to change the design."])
PAGEBREAK()

# ================================================================ 2
H("2. Basic concepts you need first", 1)
H("2.1 What is DMA and why does it exist?", 2)
P("In a simple system the CPU moves data with load and store instructions: read a word from the source, write it to the "
  "destination, repeat. That wastes CPU time and the CPU is then not available for real work. A DMA controller is a second bus "
  "master. It reads from a source and writes to a destination on its own, using the same memory bus, while the CPU does "
  "something else.", "j")
T(["", "CPU copy (processor-centric)", "DMA copy"], [
    ["Who moves data", "CPU instructions", "Dedicated hardware"],
    ["CPU load", "100 % of copy time", "Only set-up and completion interrupt"],
    ["Latency / jitter", "Depends on what the CPU is doing", "Predictable, set by arbitration"],
    ["Typical use", "Tiny copies", "Sensors, network, storage, video"],
], [3.6, 6.5, 6.5], caption="CPU copy versus DMA")
FIGURE("m1_cpu_vs_dma.png", "Processor-centric data movement (the problem in the brief) versus DMA-centric data movement (this project).")
H("2.2 Memory-mapped registers and the control plane", 2)
P("Software controls hardware by writing and reading registers at fixed addresses. Here the control plane uses **APB** "
  "(Advanced Peripheral Bus), the simplest AMBA bus: every transfer has a **setup** phase (PSEL=1, PENABLE=0, address and "
  "data valid) followed by an **access** phase (PENABLE=1). The slave answers with PREADY (done) and optionally PSLVERR "
  "(error). Our DMA is an APB slave with zero wait states.", "j")
H("2.3 The data plane: AXI4", 2)
P("The DMA moves data over **AXI4**, the standard high-performance on-chip bus. AXI has five independent channels, each using "
  "the **VALID / READY handshake**: the sender raises VALID when its data is stable, the receiver raises READY when it can "
  "accept, and the transfer happens on the clock edge where both are 1.", "j")
T(["Channel", "Direction (for a master)", "Carries"], [
    ["AW", "master to slave", "write address, length (AWLEN), size, burst type"],
    ["W", "master to slave", "write data, byte strobes, WLAST on the final beat"],
    ["B", "slave to master", "write response (OKAY / SLVERR / DECERR)"],
    ["AR", "master to slave", "read address, length, size, burst type"],
    ["R", "slave to master", "read data, response, RLAST on the final beat"],
], [2.0, 4.6, 10.0], caption="The five AXI4 channels")
B(["**Burst**: one address phase followed by several data beats; AxLEN = beats - 1. We use 1 to 16 beats of 4 bytes (INCR bursts).",
   "**Responses**: OKAY (00), SLVERR (10, the slave failed), DECERR (11, nobody owns that address).",
   "**4 KB rule**: an AXI burst must never cross a 4096-byte boundary, so a DMA must split long transfers. This design does it automatically.",
   "**Stability rule**: once VALID is raised, address and payload must not change until READY arrives. This is asserted in the testbench."])
FIGURE("m1_soc_context.png", "Where the DMA sits: a slave on the APB control bus and a master on the AXI4 data bus.")
H("2.4 Streaming sources: valid/ready word streams", 2)
P("Sensors do not have addresses; a camera simply pushes pixels. The sensor side of this DMA is therefore a simple stream "
  "interface per channel: `s_valid`, `s_data`, `s_ready`. If the DMA cannot take a word (its FIFO is full) it lowers "
  "`s_ready` and the sensor must wait. This is called **back-pressure**, and it guarantees that no data is lost.", "j")
H("2.5 FIFOs", 2)
P("A FIFO (first in, first out) is a small queue that decouples two sides running at different speeds. Each channel has a "
  "32-word FIFO between the sensor and the burst engine, so the sensor can keep delivering while the DMA is busy serving "
  "another channel. Our FIFO is first-word-fall-through: the oldest word is always visible at the output.", "j")
H("2.6 Finite state machines (FSM)", 2)
P("Control logic in hardware is usually a finite state machine: a register holds the current state, and combinational logic "
  "decides the next state from the state and the inputs. The burst engine of this project is one FSM with ten states "
  "(chapter 7).", "j")
H("2.7 Arbitration", 2)
P("When several channels want the single memory bus at the same time, an **arbiter** decides who goes first. Common "
  "policies are fixed priority (always the most important) and round-robin (take turns). This project combines them: "
  "**fixed priority between different priorities, round-robin between equal priorities**.", "j")
H("2.8 Verification basics", 2)
T(["Method", "Idea", "In this project"], [
    ["Directed tests", "Hand-written scenarios for known features", "8 directed scenarios (registers, errors, priority, ...)"],
    ["Constrained-random", "Random but legal stimulus finds unexpected corners", "dma_random_test, 5 seeds x 40 iterations"],
    ["Scoreboard / reference model", "An independent model predicts the right answer", "Tracks every channel and checks each AXI burst"],
    ["Assertions (SVA)", "Properties that must always hold, checked every clock", "APB, AXI, arbitration and channel rules"],
    ["Functional coverage", "Measures which scenarios were exercised", "7 covergroups, 100 %"],
    ["Code coverage", "Measures which lines and branches ran", "100 % statement on all RTL modules"],
    ["Mutation checking", "Inject bugs to prove the testbench notices", "4 of 4 injected bugs caught"],
], [3.6, 6.2, 6.8], caption="Verification methods used")
P("**UVM** (Universal Verification Methodology) is the industry-standard SystemVerilog class library for such testbenches. "
  "Its building blocks are sequence items (transactions), sequences (stimulus recipes), drivers (wiggle pins), monitors "
  "(observe pins), agents (driver + monitor + sequencer for one interface), scoreboard, environment and test.", "j")
PAGEBREAK()

# ================================================================ 3
H("3. The real-world problem and the requirements", 1)
H("3.1 The scenario", 2)
T(["Sensor / source", "Data behaviour", "What matters most", "Channel / priority used"], [
    ["Front camera", "Very high bandwidth, continuous frames", "Throughput, no lost pixels", "CH0, priority 1, 16-beat bursts"],
    ["Radar", "Small bursty packets", "Latency (feeds emergency braking)", "CH1, priority 3, 4-beat bursts"],
    ["LiDAR", "Medium bandwidth point clouds", "Throughput and bounded latency", "CH2, priority 2, 8-beat bursts"],
    ["Diagnostics / logging", "Bulk memory-to-memory copies", "Must not disturb the sensors", "CH3, priority 0, 16-beat bursts"],
], [3.2, 4.4, 4.4, 4.6], caption="ADAS sensors and how they are mapped to channels")
H("3.2 The problem", 2)
B(["If the CPU copies sensor data it becomes the bottleneck: higher latency and unpredictable jitter, which a safety function cannot tolerate.",
   "If a simple DMA with a single queue is used, a long camera frame can delay a radar packet.",
   "If a memory error occurs, the system must not freeze; software must be told which channel failed and why."])
H("3.3 The solution in one sentence", 2)
BOX("Solution", ["A configurable 4-channel DMA that moves sensor data straight into memory, arbitrates every burst by "
                 "criticality, splits transfers into legal AXI bursts, isolates errors to the failing channel, and reports "
                 "everything through status registers and interrupts."])
H("3.4 Functional requirements", 2)
T(["ID", "Requirement"], [
    ["R1", "4 independent channels, each configurable as memory-to-memory or sensor-stream-to-memory."],
    ["R2", "AXI4 memory interface, 32-bit, INCR bursts of 1 to 16 beats, no burst crossing a 4 KB boundary."],
    ["R3", "Channels configured through an APB register interface."],
    ["R4", "A higher-priority channel is served first at every burst boundary."],
    ["R5", "Equal-priority channels share the bus fairly (round-robin)."],
    ["R6", "Per-channel DONE and ERR interrupts, maskable, write-1-to-clear."],
    ["R7", "An AXI error stops only the affected channel; its cause is recorded; others continue."],
    ["R8", "Illegal configurations are rejected at START with ERR_CFG and cause no bus traffic."],
    ["R9", "A channel can be restarted by software after an error."],
    ["R10", "No data is ever lost or reordered; a sensor that cannot be accepted is back-pressured."],
], [1.4, 15.2], caption="Functional requirements")
H("3.5 Mapping to the course milestones", 2)
T(["Milestone", "Where it is delivered"], [
    ["Milestone 1: requirements and architecture", "Chapters 3 to 6 of this document, docs/01 to docs/03, block diagram"],
    ["Milestone 2: RTL implementation", "Chapters 7 to 9, rtl/, RTL simulation in sim/"],
    ["Milestone 3: verification and validation", "Chapters 10 and 11, tb/, sim/report/"],
], [6.0, 10.6], caption="Milestones")
H("3.6 Scope: what is built", 2)
P("The design implements **exactly the brief**, plus four small, basic features that are needed to make it correct and useful:", "j")
B(["**Sensor-stream input with a FIFO** per channel - the brief is about camera, radar and LiDAR data;",
   "**Round-robin between equal priorities** - fair sharing for channels of the same importance;",
   "**Automatic 4 KB burst splitting** - required by the AXI protocol;",
   "**Illegal-configuration detection** - part of reliable error handling."])
P("More advanced options (anti-starvation aging, continuous/ring mode, bus watchdog, abort, performance counters) are "
  "deliberately not included; they are listed as future work in section 14.4.", "j")
PAGEBREAK()

# ================================================================ 4
H("4. The project flow, phase by phase", 1)
P("This chapter is the roadmap: the order in which the project was built and why each step comes before the next.", "j")
T(["Phase", "Activity", "Output", "Exit criterion"], [
    ["0", "Understand the problem, check the tools", "Vivado xsim, UVM and synthesis available", "Simulator compiling"],
    ["1", "Requirements and architecture: modules, registers, arbitration scheme, FSM, block diagram", "docs/01 to 03, block diagram", "Every requirement has an owner module"],
    ["2", "RTL: package, FIFO, channel, arbiter, engine, top", "rtl/*.sv", "Compiles with no errors"],
    ["3", "Testbench infrastructure: interfaces, agents, memory model, scoreboard", "tb/if, tb/uvm", "First smoke test passes"],
    ["4", "Scenario tests: 9 virtual sequences", "8 directed tests plus random", "All pass, scoreboard checking real data"],
    ["5", "Assertions: bound SVA for APB, AXI, arbiter, channel", "tb/sva", "No assertion failures"],
    ["6", "Prove the checkers work: inject RTL bugs (mutation)", "4 mutants, 4 caught", "Each bug caught by its test"],
    ["7", "Coverage: covergroups and code coverage, merge, report, close holes", "sim/report", "Functional 100 %, statement 100 %"],
    ["8", "Synthesis: utilization and timing, fix RTL where needed", "synth/", "No timing violation at 100 MHz"],
    ["9", "Final regression, documentation", "README, docs, reports", "13 of 13 runs pass after the last RTL change"],
], [1.2, 6.6, 4.4, 4.4], caption="Project phases")
BOX("Important lesson of the flow", ["Synthesis exposed a timing problem and a memory-inference problem, which forced RTL changes "
    "(chapter 13). After any RTL change the whole regression must be run again; the final result is a regression that passes "
    "after the last change."])
PAGEBREAK()

# ================================================================ 5
H("5. Architecture", 1)
P("This chapter answers: how is the problem divided into hardware blocks, and how do the blocks talk to each other?", "j")
H("5.1 Top-level view", 2)
T(["Interface", "Signals", "Role"], [
    ["Clock / reset", "clk, rst_n (async, active low)", "Single clock domain"],
    ["APB slave", "psel penable pwrite paddr[11:0] pwdata prdata pready pslverr", "CPU programs and monitors the DMA"],
    ["Sensor streams (x4)", "s_valid[3:0] s_data[3:0][31:0] s_ready[3:0]", "Camera, radar, LiDAR, spare input"],
    ["AXI4 master", "aw* w* b* ar* r* (32-bit address and data)", "Reads and writes memory"],
    ["Interrupts", "irq_ch[3:0], irq", "Tell the CPU something happened"],
], [3.2, 7.6, 5.8], caption="dma_top interfaces")
FIGURE("block_diagram.png", "RTL block diagram of the ADAS multi-channel DMA subsystem.")
H("5.2 Module hierarchy", 2)
FIGURE("m1_hierarchy.png", "Module hierarchy.")
T(["Module", "Responsibility", "Does NOT do"], [
    ["dma_channel", "Holds one channel's registers and progress; decides whether it wants a burst and how big; updates itself after every burst", "Talk to AXI, decide who wins the bus"],
    ["dma_arbiter", "Picks the winning channel among those requesting", "Know about addresses or data"],
    ["dma_engine", "Executes one burst at a time on AXI; collects data; reports the result back", "Know the transfer length or priorities"],
    ["dma_top", "Register address decode, global control, wiring, irq OR", "Any data movement"],
], [3.0, 8.6, 5.0], caption="Who does what")
P("The channel owns the **what**, the arbiter owns the **who**, and the engine owns the **how**. The arbitration policy can be "
  "changed without touching the bus logic, and the bus logic works for any number of channels.", "j")
H("5.3 Data path", 2)
FIGURE("m1_datapath.png", "Store-and-forward datapath through one 16-word burst buffer.")
P("**Why store-and-forward?** A write burst on AXI must keep WVALID/WDATA flowing; if the data came straight from a slow read, "
  "the write could stall half-way. By collecting the whole burst first, the write phase is simple and always legal. The price "
  "is one burst of latency, which is why bursts are limited to 16 beats and the burst length is programmable per channel "
  "(the radar uses short bursts for low latency).", "j")
H("5.4 Control path", 2)
FIGURE("m1_controller.png", "Control path: channels request, the arbiter grants, the engine runs the burst and reports back.")
N(["Software writes START in a channel's CTRL register.",
   "The channel requests when it is active and enabled, the global enable is on, and (for sensor channels) the FIFO holds enough words for the next burst.",
   "All requesting channels present their priority to the arbiter, which picks one.",
   "The engine accepts the grant, copies that channel's burst parameters, runs the burst on AXI and reports how many words moved and with what status.",
   "The channel updates its addresses and remaining count and either requests the next burst, finishes (DONE interrupt), or stops with an error (ERR interrupt)."])
H("5.5 Design decisions and trade-offs", 2)
T(["Decision", "Alternative", "Why this choice"], [
    ["One shared engine", "One engine per channel", "Much smaller; the bus is shared anyway"],
    ["Arbitrate per burst (max 16 beats)", "Arbitrate per transfer", "A critical channel waits at most one burst of anybody else"],
    ["Store-and-forward burst buffer", "Cut-through", "Simple, always protocol-legal; latency bounded by burst size"],
    ["Single outstanding burst", "Pipelined reads and writes", "Far simpler to verify; throughput limit documented"],
    ["Registers, not memory descriptors", "Scatter-gather descriptors", "Meets the brief; descriptors are future work"],
    ["APB for control", "AXI-Lite", "Simplest standard bus, ideal for slow configuration traffic"],
], [4.6, 4.2, 7.8], caption="Design decisions")
PAGEBREAK()

# ================================================================ 6
H("6. Register map and the software view", 1)
H("6.1 Address map", 2)
P("Addresses are 12 bits. Global registers live at 0x000 to 0x00C. Each channel owns a 0x40-byte window starting at 0x100: "
  "CH0 at 0x100, CH1 at 0x140, CH2 at 0x180, CH3 at 0x1C0. Any other address, or a word offset above 8 inside a channel "
  "window, returns PSLVERR.", "j")
FIGURE("m1_address_map.png", "APB address map.")
H("6.2 Global registers", 2)
T(["Offset", "Name", "Access", "Meaning"], [
    ["0x000", "GCTRL", "RW", "bit 0 EN (global enable)"],
    ["0x004", "GSTAT", "RO", "bits 3:0 channel active; bit 8 engine busy"],
    ["0x008", "IRQ_SUM", "RO", "bits 3:0 the four channel irq lines"],
    ["0x00C", "VERSION", "RO", "0x00010000"],
], [1.8, 2.4, 1.6, 10.8], caption="Global registers")
H("6.3 Channel registers (offset from the channel base)", 2)
T(["Offset", "Name", "Access", "Meaning"], [
    ["+0x00", "CTRL", "RW", "bit 0 EN; bit 1 START (pulse); bit 2 SRC_STREAM (1 = sensor, 0 = memory); bits 5:4 PRIO (3 = most critical); bits 11:8 BLEN (beats minus 1)"],
    ["+0x04", "SRC", "RW", "source byte address (word aligned; ignored for sensor streams)"],
    ["+0x08", "DST", "RW", "destination byte address (word aligned)"],
    ["+0x0C", "LEN", "RW", "length in words, 24 bits (1 to 16 M words)"],
    ["+0x10", "INT_EN", "RW", "bit 0 DONE, bit 1 ERR interrupt enables"],
    ["+0x14", "INT_STAT", "RW1C", "bit 0 DONE, bit 1 ERR; writing 1 clears"],
    ["+0x18", "STATUS", "RO", "bit 0 ACTIVE; bit 1 IN_FLIGHT; bits 4:2 ERR_CODE; bits 13:8 FIFO level"],
    ["+0x1C", "REMAIN", "RO", "words left in the current transfer"],
    ["+0x20", "XFERRED", "RO", "words moved since the last START"],
], [1.8, 2.4, 1.6, 10.8], caption="Channel registers")
P("**ERR_CODE values:** 0 none, 1 SLVERR, 2 DECERR, 3 illegal configuration.")
FIGURE("m1_ctrl_bits.png", "Bit fields of CTRL, STATUS and INT_STAT.")
H("6.4 What the hardware enforces", 2)
B(["START while a channel is already active is ignored.",
   "START with EN = 0, LEN = 0, an unaligned DST, or an unaligned SRC (memory source) sets INT_STAT.ERR and ERR_CODE = 3, and does nothing else (no bus traffic).",
   "A new START clears ERR_CODE and XFERRED and flushes the channel's FIFO.",
   "INT_STAT is write-1-to-clear. If a new event occurs in the same cycle as the clear, the new event wins (it is never lost)."])
H("6.5 Programming sequence (what a driver does)", 2)
CODE("""write(GCTRL,  1);                 // enable the DMA
// radar: sensor stream, priority 3, 4-beat bursts, 256 words
write(CH1_DST,    0x80100000);
write(CH1_LEN,    256);
write(CH1_INT_EN, 0b11);          // DONE | ERR
write(CH1_CTRL,   (3<<8)|(3<<4)|(1<<2)|(1<<1)|1);  // BLEN=3 PRIO=3 STREAM START EN
// ... interrupt arrives ...
st = read(CH1_INT_STAT);  write(CH1_INT_STAT, st);  // acknowledge
if (st & ERR) code = (read(CH1_STATUS) >> 2) & 7;   // why did it fail""", "Driver view")
PAGEBREAK()

# ================================================================ 7
H("7. RTL deep dive, module by module", 1)
P("This chapter walks through the implementation in rtl/, in the order that is easiest to understand: package, FIFO, channel, "
  "arbiter, engine, top.", "j")
T(["File", "Lines", "Content"], [
    ["dma_pkg.sv", "54", "parameters, error codes, register offsets, AXI constants"],
    ["dma_sfifo.sv", "44", "32-word sensor FIFO"],
    ["dma_channel.sv", "199", "channel registers, context, burst sizing, request, interrupts"],
    ["dma_arbiter.sv", "47", "priority + round-robin arbiter"],
    ["dma_engine.sv", "173", "burst FSM, burst buffer, AXI4 master"],
    ["dma_top.sv", "169", "APB decode, global registers, wiring"],
], [3.4, 1.6, 11.6], caption="RTL files")
H("7.1 dma_pkg.sv: constants shared by everything", 2)
P("The package holds the compile-time parameters (N_CH = 4, DATA_W = 32, MAX_BEATS = 16, FIFO_DEPTH = 32, LEN_W = 24), the "
  "error-code enumeration (ERR_NONE, ERR_SLVERR, ERR_DECERR, ERR_CFG), the interrupt bit positions (DONE, ERR), the register "
  "offsets and the AXI response codes. Changing N_CH or FIFO_DEPTH here reconfigures the whole subsystem.", "j")
H("7.2 dma_sfifo.sv: the sensor FIFO", 2)
B(["Depth 32 words, width 32 bits, write pointer, read pointer and a 6-bit count (0 to 32); full = (count == DEPTH).",
   "First-word-fall-through: rdata = mem[rptr] is always the oldest word, so the engine can use it in the same cycle it pops.",
   "flush resets the pointers and count, used on START so no stale words from an earlier run remain.",
   "The storage array is written in an always_ff block **without reset**, so the FPGA tool maps it to cheap LUT-RAM instead of 1024 flip-flops (chapter 13)."])
H("7.3 dma_channel.sv: the heart of one channel", 2)
FIGURE("m2_channel_internal.png", "Inside one channel.")
T(["Group", "Registers", "Written by"], [
    ["Configuration", "en, src_stream, prio, blen, src_base, dst_base, len, int_en", "Software (APB)"],
    ["Run-time context", "active, cur_src, cur_dst, remaining, err_code, xferred", "Hardware (START and burst completion)"],
    ["Interrupt status", "int_stat[1:0]", "Hardware sets, software clears (W1C)"],
], [3.4, 8.2, 5.0], caption="Channel state")
H("START handling", 3)
CODE("""cfg_bad   = !new_en || (len == 0) || (dst_base[1:0] != 0)
            || (!new_strm && src_base[1:0] != 0);
start_ok  = start_w && !active && !cfg_bad;    // begin the transfer
start_bad = start_w && !active &&  cfg_bad;    // set ERR_CFG, do nothing else""")
P("On start_ok the context is loaded: active = 1, cur_src = src_base, cur_dst = dst_base, remaining = len, error code "
  "cleared, xferred = 0, and the FIFO flushed.", "j")
H("Sensor side", 3)
P("`s_ready = active && src_stream && !fifo_full`. The sensor is accepted only while a sensor transfer is running. When the "
  "FIFO is full, s_ready drops and the sensor waits (back-pressure), so no word is ever lost (R10).", "j")
H("Deciding the next burst size", 3)
CODE("""beats = min( blen+1,                       // programmed burst length
             remaining,                    // words left in the transfer
             words left in dst 4KB page,   // 4KB rule (write side)
             words left in src 4KB page )  // 4KB rule (read side, memory source only)""")
P("All terms are saturated to 6 bits (a value above 32 is irrelevant because the maximum burst is 16), which keeps the "
  "comparison logic tiny. Words left in a page come from address bits [11:2].", "j")
H("Request generation (registered)", 3)
P("`req_q` and `nb_q` (next beats) are registers computed from the context every cycle. The output is "
  "`req = req_q && gl_en && en && active`. For sensor channels req_q also requires `fifo_count >= beats`, so the engine "
  "never starts a burst it cannot finish. Registering the request was a timing fix found during synthesis.", "j")
H("Burst completion (upd)", 3)
B(["Addresses advance by beats x 4, remaining -= beats, xferred += beats.",
   "If upd_err != 0: the channel goes inactive, err_code is stored, ERR is set (R7).",
   "Else if remaining reached 0: DONE is set and the channel goes inactive."])
H("Interrupt logic", 3)
P("`int_set = {error_or_cfgbad, done_now}`; `int_stat <= (int_stat & ~w1c_mask) | int_set`, so a new event always wins "
  "over a simultaneous clear; `irq = |(int_stat & int_en)`.", "j")
FIGURE("m2_channel_fsm.png", "Channel life-cycle.")
H("7.4 dma_arbiter.sv: priority and round-robin", 2)
FIGURE("m2_arbiter_hw.png", "Arbiter structure.")
B(["The arbiter takes the four req bits and the four 2-bit priorities.",
   "**Winner**: scan the channels starting from the round-robin pointer; a channel replaces the current best only if its priority is **strictly higher**. So the highest priority always wins, and among equal priorities the first one after the pointer wins.",
   "**After a grant** (grant_fire): the round-robin pointer moves to winner + 1."])
BOX("Why this meets the requirements", ["Strict priority between different priorities satisfies R4. The round-robin pointer "
    "satisfies R5. Because decisions are made once per burst, the critical channel waits at most one burst."])
FIGURE("wave_priority.png", "dma_priority_test: four channels with priorities 3, 2, 1, 0 are granted in that order.")
FIGURE("wave_roundrobin.png", "dma_priority_test: four channels with equal priority - grants rotate 1, 2, 3, 0, ...")
H("7.5 dma_engine.sv: the burst FSM and AXI master", 2)
FIGURE("m2_engine_fsm.png", "The ten-state burst FSM.")
T(["State", "What happens", "Leaves when"], [
    ["IDLE", "Waits for a valid grant; remembers the winner", "grant valid"],
    ["LATCH", "Copies burst size, source and destination address of the winner; clears counters and error", "next cycle"],
    ["RD_AR", "Drives ARVALID with the read address and length", "ARREADY"],
    ["RD_DATA", "RREADY = 1; stores each R beat in the burst buffer; remembers the first non-OKAY response", "RVALID and RLAST"],
    ["STR_RD", "(sensor source) pops one FIFO word per cycle into the burst buffer", "all beats popped"],
    ["WR_AW", "Drives AWVALID with the write address and length", "AWREADY"],
    ["WR_W", "Drives WVALID / WDATA / WLAST from the buffer", "last beat accepted"],
    ["WR_B", "BREADY = 1, waits for the write response", "BVALID"],
    ["UPD", "Tells the channel how many words moved and the error code (0 beats on error)", "next cycle"],
    ["SETTLE", "One idle cycle so the channel's registered request reflects the update", "next cycle"],
], [2.2, 10.4, 4.0], caption="Engine states")
P("Constant AXI attributes: size = 2 (4 bytes), burst = 01 (INCR), wstrb = 1111; awlen = arlen = beats - 1; wlast is high "
  "on the last beat.", "j")
H("Error handling in the engine", 3)
P("Responses are mapped by `resp2err`: SLVERR to ERR_SLVERR, DECERR to ERR_DECERR; the first error is kept. After a read "
  "error the engine still consumes all read beats until RLAST (the protocol requires it) but skips the write phase, so no "
  "corrupted data reaches memory.", "j")
FIGURE("wave_axi_burst.png", "dma_smoke_test: one memory-to-memory burst - AXI read burst, then write burst and B response.")
H("7.6 dma_top.sv: glue and global control", 2)
B(["APB decode: an access is psel && penable; pready is tied high (zero wait states); pslverr for any address that is neither a global register nor a valid channel word.",
   "Channel window decode: ch_off = paddr - 0x100, channel = ch_off[9:6], word = ch_off[5:2].",
   "Global registers: GCTRL (enable), GSTAT, IRQ_SUM, VERSION.",
   "Read mux: global register or the selected channel's read data.",
   "Wiring: per-channel arrays (req, prio, next_beats, addresses, FIFO heads) connect the channels to the arbiter and engine; irq = |irq_ch."])
PAGEBREAK()

# ================================================================ 8
H("8. Worked examples: what really happens, step by step", 1)
H("8.1 Example 1: memory-to-memory copy of 20 words", 2)
P("Software programs channel 0: SRC = 0x0001_0000, DST = 0x0010_0000, LEN = 20, BLEN = 15 (16-beat bursts), priority 1, "
  "interrupts DONE + ERR, then writes START.", "j")
T(["Step", "Who", "What happens"], [
    ["1", "APB", "Five register writes (SRC, DST, LEN, INT_EN, CTRL with START and EN). On the CTRL write start_ok is true."],
    ["2", "Channel", "active = 1, remaining = 20, cur_src = 0x10000, cur_dst = 0x100000. Next cycle next_beats = min(16, 20, 1024, 1024) = 16 and req_q goes high."],
    ["3", "Arbiter", "Only channel 0 requests, so it wins; grant_fire pulses."],
    ["4", "Engine", "IDLE to LATCH: captures beats = 16, rd_addr = 0x10000, wr_addr = 0x100000."],
    ["5", "AXI read", "RD_AR: ARADDR = 0x10000, ARLEN = 15; 16 R beats are stored in the burst buffer; RLAST ends the phase."],
    ["6", "AXI write", "WR_AW (AWADDR = 0x100000, AWLEN = 15), WR_W streams 16 beats with WLAST on the 16th, WR_B waits for BRESP = OKAY."],
    ["7", "Engine to channel", "UPD: upd_beats = 16. Channel: cur_src = 0x10040, cur_dst = 0x100040, remaining = 4, xferred = 16."],
    ["8", "Second burst", "SETTLE, IDLE; the channel requests again with next_beats = min(16, 4) = 4. Same sequence with 4 beats."],
    ["9", "Finish", "Second UPD: remaining == upd_beats, so INT_STAT.DONE = 1, active = 0; irq_ch[0] rises."],
    ["10", "Software", "The interrupt handler reads INT_STAT (= 1), writes 1 to clear it, reads XFERRED (= 20)."],
], [1.2, 3.0, 12.4], caption="Memory-to-memory copy, cycle by cycle")
H("8.2 Example 2: sensor stream (radar, 8 words, 4-beat bursts)", 2)
N(["Software sets SRC_STREAM = 1, BLEN = 3, LEN = 8, priority 3 and START. The channel becomes active, its FIFO is flushed and s_ready goes high.",
   "The radar pushes words with s_valid; each accepted word goes into the 32-word FIFO.",
   "As soon as the FIFO holds 4 words, req_q goes high. The arbiter grants (priority 3 wins over everything).",
   "The engine goes LATCH to STR_RD and pops 4 words, one per cycle, into the burst buffer. There is no read address phase because the source is not memory.",
   "WR_AW, WR_W, WR_B write the 4 words to DST .. DST + 12.",
   "The second 4 words follow the same way; DONE is set after the second burst.",
   "If the memory is slow, the FIFO fills; when it is full s_ready drops and the radar simply waits (back-pressure) - nothing is lost."])
FIGURE("wave_sensor_stream.png", "dma_smoke_test: sensor stream on channel 1 drained as 8-beat AXI write bursts; irq_ch[1] rises at the end.")
H("8.3 Example 3: a transfer that crosses a 4 KB page", 2)
P("DST = 0x0010_0FF0, LEN = 20, BLEN = 15. The page ends at 0x0010_1000, which is 0x10 bytes (4 words) away.", "j")
T(["Burst", "Computation", "Result"], [
    ["1", "min(16, remaining 20, room in page = (4096 - 0xFF0) / 4 = 4)", "4 beats, ends exactly on the boundary"],
    ["2", "dst = 0x0010_1000, room = 1024; min(16, remaining 16, 1024)", "16 beats"],
], [1.4, 9.8, 5.4], caption="4 KB split")
P("Without the split, burst 1 would have been 16 beats from 0x0010_0FF0 and crossed the page boundary - an AXI violation. "
  "The assertions a_aw_4k / a_ar_4k and the scoreboard check this on every burst.", "j")
H("8.4 Example 4: arbitration", 2)
FIGURE("m1_arb_example.png", "Top: different priorities are served strictly in priority order. Bottom: equal priorities take turns.")
T(["Situation", "Sequence of winners", "Outcome"], [
    ["CH3 (priority 3, 512 words = 32 bursts) and CH0 (priority 0, 64 words = 4 bursts) start together", "CH3 wins every round until its 32 bursts are done, then CH0 runs", "CH3 finishes first (strict priority)"],
    ["Four channels, all priority 2, 64 words each", "1, 2, 3, 0, 1, 2, 3, 0, ... (16 grants)", "Every 4 consecutive grants serve all 4 channels"],
], [5.6, 6.0, 5.0], caption="Arbitration examples (both checked automatically by dma_priority_test)")
PAGEBREAK()

# ================================================================ 9
H("9. Key features in detail", 1)
H("9.1 Priority arbitration per burst", 2)
P("Each channel has a 2-bit priority. Arbitration happens at every burst boundary, never in the middle of a burst, so the "
  "highest-priority channel waits at most one burst (at most 16 beats) of another channel. In the ADAS scenario this makes "
  "the radar finish first even while the camera moves thousands of words.", "j")
H("9.2 Round-robin between equal priorities", 2)
P("A 2-bit pointer remembers the last winner; the next tie goes to the channel after it. This costs only one small register "
  "and guarantees fair sharing between channels that software marked as equally important.", "j")
H("9.3 Automatic 4 KB burst splitting", 2)
P("AXI forbids a burst that crosses a 4 KB boundary because the two halves could belong to different slaves. The channel "
  "computes the words left in the current page for source and destination and shortens the burst accordingly. After the "
  "short burst the address is page-aligned, so later bursts are full size. This is transparent to software.", "j")
H("9.4 Error isolation and restart", 2)
P("AXI errors are tracked per burst. A failing read or write stops only the channel that owned that burst and records the "
  "cause in ERR_CODE; the other channels remain active and finish correctly. After the fault is fixed, software simply "
  "programs the channel again and writes START. This is verified by the error test, where three channels fail in different "
  "ways while the fourth must complete normally, followed by a successful restart of the failed channels.", "j")
H("9.5 Illegal-configuration detection", 2)
P("Mistakes that would corrupt memory are caught before anything starts: zero length, unaligned addresses and START without "
  "enable. The result is an ERR interrupt with ERR_CODE = 3 and zero bus traffic. A later legal START clears the error.", "j")
H("9.6 Sensor back-pressure", 2)
P("When memory is slower than the sensors, each channel's FIFO fills and s_ready drops, so the sensor holds its data until "
  "there is room. In the back-pressure test the FIFOs were full for 12 561 cycles and still every word arrived in memory, "
  "in order.", "j")
PAGEBREAK()

# ================================================================ 10
H("10. The verification environment (UVM) in detail", 1)
P("Verification answers one question: how do we know the design is correct? The answer here is a self-checking UVM "
  "environment that drives realistic stimulus on every interface, predicts the correct result independently of the RTL, "
  "and compares.", "j")
H("10.1 Structure", 2)
FIGURE("m3_tb_arch.png", "Testbench top level.")
FIGURE("m3_uvm.png", "UVM environment.")
H("10.2 Interfaces (tb/if/dma_ifs.sv)", 2)
T(["Interface", "Purpose", "Notes"], [
    ["apb_if", "APB signals", "Driver clocking block and monitor clocking block"],
    ["axi_if", "AXI signals", "Slave-side clocking block for the responder, monitor clocking block"],
    ["strm_if", "One sensor stream", "One instance per channel (array of four)"],
    ["dbg_if", "DUT-internal probes: requests, priorities, grant, interrupts, FIFO levels", "Connected by hierarchical references in tb_top; passive"],
], [2.6, 7.0, 7.0], caption="Interfaces")
P("Clocking blocks (`default input #1step output #1`) make the testbench sample just before the clock edge and drive "
  "slightly after it, which avoids race conditions with the RTL.", "j")
H("10.3 APB agent", 2)
B(["**apb_item**: write, addr, data, delay (random idle cycles), and result fields rdata, slverr.",
   "**apb_driver**: real APB timing - setup phase, access phase, waits for PREADY, captures prdata and pslverr.",
   "**apb_monitor**: builds an item for every completed access and broadcasts it to the scoreboard and coverage."])
H("10.4 Sensor-stream agent (four instances)", 2)
B(["**strm_item**: number of words, gap_pct (probability of a pause between words, models bursty sensors), start_delay, random data.",
   "**strm_driver**: offers one word at a time with VALID, holds it until READY, with random gaps (radar 30 %, camera 0 %).",
   "**strm_monitor**: reports every accepted word, and every cycle where VALID was high but READY low (back-pressure, for coverage)."])
H("10.5 AXI memory-slave agent", 2)
B(["**axi_mem**: associative-array memory with a deterministic pattern for untouched words and a fill_random() back-door.",
   "**axi_slave_cfg**: READY percentages, read latency, gaps between read beats, write response latency, error regions (SLVERR or DECERR on read, write or both); presets set_fast(), set_slow(), set_random().",
   "**axi_slave_driver**: reactive responder for AR, AW, W, R and B with randomized timing; self-checks WLAST position.",
   "**axi_monitor**: reconstructs complete bursts (address, length, data, response) and publishes them; counts bursts so tests can prove that no bus traffic happened."])
H("10.6 Arbitration monitor", 2)
P("Every time the DUT fires a grant, this monitor samples the request vector, the priorities and the winner and publishes "
  "an arb_item. The scoreboard keeps win statistics and the coverage collector uses it for the arbitration covergroup.", "j")
H("10.7 Scoreboard: the independent reference model", 2)
FIGURE("m3_scoreboard.png", "Scoreboard structure and checks.")
P("The scoreboard never looks inside the DUT's registers. It builds its own model of each channel only from the APB writes "
  "it observes and then checks the bus.", "j")
T(["Check", "How"], [
    ["Address sequence", "Burst start address equals base + 4 x words already done"],
    ["Burst length", "Re-computes min(BLEN+1, remaining, words to 4 KB page on destination and source) independently and compares"],
    ["Data integrity", "Memory source: each written word equals the snapshot taken at START. Sensor source: each written word equals the sensor word with the same index, in order. A word the sensor never sent, or beyond LEN, is an error"],
    ["Stray traffic", "A burst whose address is in no programmed window is an error"],
    ["Interrupt sanity", "DONE requires that all words were written; ERR requires an injected error or an illegal configuration"],
    ["Completeness", "At end of test every non-failed channel must have moved all its words"],
], [3.4, 13.2], caption="What is checked for every AXI burst")
H("10.8 Functional coverage collector", 2)
P("Subscribes to the APB, AXI, stream and arbitration monitors and samples seven covergroups (chapter 11). Coverage answers "
  "'did we actually test it?', complementing the scoreboard's 'was it correct?'.", "j")
H("10.9 Virtual sequencer and sequences", 2)
FIGURE("m3_seq_flow.png", "How one stimulus flows through the environment.")
T(["Helper", "Purpose"], [
    ["wr(addr, data), rd(addr)", "One APB access through the APB sequencer"],
    ["cfg_ch(...)", "Program SRC, DST, LEN, INT_EN and CTRL (with START) for a channel"],
    ["wait_irq, ack_irq, wait_done", "Wait for the interrupt line, read and clear INT_STAT, accumulate status until DONE or ERR"],
    ["send_stream, send_stream_bg", "Send sensor words on a channel (blocking or in the background)"],
    ["gl_enable, expect32, check", "Global enable and self-checking helpers that raise UVM errors"],
], [5.0, 11.6], caption="Driver-software helpers in the base virtual sequence")
H("10.10 Tests", 2)
P("A base test builds the environment, waits for reset, starts one virtual sequence, waits a short drain time and prints "
  "`*** TEST PASSED ***` or `*** TEST FAILED ***` from the UVM error and fatal counts. Each scenario is a thin class created by "
  "a macro. A global 200 ms timeout protects against hangs.", "j")
H("10.11 tb_top and the assertion bind", 2)
P("tb_top generates a 100 MHz clock and a 10-cycle reset, instantiates the DUT and interfaces, connects the debug probes, "
  "stores the virtual interfaces in the UVM configuration database and calls run_test(). Two bind statements attach the "
  "assertion modules without modifying the RTL:", "j")
CODE("""bind dma_top     dma_sva    u_sva    (.*);
bind dma_channel dma_ch_sva u_ch_sva (.*);""")
PAGEBREAK()

# ================================================================ 11
H("11. Assertions, coverage, tests and results", 1)
H("11.1 Assertions (SystemVerilog Assertions)", 2)
FIGURE("m3_assert_map.png", "Assertion groups.")
T(["Group", "Rules checked"], [
    ["APB protocol", "Access phase follows setup; PADDR / PWRITE / PWDATA stable during setup; PREADY in access phase; PSLVERR only in access phase"],
    ["AXI handshake stability", "AW, AR and W payload stay stable while VALID is high and READY is low"],
    ["AXI legality", "Size 4 bytes, INCR, aligned, at most 16 beats; no burst crosses 4 KB (read and write); WLAST on exactly the last beat; only one AXI phase active at a time"],
    ["Arbitration", "Grant only to a requesting channel; the winner has the highest priority (one instance per channel); fire implies a valid grant"],
    ["Channel (4 instances)", "Sensor accepted only while a sensor transfer is active; no FIFO underflow or overflow; completion only for the channel in flight; requests only from an enabled active channel; irq == |(INT_STAT & INT_EN); an illegal START never activates the channel; next burst size 1..16"],
    ["Interrupts", "Global irq equals the OR of the channel irqs"],
], [4.0, 12.6], caption="25 properties, 52 instances")
BOX("Tool note", ["xsim 2025.2 ignores `cover property`; the cover statements stay in the source as documentation and the "
                  "same scenarios are measured by the covergroups below."])
H("11.2 Functional coverage", 2)
T(["Covergroup", "What it measures"], [
    ["cg_cfg", "Channel x mode (memory/sensor) x priority x burst length x transfer length, with crosses"],
    ["cg_axi", "Direction x burst length x response (OKAY/SLVERR/DECERR) x burst ending on a 4 KB boundary"],
    ["cg_arb", "Number of simultaneous requesters x winner; winner priority x best competing priority"],
    ["cg_irq", "Channel x interrupt cause seen by software (DONE, ERR)"],
    ["cg_err", "Channel x error code (none, SLVERR, DECERR, illegal configuration)"],
    ["cg_sensor", "Channel x sensor word accepted versus back-pressured"],
    ["cg_apb", "Register region (global, channel, unmapped) x read/write x PSLVERR"],
], [2.6, 14.0], caption="Covergroups")
P("Coverage-driven closure was used: stimulus was added wherever a bin stayed empty (for example a 4 608-word camera frame "
  "for the longest-length bin, a 4 x 4 error matrix so every channel sees every error type). The final merged functional "
  "coverage is **100 %**.", "j")
H("11.3 The nine scenarios (tests)", 2)
T(["Test", "What it does", "What it proves"], [
    ["dma_regs_test", "Reset values, read/write and read-only behaviour, 24-bit LEN mask, unmapped addresses, write-1-to-clear, irq lines", "Register specification"],
    ["dma_smoke_test", "One memory copy and one sensor transfer", "Bring-up works"],
    ["dma_sensor_fusion_test", "The ADAS case: camera 4608, radar 256 (bursty), LiDAR 1024, diagnostics 512 words all at once", "All data correct; radar finishes first"],
    ["dma_burst_sweep_test", "Every BLEN 0 to 15, random lengths, addresses just below a 4 KB page", "Burst partitioning and 4 KB rule"],
    ["dma_priority_test", "Priorities 3,2,1,0 together; long high-priority vs short low-priority; four equal priorities", "Priority order and round-robin rotation"],
    ["dma_error_test", "SLVERR read, DECERR write, SLVERR on a sensor channel while a healthy channel runs; recovery; 4 channels x 4 error kinds", "Error codes, isolation, restart"],
    ["dma_cfg_err_test", "Zero length, unaligned source and destination, START without EN, START while busy", "No bus traffic, ERR_CFG, busy START ignored"],
    ["dma_backpressure_test", "Very slow memory, three fast sensors", "FIFOs fill, sensors wait, no data lost"],
    ["dma_random_test", "Random channels, modes, sizes, burst lengths, priorities, memory timing, sensor gaps", "Corner cases nobody thought of"],
], [3.8, 7.8, 5.0], caption="Test scenarios")
H("11.4 Constrained-random testing", 2)
P("Each iteration of the random test randomizes the memory personality (fast, or random latencies and READY percentages), "
  "chooses which channels run (about 80 % each), their mode (about 60 % sensor), length (often tiny, sometimes up to 300 "
  "words), burst length 1 to 16, priority, sensor gaps and start addresses (one third of the time aimed at a 4 KB boundary). "
  "All active channels are configured with the DMA disabled and then released together so they compete at once. The "
  "regression runs five seeds of 40 iterations; one random run performs about 20 000 scoreboard checks on about 3 500 write "
  "bursts.", "j")
H("11.5 Mutation check: does the testbench really catch bugs?", 2)
P("A testbench that passes proves little unless it can also fail. Four bugs were injected into a copy of the final RTL, one "
  "at a time; each made its test fail:", "j")
T(["Injected bug", "Test", "Detected by"], [
    ["A data bit flipped on beat 5 of every burst", "dma_smoke_test", "Scoreboard DATA MISMATCH word 5"],
    ["Arbiter ignores priority", "dma_priority_test", "Wrong completion order"],
    ["4 KB splitting removed", "dma_burst_sweep_test", "Scoreboard burst-length check"],
    ["DECERR reported as SLVERR", "dma_error_test", "Wrong error code (1 instead of 2)"],
], [6.0, 4.0, 6.6], caption="Mutation check")
H("11.6 Results", 2)
T(["Metric", "Result"], [
    ["Regression", "13 of 13 runs pass (8 directed tests + random with 5 seeds), 0 UVM errors, 0 assertion failures"],
    ["Functional coverage (merged)", "100 %"],
    ["Checks per random run", "About 20 000 scoreboard checks and 3 000 - 3 800 write bursts"],
], [5.0, 11.6], caption="Results")
T(["Module", "Statement", "Branch", "Condition", "Toggle"], [
    ["dma_top", "100", "94.1", "83.3", "71.6"], ["dma_channel", "100", "100", "97.2", "54.6"],
    ["dma_sfifo", "100", "100", "100", "99.5"], ["dma_arbiter", "100", "100", "100", "100"],
    ["dma_engine", "100", "100", "97.9", "92.0"],
], [4.6, 3.0, 3.0, 3.0, 3.0], caption="Code coverage of the RTL (percent)")
P("Toggle coverage is lower in dma_top and dma_channel because the upper bits of the 32-bit address and length registers "
  "never change in a small simulated memory. This is expected and not a functional gap.", "j")
FIGURE("regression.png", "Regression results of the final run.", 13.0)
FIGURE("m3_cov_chart.png", "Functional coverage per covergroup.")
FIGURE("cov_functional.png", "Merged functional coverage report (Vivado xcrg).")
FIGURE("cov_code.png", "Code coverage per module (Vivado xcrg).")
PAGEBREAK()

# ================================================================ 12
H("12. How to run the flow", 1)
H("12.1 Tools", 2)
P("Vivado 2025.2 provides everything: xvlog (compile), xelab (elaborate), xsim (simulate, with the built-in UVM 1.2 "
  "library), xcrg (coverage reports) and vivado (synthesis).", "j")
H("12.2 Commands", 2)
T(["Action", "Windows", "Git Bash"], [
    ["Everything (build, all tests, coverage)", "sim\\regress.bat", "sim/regress.sh"],
    ["Build only", "sim\\build.bat", "sim/build.sh"],
    ["One test", "sim\\run_test.bat dma_sensor_fusion_test", "sim/run_test.sh dma_random_test 42 100"],
    ["Coverage reports", "sim\\coverage_report.bat", "sim/coverage_report.sh"],
    ["Synthesis", "cd synth, then vivado -mode batch -source synth.tcl", "same"],
], [5.0, 6.0, 5.6], caption="Commands")
P("Arguments of run_test: test name, random seed, number of random iterations. The Vivado path is set in sim/env.bat (and "
  "at the top of the .sh files).", "j")
FIGURE("m2_sim_flow.png", "Simulation and regression flow.")
H("12.3 What the scripts do", 2)
B(["**build**: compiles the RTL, interfaces, assertions, UVM package and tb_top with `xvlog -sv -L uvm`, then elaborates with xelab including code-coverage instrumentation.",
   "**run_test**: writes the plusargs (test name, iterations, seed, log file, coverage database name) into an arguments file and runs xsim, then prints the PASSED or FAILED line. (An arguments file is used because the Vivado batch wrapper splits arguments at the equals sign.)",
   "**regress**: build, then 8 directed tests, then the random test with 5 seeds, then the coverage report.",
   "**coverage_report**: merges the functional coverage database of every run with xcrg and writes the HTML reports, plus the code-coverage report."])
H("12.4 Where to look at the results", 2)
T(["Item", "Location"], [
    ["Logs of every run", "sim/logs/<test>_s<seed>.log (search for TEST PASSED, UVM_ERROR)"],
    ["Functional coverage", "sim/report/functional/functionalCoverageReport/dashboard.html"],
    ["Code coverage", "sim/report/code/codeCoverageReport/dashboard.html"],
    ["Synthesis", "synth/utilization_synth.rpt, synth/timing_synth.rpt, synth/synth.log"],
    ["Waveforms", "add -testplusarg WAVES to the xsim command (writes dma.vcd)"],
], [4.0, 12.6], caption="Result locations")
H("12.5 Debugging a failing test", 2)
N(["Open the log and find the first UVM_ERROR; the message names the component (SCB, CHK, AXI_SLV, TIMEOUT) and the channel.",
   "Scoreboard messages give the burst address, the word index and expected versus actual data.",
   "Assertion messages give the rule name and the exact time.",
   "Re-run only that test with the same seed and -testplusarg WAVES; inspect req, gnt_idx, the engine state and the AXI signals around the failure time."])
PAGEBREAK()

# ================================================================ 13
H("13. Synthesis, and the problems found along the way", 1)
H("13.1 Synthesis flow", 2)
P("synth/synth.tcl reads the six RTL files, runs synth_design in out-of-context mode for the Artix-7 part xc7a100t, "
  "applies a 10 ns (100 MHz) clock constraint and writes utilization and timing reports. Out-of-context means the block is "
  "synthesized alone, without top-level pins, which is the right way to size an IP block.", "j")
H("13.2 The synthesis story", 2)
T(["Metric", "First synthesis", "Final design"], [
    ["Slice LUTs", "about 3 500", "1 660 (2.6 %)"],
    ["Flip-flops", "6 010", "1 065 (0.8 %)"],
    ["LUT as memory (LUT-RAM)", "0", "128"],
    ["Block RAM / DSP", "0 / 0", "0 / 0"],
    ["Worst slack at 100 MHz", "-8.1 ns (fail)", "+1.742 ns (met)"],
    ["Errors / critical warnings", "-", "0 / 0"],
], [5.6, 5.0, 6.0], caption="First synthesis attempt versus the final design")
H("Problem 1: thousands of flip-flops", 3)
P("The FIFO and the burst buffer were first written inside always_ff blocks that also contained the reset. A reset on a "
  "whole array forces the tool to implement every bit as a resettable flip-flop. Fix: write the memories in separate "
  "reset-free always_ff blocks. The tool then maps them to LUT-RAM (128 LUTs).", "j")
H("Problem 2: a long critical path (WNS -8.1 ns)", 3)
P("The path went from a channel's remaining register through the burst-size calculation (24-bit comparisons), the request "
  "condition and the arbiter into the engine. Fixes: (a) 6-bit saturated burst-size logic, (b) register the request and "
  "next-beats in the channel, and (c) the engine states SETTLE (one idle cycle after each burst so the registered request "
  "is up to date) and LATCH (captures the winner's parameters one cycle after the arbiter decision). The cost is two extra "
  "cycles per burst, about 5 % of a 16-beat burst; the result is timing-clean at 100 MHz.", "j")
BOX("Why this matters", ["Every RTL change after verification started required rerunning the entire regression. The final "
    "13 of 13 pass happened after the last RTL change, so the verified design is exactly the one that was synthesized."])
H("13.3 Other problems found and fixed during development", 2)
T(["Problem", "Cause", "Fix"], [
    ["Recovery test failed on the second START", "Reference model still thought the channel was active after an error", "Model clears active on an AXI error and on an ERR status read"],
    ["Compile error on coverage bins", "small, medium, large, global are SystemVerilog keywords", "Renamed the bins"],
    ["Elaboration error", "xsim does not support default disable iff", "Explicit disable iff in every assertion"],
    ["xsim rejected +UVM_TESTNAME=...", "The Vivado batch wrapper splits arguments at =", "Pass plusargs through an arguments file"],
    ["No code-coverage report", "Database accumulates in work/xsim.codeCov", "Report script points at that database"],
    ["Windows scripts could not find each other", "Current directory not searched for commands", "Call helper scripts with their full path (%~dp0)"],
    ["Priority-cross coverage unreachable", "Impossible combinations (winner with lower priority) counted as holes", "Excluded with ignore_bins and proven by assertion instead"],
], [4.6, 6.0, 6.0], caption="Development problems")
PAGEBREAK()

# ================================================================ 14
H("14. Final results, limits and future work", 1)
H("14.1 The ADAS scenario in numbers", 2)
P("All four channels run at the same time (`dma_sensor_fusion_test`):")
T(["Channel", "Words", "Mode / priority", "Finished after (cycles)"], [
    ["CH1 radar", "256", "sensor, priority 3, 4-beat bursts, bursty", "1 120"],
    ["CH2 LiDAR", "1 024", "sensor, priority 2, 8-beat bursts", "4 277"],
    ["CH0 camera", "4 608", "sensor, priority 1, 16-beat bursts", "15 978"],
    ["CH3 diagnostics", "512", "memory to memory, priority 0", "17 345"],
], [3.4, 2.0, 7.0, 4.2], caption="Sensor fusion")
B(["The critical radar channel finishes first (1 120 cycles) while the camera and diagnostics move thousands of words: per-burst priority arbitration works as intended (the test checks it).",
   "Completion order follows the priorities exactly: radar, LiDAR, camera, diagnostics.",
   "6 400 words were written and every one was checked by the scoreboard.",
   "In the back-pressure scenario (very slow memory) the sensor FIFOs were full for 12 561 cycles and no data was lost."])
H("14.2 Summary table", 2)
T(["Area", "Status"], [
    ["Requirements and architecture", "Done (chapters 3 to 6, docs/)"],
    ["RTL", "Done: 6 modules, synthesizable, 0 errors and 0 critical warnings in Vivado synthesis"],
    ["Directed and random verification", "13 of 13 runs pass"],
    ["Assertions", "APB, AXI, arbiter and channel rules, zero failures"],
    ["Functional coverage", "100 %"],
    ["Code coverage", "100 % statement, 94 to 100 % branch on all RTL modules"],
    ["Mutation check", "4 of 4 caught"],
    ["Synthesis", "1 660 LUT, 1 065 FF, 100 MHz met with +1.74 ns slack (post-synthesis estimate)"],
], [5.0, 11.6], caption="Summary")
H("14.3 Known limits", 2)
B(["One outstanding burst: reads and writes never overlap, so peak throughput is below what AXI can do.",
   "32-bit data, INCR bursts only, no AXI IDs.",
   "Registers describe one transfer per channel; there are no descriptor chains in memory.",
   "Strict priority: a long high-priority transfer delays lower priorities until it finishes (intentional for a safety-critical radar).",
   "A memory that never answers is not detected (no watchdog); the simulated memory always answers.",
   "No formal verification and no UVM register model; xsim ignores cover property; synthesis results are pre-route estimates."])
H("14.4 Future work", 2)
T(["Idea", "Benefit"], [
    ["Anti-starvation aging in the arbiter", "Guarantees a low-priority channel the bus even under constant high-priority load"],
    ["Bus watchdog", "Reports a hung memory instead of waiting forever"],
    ["Continuous (ring) mode and abort", "Back-to-back camera frames without software restarts; stop a running channel"],
    ["Performance counters", "Measure bus utilisation in hardware"],
    ["Overlap read and write bursts (double buffer)", "Higher throughput and lower latency"],
    ["Scatter-gather descriptors in memory", "Chained transfers without CPU involvement"],
    ["Wider data (64/128 bit)", "Higher camera bandwidth"],
    ["UVM RAL, formal proofs, place and route on a board", "Stronger verification and a hardware proof of concept"],
], [6.4, 10.2], caption="Future work")

# ================================================================ appendices
H("Appendix A. Glossary", 1)
T(["Term", "Meaning"], [
    ["ADAS", "Advanced Driver Assistance System (lane keeping, emergency braking, ...)"],
    ["AMBA", "ARM bus standards family that includes APB and AXI"],
    ["APB", "Advanced Peripheral Bus: simple register bus (setup + access phase)"],
    ["AXI4", "Advanced eXtensible Interface: high-performance bus with five channels"],
    ["Back-pressure", "Receiver slows the sender by lowering READY"],
    ["Beat / Burst", "One data transfer / one address followed by several beats"],
    ["Covergroup", "SystemVerilog construct that counts which scenarios occurred"],
    ["DMA", "Direct Memory Access: hardware that copies data without the CPU"],
    ["DUT", "Design Under Test"],
    ["FIFO", "First-in first-out queue"],
    ["FSM", "Finite state machine"],
    ["INCR", "AXI burst type where the address increments each beat"],
    ["LUT-RAM", "FPGA lookup tables used as small memories"],
    ["Mutation", "A deliberately injected bug used to test the testbench"],
    ["Round-robin", "Taking turns: the next tie goes to the channel after the last winner"],
    ["Scoreboard", "Testbench component that compares DUT results with a prediction"],
    ["SLVERR / DECERR", "AXI error responses: slave error / decode (no such address) error"],
    ["SVA / UVM", "SystemVerilog Assertions / Universal Verification Methodology"],
    ["W1C", "Write-1-to-clear register bits"],
    ["WNS", "Worst negative slack: timing margin of the slowest path"],
], [3.4, 13.2], caption="Glossary")
H("Appendix B. File list", 1)
T(["File", "Purpose"], [
    ["rtl/dma_pkg.sv", "Parameters, error codes, register offsets"],
    ["rtl/dma_sfifo.sv", "Sensor FIFO"],
    ["rtl/dma_channel.sv", "Channel registers, context, request and interrupt logic"],
    ["rtl/dma_arbiter.sv", "Priority + round-robin arbiter"],
    ["rtl/dma_engine.sv", "Burst FSM and AXI master"],
    ["rtl/dma_top.sv", "Top level, APB decode, global registers"],
    ["tb/if/dma_ifs.sv", "APB, AXI, stream and debug interfaces"],
    ["tb/sva/dma_sva.sv", "Assertions (bound to the DUT)"],
    ["tb/uvm/dma_tb_items.svh", "Transaction items, memory model, slave configuration"],
    ["tb/uvm/dma_tb_agents.svh", "APB, stream and AXI agents, arbitration monitor"],
    ["tb/uvm/dma_tb_env.svh", "Scoreboard, coverage, environment, virtual sequencer"],
    ["tb/uvm/dma_tb_seqs.svh", "The 9 scenario sequences"],
    ["tb/uvm/dma_tb_tests.svh", "Base test and the test classes"],
    ["tb/uvm/dma_tb_pkg.sv, tb/tb_top.sv", "Package wrapper, testbench top"],
    ["sim/*.bat, sim/*.sh", "Build, run, regression, coverage scripts"],
    ["synth/synth.tcl", "Vivado synthesis script"],
    ["docs/", "Requirements, architecture, register map, verification plan, block diagram, reports, figures"],
    ["scripts/", "Figure generators and the document builders"],
], [5.6, 11.0], caption="Files")
H("Appendix C. Typical interview and viva questions with answers", 1)
QA = [
    ("Why a DMA instead of the CPU?", "It frees the CPU, gives predictable latency and higher sustained bandwidth for streaming data."),
    ("How is the critical sensor served first?", "Each channel has a 2-bit priority; at every burst boundary the arbiter grants the highest-priority requester."),
    ("Why arbitrate per burst and not per transfer?", "It bounds the wait of a critical channel to one burst (at most 16 beats) of any other channel."),
    ("What happens with equal priorities?", "Round-robin: a pointer remembers the last winner and the next tie goes to the channel after it."),
    ("What is the 4 KB rule and how is it handled?", "AXI bursts must not cross a 4 KB boundary. The channel shortens a burst to the words left in the page; the testbench re-derives the size and assertions check every burst."),
    ("What happens on an AXI error?", "The engine records the first error, skips the write on a read error, and reports the code to the owning channel, which stops and raises ERR. Other channels continue; software can restart the failed one."),
    ("What is back-pressure?", "When a channel's FIFO is full the DMA lowers s_ready and the sensor waits, so no data is lost."),
    ("How do you know the testbench is good?", "It checks data against an independent model, assertions guard the protocols, coverage reached 100 %, and all 4 injected RTL bugs were caught."),
    ("Why is there a SETTLE state?", "The request is registered for timing; after each burst the context changes, so one cycle is needed before the request is valid again."),
    ("Why no reset on the FIFO memory?", "A reset on the array forces flip-flops; without it the memory maps to LUT-RAM."),
    ("Scoreboard versus assertion?", "The scoreboard checks results (data, order, sizes) against a model; assertions check signal-level rules every cycle and fire at the exact time."),
    ("Functional versus code coverage?", "Functional coverage measures which specified scenarios were exercised; code coverage measures which RTL lines and branches ran. Both are needed."),
]
for q, a in QA:
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(1)
    r = p.add_run("Q: " + q); r.bold = True; r.font.color.rgb = NAVY
    P("A: " + a, after=8)
H("Appendix D. How to change the design", 1)
T(["Change", "Where", "Also update"], [
    ["Number of channels", "N_CH in dma_pkg.sv", "Register window decode, testbench address plan"],
    ["FIFO depth", "FIFO_DEPTH (power of two)", "Burst size 16 must stay at most the depth"],
    ["Maximum burst length", "MAX_BEATS and burst buffer size", "Assertion limits, BLEN field width"],
    ["Arbitration policy", "dma_arbiter.sv", "a_prio_order assertion, dma_priority_test expectations"],
    ["New error source", "dma_engine.sv error mapping, dma_pkg.sv error enum", "Scoreboard, cg_err, an error test"],
], [4.0, 6.0, 6.6], caption="Design changes")

# ---------------------------------------------------------------- finish (shared with the milestone report)
_TAIL = _SRC[_SRC.index("# ---------------------------------------------------------------- header / footer"):]
exec(_TAIL.replace("Milestone Report", "Complete Project Flow"))
