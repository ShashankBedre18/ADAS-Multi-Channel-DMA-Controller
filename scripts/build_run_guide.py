"""
build_run_guide.py - writes docs/ADAS_DMA_How_To_Run_And_Analyse.docx
(step-by-step guide: install, run the regression, read logs, coverage, waveforms, synthesis, debugging).
Shares its formatting helpers with build_milestone_report.py.  Needs: pip install python-docx
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = open(os.path.join(_HERE, "build_milestone_report.py"), encoding="utf8").read()
exec(_SRC[:_SRC.index("# ---------------------------------------------------------------- cover")])
OUT = os.path.join(ROOT, "docs", "ADAS_DMA_How_To_Run_And_Analyse.docx")


def STEP(n, title):
    H(f"Step {n}. {title}", 1)


# ---------------------------------------------------------------- cover
for _ in range(3):
    doc.add_paragraph()
p = P("L&T EduTech  |  VLSI Principles, RTL Design and Verification  |  Project 1", "c", 12); p.runs[0].font.color.rgb = GREY
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("ADAS Multi-Channel DMA Controller Subsystem"); r.font.size = Pt(24); r.bold = True; r.font.color.rgb = NAVY
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("How to Run the Project and Analyse the Results"); r.font.size = Pt(18); r.font.color.rgb = BLUE
P("A step-by-step guide for running the project on your own laptop: setup, simulation, logs, coverage, waveforms, "
  "synthesis and debugging", "c", 12)
doc.add_paragraph().paragraph_format.space_after = Pt(30)
T(["You will need", "Details"], [
    ["Operating system", "Windows 10 or 11 (64-bit)"],
    ["Software", "AMD Vivado 2025.2 (the free Vivado ML Standard edition is enough - it contains the xsim simulator, UVM 1.2, the xcrg coverage tool and synthesis)"],
    ["Project", "The folder ADAS_DMA_Subsystem (from LNT_ADAS_DMA_Subsystem_Submission.zip)"],
    ["Time", "About 5 minutes for the full regression on a typical laptop; about 1 minute for synthesis"],
], [4.0, 12.0], zebra=False, size=10)
PAGEBREAK()

H("Contents", 1)
TOC_PAR = field(doc.add_paragraph(), 'TOC \\o "1-2" \\h \\z \\u')
P("(In Word: right-click the list and choose Update Field to add page numbers.)", size=9, italic=True)
TOC_ANCHOR = doc.paragraphs[-1]
PAGEBREAK()

# ================================================================ overview
H("Overview: what you will do", 1)
FIGURE("m2_sim_flow.png", "The simulation flow that the scripts run for you.")
T(["Step", "What you do", "What you get"], [
    ["1", "Copy the project to your laptop", "The project folder in a short path"],
    ["2", "Tell the scripts where Vivado is", "A one-line edit in sim\\env.bat"],
    ["3", "Run the full regression with one command", "13 test runs, PASS/FAIL lines, logs, coverage database"],
    ["4", "Read the console and the log files", "Proof that every test passed and what each test checked"],
    ["5", "Open the coverage reports", "100 % functional coverage, 100 % statement coverage"],
    ["6", "Run single tests with your own seeds", "Extra confidence, specific scenarios"],
    ["7", "Look at the waveforms in the Vivado GUI", "Cycle-by-cycle view of bursts, arbitration, interrupts"],
    ["8", "Run synthesis and read the reports", "LUTs, flip-flops, timing at 100 MHz"],
    ["9", "Compare with the golden results", "Confirmation that your run matches the expected numbers"],
], [1.2, 7.6, 7.8], caption="The nine steps")
BOX("Important", ["All commands in this guide are typed in the Windows **Command Prompt** (cmd). If you use PowerShell, "
                  "put `cmd /c` in front of a .bat command, for example `cmd /c sim\\regress.bat`."])
PAGEBREAK()

# ================================================================ 1
STEP(1, "Copy the project to your laptop")
N(["Copy `LNT_ADAS_DMA_Subsystem_Submission.zip` to your laptop and extract it (right-click > Extract All).",
   "Move the extracted `ADAS_DMA_Subsystem` folder to a **short path without spaces**, for example `C:\\Projects\\ADAS_DMA_Subsystem` or your Desktop. Very long paths can make Vivado tools fail on Windows.",
   "Check that the folder contains: `docs`, `rtl`, `tb`, `sim`, `synth`, `scripts` and `README.md`."])
T(["Folder", "What is inside"], [
    ["rtl\\", "The design: 6 SystemVerilog files"],
    ["tb\\", "The UVM testbench, interfaces and assertions"],
    ["sim\\", "The scripts you run (build, run_test, regress, coverage_report, run_gui) and, after a run, the logs and reports"],
    ["synth\\", "The synthesis script and its reports"],
    ["docs\\", "Specifications, reports and figures"],
], [3.0, 13.6], caption="Project folders")

# ================================================================ 2
STEP(2, "Tell the scripts where Vivado is installed")
P("The scripts need the path of Vivado's `bin` folder. It is set in one place: `sim\\env.bat`.", "j")
H("2.1 Find your Vivado bin folder", 2)
N(["Right-click your **Vivado 2025.2** desktop shortcut and choose **Open file location**.",
   "You land in a folder such as `C:\\AMDDesignTools\\2025.2\\Vivado\\bin\\unwrapped\\win64.o` or `D:\\Vivado\\2025.2\\Vivado\\bin\\...`.",
   "The folder you need is the `...\\Vivado\\bin` folder that contains `xvlog.bat`, `xelab.bat`, `xsim.bat` and `xcrg.bat`."])
H("2.2 Edit sim\\env.bat", 2)
P("Open `sim\\env.bat` in Notepad and change the path on the third line to your own bin folder:", "j")
CODE("""@echo off
rem Path to the Vivado "bin" folder (edit if your install is elsewhere)
if not defined VIVADO_BIN set VIVADO_BIN=D:\\Vivado\\2025.2\\Vivado\\bin     <-- change this path
set PATH=%VIVADO_BIN%;%PATH%""", "sim\\env.bat")
P("If you use Git Bash and the `.sh` scripts instead, change the `export PATH=...` line at the top of each `sim\\*.sh` file "
  "in the same way (Git Bash writes `D:\\Vivado` as `/d/Vivado`).", "j")
H("2.3 Check that it works", 2)
CODE("""cd C:\\Projects\\ADAS_DMA_Subsystem
call sim\\env.bat
xvlog --version""", "Command Prompt")
P("You should see a line such as `Vivado Simulator v2025.2`. If you see `'xvlog' is not recognized`, the path in env.bat "
  "is wrong - go back to 2.1.", "j")
PAGEBREAK()

# ================================================================ 3
STEP(3, "Run the full regression")
P("The regression compiles everything, runs all 13 test runs, merges the coverage and writes the HTML reports. One command:", "j")
CODE("""cd C:\\Projects\\ADAS_DMA_Subsystem
sim\\regress.bat""", "Command Prompt")
H("3.1 What happens", 2)
T(["Stage", "Script", "What it does"], [
    ["Compile", "build.bat (xvlog)", "Compiles the 6 RTL files, the interfaces, the assertions, the UVM package and tb_top"],
    ["Elaborate", "build.bat (xelab)", "Builds the simulation snapshot tb_snap with code coverage switched on"],
    ["Simulate", "run_test.bat (xsim) x 13", "8 directed tests with seed 1, then dma_random_test with seeds 11-15 (40 iterations each)"],
    ["Coverage", "coverage_report.bat (xcrg)", "Merges the coverage of all runs and writes HTML reports"],
], [2.6, 4.6, 9.4], caption="Regression stages")
H("3.2 What you should see", 2)
P("While it runs, compile messages scroll by, then one line per test:", "j")
CODE("""Built simulation snapshot tb_snap
... [RESULT] *** TEST PASSED: dma_regs_test ***
... [RESULT] *** TEST PASSED: dma_smoke_test ***
... [RESULT] *** TEST PASSED: dma_sensor_fusion_test ***
... [RESULT] *** TEST PASSED: dma_burst_sweep_test ***
... [RESULT] *** TEST PASSED: dma_priority_test ***
... [RESULT] *** TEST PASSED: dma_error_test ***
... [RESULT] *** TEST PASSED: dma_cfg_err_test ***
... [RESULT] *** TEST PASSED: dma_backpressure_test ***
... [RESULT] *** TEST PASSED: dma_random_test ***      (x 5, one per seed)
Reports: sim\\report\\functional\\functionalCoverageReport\\dashboard.html and
         sim\\report\\code\\codeCoverageReport\\dashboard.html""", "Expected console output (shortened)")
BOX("Success criterion", ["**13 lines with TEST PASSED and no line with TEST FAILED.** If a line is missing or says FAILED, "
                          "see Step 10 (Analysing a failure) and Step 11 (Troubleshooting)."], "E7F6EC", "2F855A")
H("3.3 Files created by the run", 2)
T(["Location", "Content"], [
    ["sim\\work\\", "Compiled snapshot and the code-coverage database (re-created by every build)"],
    ["sim\\logs\\<test>_s<seed>.log", "Full log of every run - the main evidence"],
    ["sim\\cov\\", "Functional coverage database of every run"],
    ["sim\\report\\functional\\", "Merged functional coverage report (HTML)"],
    ["sim\\report\\code\\", "Code coverage report (HTML)"],
], [6.0, 10.6], caption="Outputs")
PAGEBREAK()

# ================================================================ 4
STEP(4, "Read the console and the log files")
P("Every run writes a log in `sim\\logs\\`, for example `sim\\logs\\dma_smoke_test_s1.log` (s1 = seed 1). Open it in Notepad. "
  "Most of the top is the standard UVM banner; the useful part is at the end:", "j")
CODE("""UVM_INFO @ 0: reporter [RNTST] Running test dma_smoke_test...
UVM_INFO .../dma_tb_env.svh(410) @ 5595000: uvm_test_top.env.cov [COV] cfg=40.0% axi=48.1% arb=28.6% irq=41.7% err=18.8% sensor=29.2% apb=66.7%
UVM_INFO .../dma_tb_env.svh(234) @ 5595000: uvm_test_top.env.scb [SCB] checks=110  rd_bursts=4 wr_bursts=8 wr_beats=96  apb=18  arbitrations=8 (wins 4/4/0/0)
UVM_INFO .../dma_tb_tests.svh(39) @ 5595000: uvm_test_top [RESULT] *** TEST PASSED: dma_smoke_test ***
--- UVM Report Summary ---
** Report counts by severity
UVM_INFO :    8
UVM_WARNING :    0
UVM_ERROR :    0
UVM_FATAL :    0""", "End of sim\\logs\\dma_smoke_test_s1.log")
H("4.1 How to read each line", 2)
T(["Line", "Meaning"], [
    ["Running test dma_smoke_test", "Which test (scenario) ran"],
    ["@ 5595000", "Simulation time in picoseconds: 5 595 000 ps = 5.6 us = 559 clock cycles at 100 MHz"],
    ["[COV] cfg=40.0% ...", "Functional coverage reached by THIS test alone (one test never covers everything - the merged number in Step 5 is what counts)"],
    ["[SCB] checks=110", "The scoreboard made 110 independent checks (addresses, burst lengths, data words, interrupts) - all passed"],
    ["rd_bursts / wr_bursts / wr_beats", "AXI read bursts, write bursts and write data beats seen on the bus"],
    ["arbitrations=8 (wins 4/4/0/0)", "8 arbitration decisions; how many each channel 0/1/2/3 won"],
    ["`*** TEST PASSED ***`", "Printed only when UVM_ERROR = 0 and UVM_FATAL = 0"],
    ["UVM_ERROR : 0, UVM_FATAL : 0", "No check failed. Any assertion failure, scoreboard mismatch or test check would be counted here"],
], [5.0, 11.6], caption="Reading a log")
H("4.2 What a test is allowed to print", 2)
T(["Message", "Harmless?", "Why"], [
    ["UVM release notes (`UVM_NO_DEPRECATED undefined`)", "Yes", "Standard UVM library banner"],
    ["[NO_DPI_TSTNAME]", "Yes", "Information from xsim's UVM package; the test name is passed by plusarg instead"],
    ["XSIM 43-4127 'Cover is not supported yet' (during build)", "Yes", "xsim ignores `cover property`; covergroups are used instead"],
    ["UVM_ERROR or UVM_FATAL with a count above 0", "**No**", "A real failure - see Step 10"],
], [7.6, 2.0, 7.0], caption="Expected messages")
H("4.3 Extra lines printed by specific tests", 2)
T(["Test", "Line to look for", "What it proves"], [
    ["dma_sensor_fusion_test", "[FUSION] CH1 radar 256 words done after 1120 cycles (and one line per channel)", "Radar (highest priority) finishes first; all four streams complete"],
    ["dma_priority_test", "[PRIO] equal-priority grant sequence: '{1,2,3,0,1,2,3,0,...}", "Round-robin between equal priorities"],
    ["dma_backpressure_test", "[BACKPRESSURE] cycles with a full sensor FIFO: 12561 (no data lost)", "Sensors were held off by a full FIFO and no word was lost"],
    ["dma_random_test", "[RANDOM] 40 random iterations completed, [SCB] checks=20089 ...", "About 20 000 automatic checks per run"],
], [4.0, 7.4, 5.2], caption="Scenario-specific results")
P("Quick way to list all results at once:", "j")
CODE("""findstr /C:"TEST PASSED" /C:"TEST FAILED" sim\\logs\\*.log
findstr /C:"UVM_ERROR :" sim\\logs\\*.log
findstr /C:"[FUSION]" /C:"[PRIO]" /C:"[BACKPRESSURE]" sim\\logs\\*.log""", "Command Prompt")
FIGURE("regression.png", "Expected regression result: 13 of 13 runs pass with 0 UVM_ERROR and 0 UVM_FATAL.", 13.0)
PAGEBREAK()

# ================================================================ 5
STEP(5, "Open the coverage reports")
H("5.1 Functional coverage", 2)
P("Double-click `sim\\report\\functional\\functionalCoverageReport\\dashboard.html` (it opens in your browser), then click "
  "**Groups**.", "j")
FIGURE("cov_functional.png", "Functional coverage report: overall score 100 %, all 7 covergroups at 100 %.")
T(["Column", "Meaning"], [
    ["Score", "Merged coverage of all 13 runs - should be 100"],
    ["Name", "The covergroup, e.g. dma_coverage::cg_arb (arbitration)"],
    ["Click a covergroup name", "Shows every coverpoint and cross with its bins and hit counts; a bin with 0 hits would be a test gap"],
], [4.0, 12.6], caption="Reading the functional report")
H("5.2 Code coverage", 2)
P("Open `sim\\report\\code\\codeCoverageReport\\dashboard.html` and click **Modules**.", "j")
FIGURE("cov_code.png", "Code coverage per module.")
T(["Module", "Statement", "Branch", "Condition", "Toggle"], [
    ["dma_top", "100", "94.1", "83.3", "71.6"], ["dma_channel", "100", "100", "97.2", "54.6"],
    ["dma_sfifo", "100", "100", "100", "99.5"], ["dma_arbiter", "100", "100", "100", "100"],
    ["dma_engine", "100", "100", "97.9", "92.0"],
], [4.6, 3.0, 3.0, 3.0, 3.0], caption="Expected values for the 5 RTL modules")
B(["**Only the 5 RTL modules matter** (dma_top, dma_channel, dma_sfifo, dma_arbiter, dma_engine). The other rows (tb_top, interfaces, dma_sva, dma_tb_pkg, uvm_pkg) are testbench code, so the overall totals at the top of the page are lower - that is normal.",
   "**Statement 100 %** means every line of the design was executed at least once.",
   "**Toggle** is lower for dma_top and dma_channel because the upper bits of 32-bit addresses never change in the small simulated memory - not a design gap.",
   "Click a module name to see the source code with covered and uncovered lines highlighted."])
PAGEBREAK()

# ================================================================ 6
STEP(6, "Run single tests with your own seeds")
P("You do not have to run the whole regression every time. Build once, then run any test:", "j")
CODE("""sim\\build.bat                                   (only needed once, or after changing a .sv file)
sim\\run_test.bat dma_priority_test
sim\\run_test.bat dma_random_test 42 100         (seed 42, 100 random iterations)
sim\\coverage_report.bat                         (update the HTML reports from the runs in sim\\cov)""", "Command Prompt")
T(["Argument", "Meaning", "Default"], [
    ["1: test name", "One of the 9 tests below", "-"],
    ["2: seed", "Random seed; a different seed gives different random stimulus", "1"],
    ["3: iterations", "Only for dma_random_test: number of random transfer groups", "25"],
], [3.4, 10.0, 3.2], caption="run_test.bat arguments")
T(["Test", "What it checks"], [
    ["dma_regs_test", "Register reset values, read/write, read-only, PSLVERR for unmapped addresses, write-1-to-clear"],
    ["dma_smoke_test", "One memory-to-memory and one sensor transfer"],
    ["dma_sensor_fusion_test", "Camera, radar, LiDAR and diagnostics at once; radar must finish first"],
    ["dma_burst_sweep_test", "All burst lengths 1-16 and 4 KB boundary splitting"],
    ["dma_priority_test", "Priority order and round-robin rotation"],
    ["dma_error_test", "SLVERR / DECERR on each channel, isolation and restart"],
    ["dma_cfg_err_test", "Zero length, unaligned addresses, START without EN, START while busy"],
    ["dma_backpressure_test", "Very slow memory: FIFOs fill, sensors wait, no data lost"],
    ["dma_random_test", "Constrained-random mix of everything"],
], [4.6, 12.0], caption="Available tests")
BOX("Good practice", ["Running dma_random_test with a few new seeds (for example 101, 202, 303) is a quick way to show "
                      "an examiner that the design is robust: every new seed generates different traffic and must still pass."])
PAGEBREAK()

# ================================================================ 7
STEP(7, "Look at the waveforms in the Vivado GUI")
P("Logs tell you *whether* the design works; waveforms show *how*. The script `sim\\run_gui.bat` opens the Vivado "
  "simulator window with the important signals already grouped:", "j")
CODE("""sim\\build.bat                              (if not built yet)
sim\\run_gui.bat dma_smoke_test
sim\\run_gui.bat dma_priority_test""", "Command Prompt")
N(["The Vivado simulator window opens and runs the test to the end (watch the Tcl Console at the bottom).",
   "Click the waveform tab. Press the **Zoom Fit** button in the waveform toolbar to see the whole run.",
   "Drag a box with the mouse over the area you want to zoom into; use the + and - zoom buttons to adjust.",
   "Right-click a bus such as `awaddr` > **Radix** > **Hexadecimal** to read addresses easily.",
   "`state` (engine FSM) is shown with its state names (IDLE, RD_AR, WR_W, ...).",
   "Every signal of the DUT is recorded: to add another one, find it in the **Scope** / **Objects** panels and drag it into the waveform.",
   "Close the window when finished. The waveform is also saved as `sim\\work\\gui_<test>.wdb` and can be reopened from the GUI (File > Open Waveform Database)."])
H("7.1 What to look for", 2)
FIGURE("wave_axi_burst.png", "dma_smoke_test - one AXI burst (zoom into about 380-1080 ns).")
T(["Check in the waveform", "Correct behaviour"], [
    ["arvalid / arready", "One-cycle handshake; araddr = source address, arlen = F (16 beats)"],
    ["rvalid ... rlast", "16 read beats, rlast on the 16th"],
    ["awvalid / awready, awaddr", "Address handshake for the write; awaddr = destination address"],
    ["wvalid ... wlast", "16 write beats, wlast exactly on the last beat"],
    ["bvalid, bresp = 0", "Write response OKAY ends the burst"],
    ["Next burst", "Addresses advance by 0x40 (16 words x 4 bytes)"],
], [5.0, 11.6], caption="Reading an AXI burst")
FIGURE("wave_priority.png", "dma_priority_test - 4 channels with priorities 3, 2, 1, 0 (zoom into 0-30 us).")
P("**Check:** `gnt_idx` stays at 3 until channel 3 is done (its `irq_ch` bit rises), then 2, then 1, then 0 - strict priority.", "j")
FIGURE("wave_roundrobin.png", "dma_priority_test - 4 channels with equal priority (zoom into about 46-54 us).")
P("**Check:** at every `grant_fire` pulse, `gnt_idx` moves to the next channel 1, 2, 3, 0, ... and `rr_ptr` follows - round-robin.", "j")
FIGURE("wave_sensor_stream.png", "dma_smoke_test - sensor stream on channel 1 (zoom into about 2.4-3.6 us).")
P("**Check:** `s_valid`/`s_ready` accept sensor words into the FIFO, the engine goes STR_RD -> WR_AW -> WR_W -> WR_B, "
  "the addresses advance by 0x20 per 8-beat burst, and `irq_ch[1]` and `irq` rise at the end.", "j")
BOX("Alternative without the GUI", ["Add `-testplusarg WAVES` to a batch run to write a standard `dma.vcd` file in "
    "sim\\work, which any VCD viewer (for example GTKWave) can open."])
PAGEBREAK()

# ================================================================ 8
STEP(8, "Run synthesis and read the reports")
CODE("""cd C:\\Projects\\ADAS_DMA_Subsystem\\synth
call ..\\sim\\env.bat
vivado -mode batch -source synth.tcl""", "Command Prompt")
P("Synthesis takes about one minute and ends with `SYNTHESIS DONE`. It writes three files in `synth\\`:", "j")
T(["File", "What to look for", "Expected"], [
    ["utilization_synth.rpt", "Table '1. Slice Logic': rows Slice LUTs and Slice Registers", "1 660 LUTs (2.62 %), 1 065 registers (0.84 %)"],
    ["utilization_synth.rpt", "Rows LUT as Memory, Block RAM Tile, DSPs", "128 LUT-RAM (the FIFOs and burst buffer), 0 BRAM, 0 DSP"],
    ["timing_synth.rpt", "'Design Timing Summary': WNS(ns)", "+1.742 ns (positive = timing met at 100 MHz)"],
    ["timing_synth.rpt", "The sentence below the summary", "All user specified timing constraints are met."],
    ["synth.log", "Last summary line", "0 Critical Warnings and 0 Errors"],
], [4.2, 6.6, 5.8], caption="Reading the synthesis reports")
B(["**WNS (Worst Negative Slack)** is the timing margin of the slowest path. Positive means the design can run at the "
   "constrained 100 MHz; negative would mean it is too slow.",
   "**WHS** is the hold-time margin; it must also be positive (0.227 ns expected).",
   "These are post-synthesis estimates; a full place-and-route would give final numbers."])
PAGEBREAK()

# ================================================================ 9
STEP(9, "Compare with the golden results")
P("If your run is correct, your numbers match this table exactly (the simulation is deterministic for a given seed).", "j")
T(["Test (seed)", "Simulation end time", "Result"], [
    ["dma_regs_test (1)", "5.01 us", "PASS"], ["dma_smoke_test (1)", "5.59 us", "PASS"],
    ["dma_sensor_fusion_test (1)", "176.69 us", "PASS"], ["dma_burst_sweep_test (1)", "109.52 us", "PASS"],
    ["dma_priority_test (1)", "56.09 us", "PASS"], ["dma_error_test (1)", "20.80 us", "PASS"],
    ["dma_cfg_err_test (1)", "11.99 us", "PASS"], ["dma_backpressure_test (1)", "75.73 us", "PASS"],
    ["dma_random_test (11)", "918.82 us", "PASS"], ["dma_random_test (12)", "1077.68 us", "PASS"],
    ["dma_random_test (13)", "846.75 us", "PASS"], ["dma_random_test (14)", "968.63 us", "PASS"],
    ["dma_random_test (15)", "992.73 us", "PASS"],
], [6.6, 5.0, 5.0], caption="Golden regression results (the time is the @ value of the TEST PASSED line)")
T(["Metric", "Expected value"], [
    ["Merged functional coverage", "100 %"],
    ["RTL statement coverage", "100 % on all 5 modules"],
    ["Radar completion in dma_sensor_fusion_test", "1 120 cycles, first of the four channels"],
    ["Equal-priority grant sequence", "1, 2, 3, 0, 1, 2, 3, 0, ..."],
    ["Synthesis", "1 660 LUTs, 1 065 FFs, WNS +1.742 ns"],
], [7.0, 9.6], caption="Other golden numbers")
PAGEBREAK()

# ================================================================ 10
STEP(10, "Analysing a failure (if a test ever fails)")
P("A failing test prints `*** TEST FAILED ***` and a non-zero UVM_ERROR count. To show what this looks like, four bugs were "
  "deliberately injected into a copy of the RTL; these are the real messages they produced:", "j")
CODE("""[SCB] CH0 DATA MISMATCH word 5 addr 0x00100014: got 0x00fb406c exp 0x00fb406d
[CHK] strict priority order wrong: '{0,1,2,3}
[SCB] CH2 read burst len 2 expected 1 (addr 0x00030ffc)
[CHK] CH1 err code: got 0x00000001 expected 0x00000002""", "Example error messages")
T(["Tag in the message", "Who reported it", "What it means"], [
    ["[SCB]", "Scoreboard (reference model)", "The bus traffic differs from the prediction: wrong data, address or burst length, or a stray burst"],
    ["[CHK]", "The test sequence", "A register value, interrupt or completion order is not what the test expected"],
    ["[TIMEOUT]", "The test sequence", "A channel never finished (no DONE/ERR interrupt within the allowed time)"],
    ["AXI: / APB: / Arbiter: / CH:", "An assertion (tb/sva/dma_sva.sv)", "A protocol or design rule was broken at that exact simulation time"],
    ["[AXI_SLV]", "AXI memory model", "Wrong WLAST position or missing WLAST"],
], [4.0, 4.6, 8.0], caption="Who reports what")
H("10.1 Debug procedure", 2)
N(["Open the log and search for the **first** `UVM_ERROR` - later errors are often consequences of the first.",
   "Note the time (`@ ... ps`), the channel and the message.",
   "Re-run only that test with the **same seed**: `sim\\run_test.bat <test> <seed>` - the failure repeats exactly.",
   "Open it in the GUI: `sim\\run_gui.bat <test> <seed>`, go to the reported time and look at req, gnt_idx, the engine `state` and the AXI signals of that channel.",
   "Fix the RTL, then run `sim\\regress.bat` again - **always the full regression after any change**."])

# ================================================================ 11
STEP(11, "Troubleshooting")
T(["Problem", "Cause", "Solution"], [
    ["'xvlog' / 'xsim' is not recognized", "Wrong Vivado path in sim\\env.bat", "Fix the path (Step 2) and check with xvlog --version"],
    ["Compile errors mentioning a file path", "Project in a very long path or a path with spaces", "Move the folder to e.g. C:\\Projects\\ADAS_DMA_Subsystem"],
    ["Nothing happens when typing sim\\regress.bat in PowerShell", "PowerShell does not run .bat the same way", "Use cmd, or type cmd /c sim\\regress.bat"],
    ["A run takes much longer than expected", "Antivirus scanning the many files xsim writes", "Exclude the project folder from real-time scanning, or just wait"],
    ["run_test.bat says the log file is not found", "build.bat was not run first", "Run sim\\build.bat once"],
    ["Coverage report is empty", "No runs in sim\\cov", "Run some tests first, then sim\\coverage_report.bat"],
    ["The GUI opens but the waveform is empty", "Test still running or waveform tab not selected", "Wait for the Tcl Console to show the test result, then press Zoom Fit"],
    ["Git Bash: 'xvlog.bat: command not found'", "Path in the .sh files", "Edit the export PATH line at the top of each sim\\*.sh file"],
], [5.0, 5.0, 6.6], caption="Common problems")

H("Quick reference card", 1)
T(["I want to ...", "Command (Command Prompt, in the project folder)"], [
    ["Run everything", "sim\\regress.bat"],
    ["Compile only", "sim\\build.bat"],
    ["Run one test", "sim\\run_test.bat dma_smoke_test"],
    ["Run random with my seed", "sim\\run_test.bat dma_random_test 42 100"],
    ["Update coverage reports", "sim\\coverage_report.bat"],
    ["See waveforms", "sim\\run_gui.bat dma_priority_test"],
    ["List pass/fail", "findstr /C:\"TEST PASSED\" /C:\"TEST FAILED\" sim\\logs\\*.log"],
    ["Synthesize", "cd synth  then  vivado -mode batch -source synth.tcl"],
], [5.4, 11.2], caption="Commands")

_TAIL = _SRC[_SRC.index("# ---------------------------------------------------------------- header / footer"):]
exec(_TAIL.replace("Milestone Report", "How to Run and Analyse"))
