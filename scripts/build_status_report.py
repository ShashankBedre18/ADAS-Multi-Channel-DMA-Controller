"""
build_status_report.py - writes docs/ADAS_DMA_Project_Status_Report.docx
(status of every item the brief asked for, with evidence and results).
Shares its formatting helpers with build_milestone_report.py.  Needs: pip install python-docx
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = open(os.path.join(_HERE, "build_milestone_report.py"), encoding="utf8").read()
exec(_SRC[:_SRC.index("# ---------------------------------------------------------------- cover")])
OUT = os.path.join(ROOT, "docs", "ADAS_DMA_Project_Status_Report.docx")

DONE = "**COMPLETE**"


def status_table(rows, caption, widths=(1.3, 5.2, 2.4, 7.7)):
    T(["#", "Item asked for", "Status", "Evidence"], rows, list(widths), caption=caption)


# ---------------------------------------------------------------- cover
for _ in range(3):
    doc.add_paragraph()
p = P("L&T EduTech  |  VLSI Principles, RTL Design and Verification  |  Project 1", "c", 12); p.runs[0].font.color.rgb = GREY
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Multi-Channel DMA Controller Subsystem"); r.font.size = Pt(26); r.bold = True; r.font.color.rgb = NAVY
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Project Status Report"); r.font.size = Pt(20); r.font.color.rgb = BLUE
P("Status of every item in the problem statement, the verification requirements and the three milestones", "c", 12)
doc.add_paragraph().paragraph_format.space_after = Pt(30)
T(["Item", "Details"], [
    ["Student name", ""], ["Registration / LMS ID", ""],
    ["Report date", "21 October 2026"],
    ["Overall status", "COMPLETE - all items of the brief implemented, verified and documented"],
    ["Tools", "SystemVerilog, UVM 1.2, SVA, AMD Vivado 2025.2 (xsim, xcrg, synthesis)"],
], [4.5, 11.5], zebra=False, size=10)
PAGEBREAK()

H("Contents", 1)
TOC_PAR = field(doc.add_paragraph(), 'TOC \\o "1-2" \\h \\z \\u')
P("(In Word: right-click the list and choose Update Field to add page numbers.)", size=9, italic=True)
TOC_ANCHOR = doc.paragraphs[-1]
PAGEBREAK()

# ================================================================ 1
H("1. Executive summary", 1)
BOX("Overall status: COMPLETE", [
    "All **5 capabilities** required by the problem statement are implemented in synthesizable SystemVerilog RTL.",
    "All **4 verification requirements** are met: transaction-based testbench, assertions, covergroups and functional coverage reports.",
    "All **15 milestone items** (3 milestones x 5 items) are complete, each with files that prove it.",
    "Final regression: **13 of 13 test runs pass**, 0 UVM errors, 0 assertion failures.",
    "Coverage: **100 % functional**, **100 % statement** coverage on every RTL module.",
    "Synthesis on an Artix-7 FPGA: **1 660 LUTs, 1 065 flip-flops, 100 MHz met** (+1.74 ns slack), 0 errors, 0 critical warnings.",
], "E7F6EC", "2F855A")
T(["Area", "Items", "Complete", "Status"], [
    ["Problem-statement capabilities", "5", "5", DONE],
    ["Verification requirements", "4", "4", DONE],
    ["Milestone 1: Requirements and Architecture Design", "5", "5", DONE],
    ["Milestone 2: RTL Implementation", "5", "5", DONE],
    ["Milestone 3: Verification and Validation", "5", "5", DONE],
    ["Functional requirements R1 - R10 (derived from the brief)", "10", "10", DONE],
    ["**Total**", "**34**", "**34**", DONE],
], [8.2, 2.0, 2.4, 4.0], caption="Status at a glance")
FIGURE("f_flow.png", "Project flow followed from problem to synthesis - every step is complete.")
PAGEBREAK()

# ================================================================ 2
H("2. What was asked", 1)
P("The problem statement describes an automotive SoC manufacturer building an **ADAS** platform that must continuously move "
  "high-bandwidth sensor data from **cameras, radar and LiDAR** into memory while minimising CPU overhead. The existing "
  "processor-centric data movement causes performance bottlenecks and latency. The company asked for a **configurable DMA "
  "subsystem** that can:", "j")
B(["manage multiple concurrent data streams,",
   "prioritise critical sensor transfers,",
   "support burst transactions,",
   "generate status interrupts, and",
   "provide reliable error handling."])
P("It also asked for a SystemVerilog transaction-based testbench, assertions, covergroups and functional coverage reports, "
  "delivered through three milestones of five items each.", "j")
FIGURE("m1_cpu_vs_dma.png", "The problem (CPU copies every word) and the solution delivered (DMA moves the data in bursts).")

# ================================================================ 3
H("3. Status of the problem-statement capabilities", 1)
status_table([
    ["C1", "Manage multiple concurrent data streams", DONE,
     "4 independent channels (memory-to-memory or sensor-to-memory) sharing one burst engine - rtl/dma_channel.sv, rtl/dma_engine.sv. Verified by dma_sensor_fusion_test (4 streams at once) and dma_random_test."],
    ["C2", "Prioritise critical sensor transfers", DONE,
     "2-bit priority per channel, decided at every burst boundary; round-robin among equal priorities - rtl/dma_arbiter.sv. Verified by dma_priority_test and assertion a_prio_order; radar finishes first in the ADAS test."],
    ["C3", "Support burst transactions", DONE,
     "AXI4 INCR bursts of 1-16 beats, automatically split at 4 KB boundaries. Verified by dma_burst_sweep_test (all 16 burst lengths), scoreboard length check and assertions a_aw_4k / a_ar_4k."],
    ["C4", "Generate status interrupts", DONE,
     "DONE and ERR per channel, maskable (INT_EN), write-1-to-clear (INT_STAT), global irq; STATUS / REMAIN / XFERRED registers. Verified by dma_regs_test and assertions a_irq_def / a_irq_or."],
    ["C5", "Reliable error handling", DONE,
     "SLVERR / DECERR detected and isolated to one channel with an error code; illegal configurations rejected with no bus traffic; restart after error. Verified by dma_error_test (4 x 4 error matrix) and dma_cfg_err_test."],
], "Problem-statement capabilities")
H("3.1 Proof from simulation: the ADAS scenario", 2)
T(["Channel", "Words", "Priority", "Finished after (cycles)"], [
    ["CH1 radar", "256", "3 (highest)", "1 120 - first"],
    ["CH2 LiDAR", "1 024", "2", "4 277"],
    ["CH0 camera", "4 608", "1", "15 978"],
    ["CH3 diagnostics", "512", "0", "17 345"],
], [4.0, 2.4, 3.4, 6.8], caption="All four streams running together (dma_sensor_fusion_test)")
P("All 6 400 words were checked by the scoreboard, and the completion order follows the priorities exactly - the "
  "critical radar data is never stuck behind the camera frame.", "j")

# ================================================================ 4
H("4. Status of the verification requirements", 1)
status_table([
    ["V1", "Develop a SystemVerilog transaction-based testbench", DONE,
     "UVM environment: APB agent, 4 sensor-stream agents, reactive AXI memory agent, arbitration monitor, scoreboard, coverage, virtual sequencer - tb/."],
    ["V2", "Develop assertions to verify ...", DONE,
     "25 SVA properties (52 instances) for APB protocol, AXI handshake and legality (incl. 4 KB rule and WLAST), arbitration order, channel rules and interrupts - tb/sva/dma_sva.sv. 0 failures."],
    ["V3", "Create covergroups to measure ...", DONE,
     "7 covergroups: configuration, AXI bursts and responses, arbitration, interrupts, error codes, sensor back-pressure, APB access - tb/uvm/dma_tb_env.svh."],
    ["V4", "Generate functional coverage reports", DONE,
     "Merged HTML reports from Vivado xcrg - sim/report/functional/ (100 %) and sim/report/code/ (100 % statement)."],
], "Verification requirements")
FIGURE("m3_cov_chart.png", "Functional coverage per covergroup - every covergroup at 100 %.")

# ================================================================ 5
H("5. Status of the milestones", 1)
H("5.1 Milestone 1: Requirements and Architecture Design", 2)
status_table([
    ["M1.1", "Study DMA architecture used in SoCs", DONE, "docs/01_problem_and_requirements.md, docs/02_architecture.md; Milestones Report section 2.1"],
    ["M1.2", "Define channel configuration registers", DONE, "docs/03_register_map.md - 4 global + 9 per-channel registers with bit fields; rtl/dma_pkg.sv"],
    ["M1.3", "Design arbitration scheme for multiple DMA requests", DONE, "Priority + round-robin, one decision per burst - docs/02_architecture.md section 2.5"],
    ["M1.4", "Create datapath and controller architecture", DONE, "Store-and-forward datapath, channel / arbiter / engine controller split - docs/02_architecture.md sections 2.2-2.4"],
    ["M1.5", "Develop RTL block diagram", DONE, "docs/block_diagram.svg; module hierarchy and port list in the reports"],
], "Milestone 1")
H("5.2 Milestone 2: RTL Implementation", 2)
status_table([
    ["M2.1", "Implement DMA channel controller", DONE, "rtl/dma_channel.sv (+ rtl/dma_sfifo.sv), instantiated 4 times"],
    ["M2.2", "Design arbitration logic", DONE, "rtl/dma_arbiter.sv - priority scan from a round-robin pointer"],
    ["M2.3", "Implement transfer state machine", DONE, "rtl/dma_engine.sv - 10-state burst FSM, AXI4 master"],
    ["M2.4", "Integrate interrupt and status registers", DONE, "INT_EN / INT_STAT / STATUS / REMAIN / XFERRED in rtl/dma_channel.sv; GSTAT / IRQ_SUM in rtl/dma_top.sv"],
    ["M2.5", "Perform RTL simulation", DONE, "sim/ scripts, sim/logs/ - 13 of 13 runs pass; waveforms in docs/figures/"],
], "Milestone 2")
H("5.3 Milestone 3: Verification and Validation", 2)
status_table([
    ["M3.1", "Develop SystemVerilog testbench", DONE, "tb/tb_top.sv, tb/if/dma_ifs.sv, transaction items"],
    ["M3.2", "Create UVM agents and sequences", DONE, "tb/uvm/ - 3 agent types, 9 virtual sequences / tests"],
    ["M3.3", "Implement scoreboarding and checking", DONE, "dma_scoreboard with an independent reference model; mutation check: 4 of 4 injected bugs caught"],
    ["M3.4", "Add assertions for protocol compliance", DONE, "tb/sva/dma_sva.sv - 25 properties, 0 failures"],
    ["M3.5", "Generate functional and code coverage reports", DONE, "sim/report/ - 100 % functional, 100 % statement on all RTL modules"],
], "Milestone 3")

# ================================================================ 6
H("6. Requirements traceability (R1 - R10)", 1)
P("The brief was turned into ten testable requirements. Each one is implemented in a named RTL block and checked by named "
  "tests and assertions.", "j")
T(["ID", "Requirement", "Implemented in", "Verified by", "Status"], [
    ["R1", "4 channels, memory or sensor source", "dma_channel x4", "smoke, sensor_fusion, random", DONE],
    ["R2", "AXI4 INCR bursts 1-16 beats, no 4 KB crossing", "dma_engine, dma_channel", "burst_sweep, a_aw_4k, a_ar_4k, scoreboard", DONE],
    ["R3", "APB register interface", "dma_top, dma_channel", "regs_test, APB assertions", DONE],
    ["R4", "Higher priority served first", "dma_arbiter", "priority_test, sensor_fusion, a_prio_order", DONE],
    ["R5", "Round-robin among equal priorities", "dma_arbiter", "priority_test (grant rotation check)", DONE],
    ["R6", "DONE / ERR interrupts, maskable, W1C", "dma_channel, dma_top", "regs_test, a_irq_def, a_irq_or", DONE],
    ["R7", "Bus error isolated to one channel", "dma_engine, dma_channel", "error_test (4 x 4 matrix)", DONE],
    ["R8", "Illegal configuration rejected, no traffic", "dma_channel", "cfg_err_test, a_bad_start_inactive", DONE],
    ["R9", "Restart after error", "dma_channel", "error_test, cfg_err_test", DONE],
    ["R10", "No data loss (back-pressure)", "dma_channel, dma_sfifo", "backpressure_test, scoreboard data check", DONE],
], [1.2, 4.6, 3.4, 5.0, 2.4], caption="Traceability matrix")

# ================================================================ 7
H("7. Verification results", 1)
H("7.1 Regression", 2)
FIGURE("regression.png", "Final regression: 13 of 13 runs pass, 0 UVM errors, 0 fatals.", 13.0)
T(["Test", "Purpose", "Result"], [
    ["dma_regs_test", "Register reset values, access types, PSLVERR, write-1-to-clear", "PASS"],
    ["dma_smoke_test", "One memory and one sensor transfer", "PASS"],
    ["dma_sensor_fusion_test", "ADAS scenario: 4 streams at once, radar first", "PASS"],
    ["dma_burst_sweep_test", "All burst lengths, 4 KB splitting", "PASS"],
    ["dma_priority_test", "Priority order and round-robin rotation", "PASS"],
    ["dma_error_test", "SLVERR / DECERR isolation and recovery", "PASS"],
    ["dma_cfg_err_test", "Illegal configurations rejected", "PASS"],
    ["dma_backpressure_test", "Slow memory, sensors held off, no data lost", "PASS"],
    ["dma_random_test (5 seeds)", "Constrained-random mix, about 20 000 checks per run", "PASS x 5"],
], [4.6, 9.4, 2.6], caption="Tests")
H("7.2 Coverage", 2)
T(["RTL module", "Statement %", "Branch %", "Condition %", "Toggle %"], [
    ["dma_top", "100", "94.1", "83.3", "71.6"], ["dma_channel", "100", "100", "97.2", "54.6"],
    ["dma_sfifo", "100", "100", "100", "99.5"], ["dma_arbiter", "100", "100", "100", "100"],
    ["dma_engine", "100", "100", "97.9", "92.0"],
], [4.6, 3.0, 3.0, 3.0, 3.0], caption="Code coverage (functional coverage: 100 %)")
P("Toggle coverage is lower in dma_top and dma_channel only because the upper bits of 32-bit addresses never change in "
  "the small simulated memory; it is not a functional gap.", "j")
H("7.3 Does the testbench really catch bugs?", 2)
T(["Injected bug", "Caught by", "Result"], [
    ["Data bit flipped on beat 5", "dma_smoke_test (scoreboard)", "Caught"],
    ["Arbiter ignores priority", "dma_priority_test", "Caught"],
    ["4 KB splitting removed", "dma_burst_sweep_test (scoreboard)", "Caught"],
    ["DECERR reported as SLVERR", "dma_error_test", "Caught"],
], [6.0, 7.0, 3.6], caption="Mutation check on the final RTL")

# ================================================================ 8
H("8. Implementation results (synthesis)", 1)
T(["Metric", "Result (xc7a100t, Vivado 2025.2, out-of-context)"], [
    ["Slice LUTs", "1 660 (2.6 % of the device)"],
    ["Flip-flops", "1 065 (0.8 %)"],
    ["Block RAM / DSP", "0 / 0"],
    ["Clock", "100 MHz met, worst slack +1.742 ns"],
    ["Errors / critical warnings", "0 / 0"],
], [5.0, 11.6], caption="Synthesis (post-synthesis estimate)")
P("Synthesis is beyond what the brief requires; it shows the RTL is real, implementable hardware.", "j")

# ================================================================ 9
H("9. Scope of the delivered design", 1)
T(["Category", "Features"], [
    ["Required by the brief", "4 concurrent channels; priority arbitration; AXI4 burst transfers; DONE / ERR interrupts and status registers; error detection, isolation and restart"],
    ["Basic extras (needed for correctness)", "Sensor-stream input with a 32-word FIFO per channel; round-robin between equal priorities; automatic 4 KB burst splitting; illegal-configuration detection"],
    ["Not included (future work)", "Anti-starvation aging, continuous / ring mode, bus watchdog, abort, performance counters, scatter-gather descriptors"],
], [5.0, 11.6], caption="What is in and out of scope")

# ================================================================ 10
H("10. Deliverables", 1)
T(["Deliverable", "Location", "Status"], [
    ["Requirements and architecture documents", "docs/01 - docs/04, docs/block_diagram.svg", DONE],
    ["RTL source (6 modules)", "rtl/", DONE],
    ["UVM testbench and assertions", "tb/", DONE],
    ["Simulation and regression scripts", "sim/*.bat, sim/*.sh", DONE],
    ["Regression logs", "sim/logs/", DONE],
    ["Functional and code coverage reports (HTML)", "sim/report/", DONE],
    ["Synthesis script and reports", "synth/", DONE],
    ["Milestones Report", "docs/ADAS_DMA_Milestones_Report.docx", DONE],
    ["Complete Project Flow", "docs/ADAS_DMA_Complete_Project_Flow.docx", DONE],
    ["Project Status Report (this document)", "docs/ADAS_DMA_Project_Status_Report.docx", DONE],
    ["Submission package", "LNT_ADAS_DMA_Subsystem_Submission.zip (next to the project folder)", DONE],
], [6.0, 7.8, 2.8], caption="Deliverables")

# ================================================================ 11
H("11. Known limits and remaining actions", 1)
H("11.1 Known limits (documented, not defects)", 2)
B(["One outstanding AXI burst at a time (reads and writes do not overlap).",
   "32-bit data, INCR bursts only; one transfer per channel (no descriptor chains).",
   "Strict priority: a long high-priority transfer delays lower priorities until it finishes (intentional for safety-critical radar).",
   "No formal verification or UVM register model; xsim ignores cover property; synthesis numbers are pre-route estimates."])
H("11.2 Remaining actions before submission", 2)
T(["Action", "Who", "Status"], [
    ["Fill in student name and LMS ID on the cover pages of the three reports", "Student", "To do"],
    ["Open each report in Word and update the table of contents (right-click, Update Field)", "Student", "To do"],
    ["Export to PDF if the LMS portal requires PDF", "Student", "If required"],
    ["Upload LNT_ADAS_DMA_Subsystem_Submission.zip to the LMS portal", "Student", "To do"],
], [10.0, 2.6, 4.0], caption="Remaining actions")

_TAIL = _SRC[_SRC.index("# ---------------------------------------------------------------- header / footer"):]
exec(_TAIL.replace("Milestone Report", "Project Status Report"))
