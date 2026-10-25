"""
milestone_diagrams.py - draws the explanatory diagrams used in the milestone report
(docs/figures/m*.svg).  Pure Python, no packages needed.  Render to PNG with any browser.
"""
import os
from html import escape

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "figures")

INK, MUTED, LINE = "#1f2937", "#5b6472", "#64748b"
C = {  # fill, stroke
    "blue":   ("#e8f0fb", "#2f5d9a"),
    "green":  ("#e7f6ec", "#2f855a"),
    "orange": ("#fdf0e2", "#c05621"),
    "purple": ("#f1ecfb", "#6b46c1"),
    "grey":   ("#f1f3f5", "#6b7280"),
    "red":    ("#fdecec", "#c53030"),
    "teal":   ("#e6f5f5", "#2c7a7b"),
    "yellow": ("#fdf8e1", "#b7791f"),
    "navy":   ("#1e3a5f", "#1e3a5f"),
}


class Svg:
    def __init__(self, w, h, title=None):
        self.w, self.h, self.o = w, h, []
        self.o.append(f'<rect width="{w}" height="{h}" fill="#ffffff"/>')
        if title:
            self.text(w / 2, 26, title, size=17, weight="700", anchor="middle")

    def text(self, x, y, s, size=13, weight="400", anchor="start", color=INK, italic=False, mono=False):
        fam = ' font-family="Consolas, monospace"' if mono else ""
        st = ' font-style="italic"' if italic else ""
        self.o.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
                      f'text-anchor="{anchor}" fill="{color}"{fam}{st}>{escape(str(s))}</text>')

    def box(self, x, y, w, h, lines, col="blue", size=13, bold_first=True, rx=8, dash=False, align="middle"):
        f, s = C[col]
        d = ' stroke-dasharray="6 4"' if dash else ""
        self.o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{f}" stroke="{s}" stroke-width="1.6"{d}/>')
        if isinstance(lines, str):
            lines = [lines]
        lh = size + 4
        y0 = y + h / 2 - (len(lines) - 1) * lh / 2 + size * 0.35
        tx = x + w / 2 if align == "middle" else x + 10
        for i, ln in enumerate(lines):
            col_txt = "#ffffff" if col == "navy" else INK
            wt = "700" if (i == 0 and bold_first) else "400"
            sz = size if i == 0 else size - 1
            self.text(tx, y0 + i * lh, ln, size=sz, weight=wt, anchor=align if align == "middle" else "start", color=col_txt)

    def arrow(self, pts, label=None, lx=None, ly=None, color=LINE, dash=False, both=False, w=1.8, lsize=12, lanchor="middle"):
        p = " ".join(f"{x},{y}" for x, y in pts)
        d = ' stroke-dasharray="6 4"' if dash else ""
        ms = ' marker-start="url(#ah)"' if both else ""
        self.o.append(f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{w}"{d} marker-end="url(#ah)"{ms}/>')
        if label:
            if lx is None:
                (x1, y1), (x2, y2) = pts[0], pts[-1]
                lx, ly = (x1 + x2) / 2, (y1 + y2) / 2 - 6
            self.text(lx, ly, label, size=lsize, anchor=lanchor, color=MUTED)

    def line(self, x1, y1, x2, y2, color=LINE, w=1.4, dash=False):
        d = ' stroke-dasharray="5 4"' if dash else ""
        self.o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{w}"{d}/>')

    def circle(self, cx, cy, r, label, col="blue", sub=None):
        f, s = C[col]
        self.o.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{f}" stroke="{s}" stroke-width="2"/>')
        self.text(cx, cy + (0 if sub else 5), label, size=13, weight="700", anchor="middle")
        if sub:
            self.text(cx, cy + 17, sub, size=10.5, anchor="middle", color=MUTED)

    def note(self, x, y, s, color=MUTED, size=12, anchor="start", italic=True):
        self.text(x, y, s, size=size, anchor=anchor, color=color, italic=italic)

    def raw(self, s):
        self.o.append(s)

    def save(self, name):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
                f'height="{self.h}" font-family="Segoe UI, Arial, sans-serif">'
                '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                f'orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{LINE}"/></marker></defs>')
        with open(os.path.join(OUT, name + ".svg"), "w", encoding="utf8") as f:
            f.write(head + "\n".join(self.o) + "</svg>")


# ---------------------------------------------------------------- Milestone 1
def m1_cpu_vs_dma():
    s = Svg(1000, 430, "Data movement: processor-centric (before) vs DMA-centric (this project)")
    for x0, title, col in ((20, "BEFORE - CPU copies every word", "red"), (520, "AFTER - DMA subsystem moves data", "green")):
        f, st = C[col]
        s.raw(f'<rect x="{x0}" y="48" width="460" height="370" rx="10" fill="#fff" stroke="{st}" stroke-width="1.5"/>')
        s.text(x0 + 230, 72, title, size=14, weight="700", anchor="middle", color=st)
        for i, n in enumerate(["Camera", "Radar", "LiDAR"]):
            s.box(x0 + 15, 100 + i * 70, 100, 46, n, "orange")
        s.box(x0 + 345, 160, 100, 70, ["DDR", "memory"], "purple")
    # before
    s.box(170, 160, 120, 70, ["CPU", "load + store"], "red")
    for i in range(3):
        s.arrow([(135, 123 + i * 70), (170, 195)])
    s.arrow([(290, 195), (365, 195)], "every word", 327, 186)
    for i, t in enumerate(["- CPU busy moving data, not computing", "- latency + jitter under load",
                           "- radar packets wait behind camera copies", "- bottleneck in real-time operation"]):
        s.note(40, 330 + i * 20, t, color=C["red"][1])
    # after
    s.box(670, 160, 120, 70, ["DMA", "4 channels"], "green")
    s.box(670, 75, 120, 44, ["CPU"], "blue")
    for i in range(3):
        s.arrow([(635, 123 + i * 70), (670, 195)])
    s.arrow([(790, 195), (865, 195)], "AXI bursts", 827, 186)
    s.arrow([(700, 119), (700, 160)], dash=True)
    s.note(694, 145, "program (APB)", size=11, anchor="end")
    s.arrow([(760, 160), (760, 119)], dash=True)
    s.note(768, 145, "IRQ", size=11)
    for i, t in enumerate(["+ CPU only programs registers and handles IRQs", "+ bursts use the bus efficiently",
                           "+ radar (priority 3) served first", "+ errors reported per channel"]):
        s.note(540, 330 + i * 20, t, color=C["green"][1])
    s.save("m1_cpu_vs_dma")


def m1_soc_context():
    s = Svg(1000, 430, "Where the DMA subsystem sits inside the ADAS SoC")
    s.box(40, 60, 150, 60, ["CPU cluster", "perception SW"], "blue")
    s.box(40, 170, 150, 60, ["Interrupt", "controller"], "grey")
    s.box(260, 60, 150, 60, ["APB bridge", "(control bus)"], "grey")
    s.box(260, 300, 480, 56, ["AXI4 interconnect (data bus)"], "grey")
    s.box(450, 140, 200, 110, ["DMA subsystem", "dma_top", "APB slave + AXI4 master"], "green")
    s.box(800, 290, 160, 76, ["DDR controller", "+ memory"], "purple")
    s.box(800, 60, 160, 50, ["Camera I/F"], "orange")
    s.box(800, 125, 160, 50, ["Radar I/F"], "orange")
    s.box(800, 190, 160, 50, ["LiDAR I/F"], "orange")
    s.arrow([(190, 90), (260, 90)])
    s.arrow([(410, 90), (480, 90), (480, 140)], "register writes", 520, 84)
    for y in (85, 150, 215):
        s.arrow([(800, y), (650, y if y != 85 else 160)])
    s.note(680, 180, "sensor streams", size=11)
    s.note(680, 194, "(valid / ready)", size=11)
    s.arrow([(550, 250), (550, 300)], "AXI master", 600, 280)
    s.arrow([(740, 328), (800, 328)])
    s.arrow([(450, 220), (190, 200)], "irq_ch[3:0], irq", 330, 200)
    s.arrow([(115, 170), (115, 120)])
    s.arrow([(115, 120), (115, 120)])
    s.arrow([(190, 110), (230, 110), (230, 328), (260, 328)], dash=True)
    s.note(236, 260, "CPU reads", size=11)
    s.note(236, 274, "results", size=11)
    s.note(40, 400, "Control plane = APB (slow, simple).  Data plane = AXI4 bursts (fast).  The DMA is a slave on APB and a master on AXI.", size=12)
    s.save("m1_soc_context")


def m1_address_map():
    s = Svg(1000, 470, "Channel configuration registers - APB address map")
    rows = [("0x000 - 0x00C", "Global registers", "enable, status, irq summary, version", "navy"),
            ("0x100 - 0x13C", "Channel 0 window", "camera", "blue"),
            ("0x140 - 0x17C", "Channel 1 window", "radar", "blue"),
            ("0x180 - 0x1BC", "Channel 2 window", "LiDAR", "blue"),
            ("0x1C0 - 0x1FC", "Channel 3 window", "diagnostics", "blue"),
            ("other", "Unmapped", "access returns PSLVERR", "red")]
    for i, (a, n, d, col) in enumerate(rows):
        y = 55 + i * 62
        s.text(30, y + 33, a, size=12.5, mono=True)
        s.box(150, y, 280, 52, [n, d], col, size=13)
    s.text(720, 60, "One channel window (offset from base)", size=14, weight="700", anchor="middle")
    regs = [("+0x00", "CTRL", "RW", "EN, START, SRC_STREAM, PRIO, BLEN"),
            ("+0x04", "SRC", "RW", "source address (memory mode)"),
            ("+0x08", "DST", "RW", "destination address"),
            ("+0x0C", "LEN", "RW", "length in words (24 bit)"),
            ("+0x10", "INT_EN", "RW", "enable DONE / ERR interrupts"),
            ("+0x14", "INT_STAT", "W1C", "DONE / ERR flags"),
            ("+0x18", "STATUS", "RO", "ACTIVE, IN_FLIGHT, ERR_CODE, FIFO level"),
            ("+0x1C", "REMAIN", "RO", "words left in this transfer"),
            ("+0x20", "XFERRED", "RO", "words moved since START")]
    for i, (o, n, a, d) in enumerate(regs):
        y = 75 + i * 37
        col = {"RW": "blue", "RO": "green", "W1C": "orange"}[a]
        f, st = C[col]
        s.raw(f'<rect x="480" y="{y}" width="490" height="31" rx="5" fill="{f}" stroke="{st}" stroke-width="1.2"/>')
        s.text(490, y + 20, o, size=12, mono=True)
        s.text(545, y + 20, n, size=12.5, weight="700")
        s.text(625, y + 20, a, size=11.5, color=st, weight="700")
        s.text(665, y + 20, d, size=11.5)
    s.arrow([(430, 143), (478, 80)], dash=True)
    s.arrow([(430, 143), (478, 403)], dash=True)
    s.note(30, 455, "Channel n base = 0x100 + n x 0x40   |   RW = read/write   |   RO = read-only   |   W1C = write 1 to clear", size=12)
    s.save("m1_address_map")


def bitstrip(s, y, name, fields, total=32):
    # fields: list of (msb, lsb, label, col)
    x0, W = 120, 850
    bw = W / total
    s.text(20, y + 30, name, size=14, weight="700")
    for msb, lsb, lab, col in fields:
        x = x0 + (total - 1 - msb) * bw
        w = (msb - lsb + 1) * bw
        f, st = C[col]
        s.raw(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="44" fill="{f}" stroke="{st}" stroke-width="1.2"/>')
        rng = f"{msb}" if msb == lsb else f"{msb}:{lsb}"
        s.text(x + w / 2, y - 5, rng, size=10, anchor="middle", color=MUTED)
        sz = 11 if w > 60 else 9.5
        if w < 34:
            s.raw(f'<text x="{x + w/2 + 4:.1f}" y="{y + 40}" font-size="9.5" font-weight="700" fill="{INK}" '
                  f'transform="rotate(-90 {x + w/2 + 4:.1f} {y + 40})">{escape(lab)}</text>')
        else:
            s.text(x + w / 2, y + 27, lab, size=sz, weight="700", anchor="middle")


def m1_ctrl_bits():
    s = Svg(1000, 330, "Bit fields of the most important channel registers")
    bitstrip(s, 70, "CTRL", [(31, 12, "reserved", "grey"),
                             (11, 8, "BLEN", "purple"), (7, 6, "rsvd", "grey"), (5, 4, "PRIO", "orange"),
                             (3, 3, "rsvd", "grey"), (2, 2, "STRM", "teal"), (1, 1, "START", "green"), (0, 0, "EN", "blue")])
    bitstrip(s, 165, "STATUS", [(31, 14, "reserved", "grey"), (13, 8, "FIFO_LEVEL", "teal"), (7, 5, "rsvd", "grey"),
                                (4, 2, "ERR_CODE", "red"), (1, 1, "INFL", "orange"), (0, 0, "ACT", "green")])
    bitstrip(s, 255, "INT_STAT", [(31, 2, "reserved", "grey"), (1, 1, "ERR", "red"), (0, 0, "DONE", "green")])
    s.note(120, 318, "BLEN = beats-1 (0..15 = 1..16-beat bursts)  |  PRIO 3 = most critical  |  ERR_CODE: 0 none, 1 SLVERR, 2 DECERR, 3 bad config", size=11.5)
    s.save("m1_ctrl_bits")


def m1_arb_flow():
    s = Svg(1000, 470, "Arbitration scheme - one decision per burst")
    s.box(370, 50, 260, 46, ["Engine idle and >= 1 request"], "navy")
    s.box(370, 125, 260, 52, ["For every channel c", "req[c] = active & enabled & data ready"], "blue")
    s.box(370, 205, 260, 52, ["Find the highest PRIO[c]", "among requesting channels (0..3)"], "orange")
    s.raw('<polygon points="500,285 640,320 500,355 360,320" fill="#fdf8e1" stroke="#b7791f" stroke-width="1.6"/>')
    s.text(500, 316, "more than one channel", size=12.5, weight="700", anchor="middle")
    s.text(500, 333, "with that priority?", size=12.5, weight="700", anchor="middle")
    s.box(110, 295, 200, 50, ["no: that channel", "wins"], "green")
    s.box(690, 295, 230, 50, ["yes: first one at/after", "rr_ptr wins (round-robin)"], "teal")
    s.arrow([(500, 96), (500, 125)])
    s.arrow([(500, 177), (500, 205)])
    s.arrow([(500, 257), (500, 285)])
    s.arrow([(360, 320), (310, 320)], "no", 335, 312)
    s.arrow([(640, 320), (690, 320)], "yes", 665, 312)
    s.box(330, 385, 340, 46, ["grant_fire: engine takes gnt_idx"], "navy")
    s.arrow([(210, 345), (210, 408), (330, 408)])
    s.arrow([(805, 345), (805, 408), (670, 408)])
    s.text(500, 455, "then rr_ptr <= winner + 1, so the next tie starts after the last winner", size=12, anchor="middle", color=MUTED)
    s.note(690, 120, "Why per burst?", size=12, italic=False, color=INK)
    s.note(690, 138, "A critical sensor waits at most", size=11.5)
    s.note(690, 154, "ONE burst of another channel.", size=11.5)
    s.save("m1_arb_flow")


def m1_arb_example():
    s = Svg(1000, 415, "Arbitration example - grant given at each burst boundary")
    names = ["CH0 camera", "CH1 radar", "CH2 LiDAR", "CH3 diag"]
    strict = [1, 1, 2, 2, 2, 0, 0, 0, 3, 3]
    equal = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1]
    cols = {0: "orange", 1: "red", 2: "teal", 3: "purple"}
    groups = (("Different priorities (radar 3, LiDAR 2, camera 1, diag 0): strict priority order", strict, 60,
               ["P1", "P3", "P2", "P0"]),
              ("Equal priorities (all 2): round-robin - every channel gets every 4th burst", equal, 235,
               ["P2", "P2", "P2", "P2"]))
    for title, seq, y0, pr in groups:
        s.text(30, y0 + 4, title, size=13.5, weight="700")
        for r in range(10):
            s.text(235 + r * 72 + 33, y0 + 24, f"burst {r+1}", size=10.5, anchor="middle", color=MUTED)
        for ci, n in enumerate(names):
            y = y0 + 32 + ci * 30
            s.text(30, y + 18, f"{n} ({pr[ci]})", size=12)
            for r in range(10):
                x = 235 + r * 72
                if seq[r] == ci:
                    st = C[cols[ci]][1]
                    s.raw(f'<rect x="{x+2}" y="{y+2}" width="66" height="24" rx="4" fill="{st}" />')
                    s.text(x + 35, y + 19, "GRANT", size=10.5, weight="700", anchor="middle", color="#fff")
                else:
                    s.raw(f'<rect x="{x+2}" y="{y+2}" width="66" height="24" rx="4" fill="#f4f5f7" stroke="#e1e4e8"/>')
    s.note(30, 403, "Top: radar (2 bursts) is served first, then LiDAR (3), camera (3), diagnostics (2). Bottom: equal channels take turns.", size=12)
    s.save("m1_arb_example")


def m1_datapath():
    s = Svg(1000, 470, "Datapath architecture - store-and-forward through one burst buffer")
    s.box(30, 70, 170, 64, ["Memory source", "AXI read AR / R"], "purple")
    for i in range(4):
        s.box(30 + i * 8, 180 + i * 8, 170, 60, ["Sensor FIFO", "32 x 32-bit, per channel"] if i == 3 else [""], "teal")
    s.text(30, 290, "x4 (one per channel)", size=11, color=MUTED)
    s.raw('<polygon points="270,90 310,110 310,230 270,250" fill="#f1f3f5" stroke="#6b7280" stroke-width="1.6"/>')
    s.text(290, 175, "MUX", size=12, weight="700", anchor="middle")
    s.arrow([(200, 102), (270, 120)], "rdata", 232, 102)
    s.arrow([(224, 240), (270, 220)])
    s.text(300, 272, "fifo_rdata[cur]", size=12, anchor="middle", color=MUTED)
    s.box(360, 120, 200, 100, ["Burst buffer", "16 x 32-bit", "(LUT-RAM, no reset)"], "green")
    s.arrow([(310, 170), (360, 170)])
    s.box(620, 120, 160, 100, ["AXI write", "AW / W / B", "wdata = buf[cnt]"], "purple")
    s.arrow([(560, 170), (620, 170)])
    s.box(840, 120, 130, 100, ["Destination", "memory"], "purple")
    s.arrow([(780, 170), (840, 170)])
    # address path
    s.text(30, 345, "Address and size path", size=14, weight="700")
    s.box(30, 365, 200, 76, ["Channel context", "cur_src, cur_dst", "remaining"], "blue")
    s.box(290, 365, 220, 76, ["Burst sizing (min)", "BLEN+1, remaining,", "4 KB page room"], "orange")
    s.box(570, 365, 200, 76, ["LATCH stage", "rd_addr, wr_addr, beats"], "yellow")
    s.box(830, 365, 140, 76, ["ARADDR/ARLEN", "AWADDR/AWLEN"], "purple")
    s.arrow([(230, 403), (290, 403)])
    s.arrow([(510, 403), (570, 403)], "next_beats", 540, 395)
    s.arrow([(770, 403), (830, 403)])
    s.arrow([(670, 365), (670, 300), (460, 300), (460, 220)], dash=True)
    s.note(480, 292, "cnt indexes buffer", size=11)
    s.note(30, 460, "After every burst the engine reports beats moved; the channel adds beats x 4 to both addresses and subtracts beats from remaining.", size=12)
    s.save("m1_datapath")


def m1_controller():
    s = Svg(1000, 430, "Controller architecture - who decides what")
    s.box(30, 60, 200, 80, ["APB register block", "dma_top decoder", "global + channel regs"], "navy")
    for i in range(4):
        s.box(300, 55 + i * 82, 210, 66, [f"Channel controller {i}", "context, FIFO, req, IRQ"], "blue")
    s.box(590, 120, 160, 120, ["Arbiter", "priority", "+ round-robin"], "orange")
    s.box(810, 90, 170, 180, ["Engine FSM", "one burst at a time", "AXI master", "error capture"], "green")
    for i in range(4):
        y = 88 + i * 82
        s.arrow([(230, 100), (300, y)])
        s.arrow([(510, y), (590, 180)])
    s.note(522, 74, "req, prio", size=11)
    s.arrow([(750, 180), (810, 180)], "gnt_idx", 780, 172)
    s.arrow([(895, 270), (895, 380), (405, 380), (405, 367)], "upd, upd_beats, upd_err (burst finished)", 650, 373)
    s.box(30, 230, 200, 90, ["Interrupt outputs", "irq_ch[c] = |(INT_STAT & INT_EN)", "irq = |irq_ch"], "red")
    s.arrow([(300, 285), (230, 275)])
    s.note(30, 415, "Control decisions are split: channels decide IF they need the bus, the arbiter decides WHO gets it, the engine decides HOW the burst runs.", size=12)
    s.save("m1_controller")


def m1_hierarchy():
    s = Svg(1000, 330, "RTL module hierarchy (6 synthesizable SystemVerilog files)")
    s.box(390, 50, 220, 56, ["dma_top", "APB decode, global regs, IRQ OR"], "navy")
    s.box(40, 170, 250, 66, ["dma_channel  x4", "registers, context, burst size, IRQ"], "blue")
    s.box(375, 170, 250, 66, ["dma_arbiter", "priority + round-robin"], "orange")
    s.box(710, 170, 250, 66, ["dma_engine", "burst FSM, buffer, AXI4 master"], "green")
    s.box(65, 265, 200, 50, ["dma_sfifo", "32-word sensor FIFO"], "teal")
    for x in (165, 500, 835):
        s.arrow([(500, 106), (x, 170)])
    s.arrow([(165, 236), (165, 265)])
    s.box(760, 265, 200, 50, ["dma_pkg", "parameters, codes, offsets"], "grey", dash=True)
    s.note(700, 255, "imported by all modules", size=11)
    s.save("m1_hierarchy")


# ---------------------------------------------------------------- Milestone 2
def m2_channel_internal():
    s = Svg(1000, 500, "dma_channel - inside one channel controller")
    s.raw('<rect x="20" y="45" width="960" height="440" rx="12" fill="#fbfcfe" stroke="#2f5d9a" stroke-width="1.5" stroke-dasharray="7 5"/>')
    s.box(45, 70, 200, 110, ["Config registers", "EN, PRIO, BLEN,", "SRC_STREAM, SRC, DST,", "LEN, INT_EN"], "blue")
    s.box(45, 210, 200, 80, ["START decode", "cfg check: EN, LEN != 0,", "word-aligned addresses"], "yellow")
    s.box(300, 70, 210, 110, ["Run-time context", "active, cur_src, cur_dst,", "remaining, xferred,", "err_code"], "green")
    s.box(300, 210, 210, 80, ["Burst sizing", "min(BLEN+1, remaining,", "4 KB room)"], "orange")
    s.box(565, 210, 180, 80, ["Request register", "req_q, nb_q", "(registered for timing)"], "purple")
    s.box(565, 70, 180, 110, ["Sensor FIFO", "dma_sfifo 32 words", "s_ready = active & !full", "(full = back-pressure)"], "teal")
    s.box(300, 330, 210, 90, ["Interrupt logic", "INT_STAT (W1C)", "irq = |(INT_STAT & INT_EN)"], "red")
    s.box(565, 330, 180, 90, ["Read mux", "CTRL..XFERRED", "to APB prdata"], "grey")
    s.arrow([(245, 125), (300, 125)])
    s.arrow([(245, 250), (300, 150)])
    s.text(255, 196, "start_ok", size=12, anchor="end", color=MUTED)
    s.arrow([(405, 180), (405, 210)])
    s.arrow([(510, 250), (565, 250)])
    s.arrow([(655, 180), (655, 210)], "fifo level", 700, 200)
    s.arrow([(145, 290), (145, 375), (300, 375)], "start_bad", 220, 368)
    # ports
    s.arrow([(820, 230), (745, 230)], both=True)
    s.text(830, 225, "to arbiter / engine:", size=11.5, weight="700")
    s.text(830, 242, "req, prio, next_beats,", size=11)
    s.text(830, 257, "src/dst address", size=11)
    s.arrow([(840, 120), (745, 120)])
    s.text(850, 115, "sensor stream", size=11.5, weight="700")
    s.text(850, 132, "s_valid / s_data (in)", size=11)
    s.arrow([(745, 150), (840, 150)], dash=True)
    s.text(850, 155, "s_ready (out)", size=11)
    s.arrow([(870, 330), (870, 305), (535, 305), (535, 160), (512, 160)], dash=True)
    s.text(770, 350, "upd, upd_beats, upd_err", size=11)
    s.text(770, 365, "from the engine", size=11)
    s.arrow([(405, 420), (405, 460)])
    s.text(415, 455, "irq_ch[c]", size=11.5, weight="700")
    s.text(45, 334, "APB write", size=11.5, weight="700")
    s.arrow([(135, 330), (135, 292)], dash=True)
    s.save("m2_channel_internal")


def m2_channel_fsm():
    s = Svg(1000, 380, "Channel life-cycle (implemented with the 'active' flag)")
    s.circle(260, 200, 75, "IDLE", "grey", "active = 0")
    s.circle(740, 200, 80, "ACTIVE", "green", "requests bursts")
    s.arrow([(333, 180), (662, 180)], "START with valid config", 497, 170)
    s.arrow([(662, 222), (333, 222)], "last burst done -> DONE irq", 497, 242)
    s.raw('<path d="M 700 272 C 640 360, 360 360, 300 272" fill="none" stroke="#c53030" stroke-width="1.8" marker-end="url(#ah)"/>')
    s.text(500, 352, "SLVERR / DECERR -> ERR irq + ERR_CODE (restart later with a new START)", size=12, anchor="middle", color="#c53030")
    s.raw('<path d="M 210 135 C 150 40, 320 40, 290 128" fill="none" stroke="#b7791f" stroke-width="1.8" marker-end="url(#ah)"/>')
    s.text(250, 48, "START with bad config -> ERR_CFG (stays idle)", size=12, anchor="middle", color="#b7791f")
    s.raw('<path d="M 700 130 C 660 40, 840 40, 790 128" fill="none" stroke="#64748b" stroke-width="1.6" stroke-dasharray="6 4" marker-end="url(#ah)"/>')
    s.text(745, 48, "START while active: ignored", size=12, anchor="middle", color=MUTED)
    s.save("m2_channel_fsm")


def m2_arbiter_hw():
    s = Svg(1000, 360, "dma_arbiter - hardware structure")
    for i in range(4):
        y = 60 + i * 65
        s.box(30, y, 230, 48, [f"req[{i}], PRIO[{i}]  (from channel {i})"], "blue", size=12)
        s.arrow([(260, y + 24), (380, 180)])
    s.box(380, 100, 260, 160, ["Rotating scan", "for i in 0..3:", "idx = (rr_ptr + i) % 4", "keep the first requester with", "a strictly higher PRIO"], "orange")
    s.box(720, 90, 240, 70, ["gnt_valid, gnt_idx", "to the engine"], "green")
    s.box(720, 220, 240, 70, ["rr_ptr register", "<= gnt_idx + 1 on grant_fire"], "teal")
    s.arrow([(640, 150), (720, 125)])
    s.arrow([(840, 160), (840, 220)], dash=True)
    s.arrow([(720, 255), (640, 240)], "rr_ptr", 680, 236)
    s.note(380, 300, "Only one 2-bit register (rr_ptr) and combinational compare logic - very small.", size=12)
    s.save("m2_arbiter_hw")


def m2_engine_fsm():
    s = Svg(1000, 535, "Transfer state machine (dma_engine) - one burst per pass")
    P = {"IDLE": (90, 260), "LATCH": (240, 260), "RD_AR": (400, 130), "RD_DATA": (580, 130),
         "STR_RD": (490, 400), "WR_AW": (740, 260), "WR_W": (880, 140), "WR_B": (880, 400),
         "UPD": (690, 470), "SETTLE": (300, 450)}
    col = {"IDLE": "grey", "LATCH": "yellow", "RD_AR": "purple", "RD_DATA": "purple", "STR_RD": "teal",
           "WR_AW": "green", "WR_W": "green", "WR_B": "green", "UPD": "orange", "SETTLE": "orange"}
    R = 46
    for n, (x, y) in P.items():
        s.circle(x, y, R, n, col[n])

    def e(a, b, lab, dx=0, dy=-8, red=False):
        (x1, y1), (x2, y2) = P[a], P[b]
        import math
        d = math.hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1) / d, (y2 - y1) / d
        s.arrow([(x1 + ux * R, y1 + uy * R), (x2 - ux * (R + 2), y2 - uy * (R + 2))],
                color="#c53030" if red else LINE)
        s.text((x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy, lab, size=11, anchor="middle", color="#c53030" if red else MUTED)
    e("IDLE", "LATCH", "gnt_valid")
    e("LATCH", "RD_AR", "memory src", -40, 0)
    e("LATCH", "STR_RD", "sensor src", -50, 10)
    e("RD_AR", "RD_DATA", "arready")
    e("RD_DATA", "WR_AW", "rlast, OKAY", 55, 0)
    e("STR_RD", "WR_AW", "beats popped", -10, 32)
    e("WR_AW", "WR_W", "awready", -25, -5)
    e("WR_W", "WR_B", "wready & wlast", 55, 0)
    e("WR_B", "UPD", "bvalid", 20, -10)
    e("UPD", "SETTLE", "", 0, 0)
    e("SETTLE", "IDLE", "", 0, 0)
    s.raw('<path d="M 620 170 C 680 300, 700 360, 700 422" fill="none" stroke="#c53030" stroke-width="1.6" stroke-dasharray="6 4" marker-end="url(#ah)"/>')
    s.text(612, 296, "read error: skip the write", size=11, anchor="end", color="#c53030")
    s.note(20, 62, "Any non-OKAY response is stored in err and reported to the channel in UPD", size=12, color="#c53030")
    s.note(20, 525, "LATCH and SETTLE are one-cycle states added to meet 100 MHz timing (registered request).", size=12)
    s.save("m2_engine_fsm")


def m2_irq_logic():
    s = Svg(1000, 380, "Interrupt and status register logic (per channel, then global)")
    ev = [("done_now", "last word of the transfer moved", "green"),
          ("upd_err != 0  |  start_bad", "bus error (SLVERR/DECERR) or bad config", "red")]
    for i, (a, b, col) in enumerate(ev):
        s.box(30, 90 + i * 110, 260, 62, [a, b], col, size=12.5)
        s.arrow([(290, 121 + i * 110), (360, 180)])
    s.box(360, 140, 190, 90, ["INT_STAT[1:0]", "set has priority", "over W1C clear"], "orange")
    s.box(360, 280, 190, 60, ["APB write 1", "to INT_STAT -> clear"], "grey")
    s.arrow([(455, 280), (455, 230)])
    s.raw('<path d="M 610 150 L 640 150 A 35 35 0 0 1 640 220 L 610 220 Z" fill="#e8f0fb" stroke="#2f5d9a" stroke-width="1.6"/>')
    s.text(635, 190, "AND", size=11.5, weight="700", anchor="middle")
    s.arrow([(550, 170), (610, 170)])
    s.box(560, 290, 120, 50, ["INT_EN[1:0]"], "blue")
    s.arrow([(620, 290), (620, 220)])
    s.raw('<path d="M 720 150 Q 750 185 720 220 Q 790 220 820 185 Q 790 150 720 150 Z" fill="#e8f0fb" stroke="#2f5d9a" stroke-width="1.6"/>')
    s.text(760, 190, "OR", size=11.5, weight="700", anchor="middle")
    s.arrow([(675, 185), (728, 185)])
    s.arrow([(820, 185), (870, 185)])
    s.text(875, 180, "irq_ch[c]", size=12.5, weight="700")
    s.box(860, 260, 120, 64, ["irq = OR of", "irq_ch[3:0]"], "red")
    s.arrow([(910, 195), (910, 260)])
    s.note(30, 368, "STATUS (read-only) shows ACTIVE, IN_FLIGHT, ERR_CODE and FIFO level; REMAIN and XFERRED show progress.", size=12)
    s.save("m2_irq_logic")


def m2_sim_flow():
    s = Svg(1000, 260, "RTL simulation and regression flow (Vivado 2025.2 xsim)")
    st = [("xvlog -sv", "compile RTL + UVM TB", "blue"), ("xelab", "elaborate, code-cov on", "blue"),
          ("xsim x 13", "8 tests + 5 seeds", "green"), ("logs/*.log", "PASS / FAIL, UVM report", "grey"),
          ("xcrg", "merge coverage DBs", "orange"), ("HTML reports", "functional + code", "purple")]
    for i, (a, b, c) in enumerate(st):
        x = 20 + i * 165
        s.box(x, 80, 140, 70, [a, b], c, size=13)
        if i:
            s.arrow([(x - 25, 115), (x, 115)])
    s.note(20, 200, "One command:  sim\\regress.bat  (Windows)  or  sim/regress.sh  (Git Bash)", size=13, italic=False, color=INK)
    s.note(20, 225, "Single test with waveform:  xsim tb_snap -testplusarg UVM_TESTNAME=dma_smoke_test -testplusarg WAVES -R", size=12)
    s.save("m2_sim_flow")


# ---------------------------------------------------------------- Milestone 3
def m3_tb_arch():
    s = Svg(1000, 450, "SystemVerilog transaction-based testbench - tb_top")
    s.raw('<rect x="20" y="45" width="960" height="390" rx="12" fill="#fbfcfe" stroke="#1e3a5f" stroke-width="1.5"/>')
    s.text(40, 70, "tb_top", size=14, weight="700")
    s.box(40, 85, 170, 56, ["clock 100 MHz", "+ reset"], "grey")
    s.box(370, 175, 260, 150, ["DUT: dma_top", "", "APB slave | AXI4 master", "4 sensor ports | irq"], "green")
    s.box(370, 345, 260, 56, ["bound SVA: dma_sva, dma_ch_sva", "(bind - RTL untouched)"], "red", size=12)
    ifs = [("apb_if", 90, "blue"), ("axi_if", 175, "purple"), ("strm_if x4", 260, "teal"), ("dbg_if", 345, "yellow")]
    for n, y, c in ifs:
        s.box(240, y + 85 - 85 + 0, 100, 50, [n], c) if False else None
    for i, (n, c) in enumerate((("apb_if", "blue"), ("axi_if", "purple"), ("strm_if x4", "teal"), ("dbg_if (probe)", "yellow"))):
        y = 165 + i * 50
        s.box(690, y, 140, 40, [n], c, size=12)
        s.arrow([(690, y + 20), (630, 250)], both=True)
    s.box(40, 175, 250, 150, ["UVM world", "run_test()", "uvm_config_db passes", "virtual interfaces", "to agents"], "navy")
    s.arrow([(290, 250), (370, 250)], "transactions", 330, 242)
    s.arrow([(840, 185), (920, 185), (920, 120), (290, 120), (290, 175)], dash=True)
    s.note(560, 112, "virtual interface handles", size=11.5)
    s.arrow([(125, 141), (125, 175)])
    s.note(40, 420, "Transaction-based: tests create items (APB read/write, sensor words); drivers turn them into pin wiggles; monitors turn pins back into items.", size=12)
    s.save("m3_tb_arch")


def m3_uvm():
    s = Svg(1000, 560, "UVM environment - agents, sequences and analysis connections")
    s.box(20, 45, 960, 40, ["uvm_test_top : dma_<scenario>_test  (9 tests, one per scenario)"], "navy", size=13)
    s.raw('<rect x="20" y="100" width="960" height="440" rx="10" fill="#fbfcfe" stroke="#2f5d9a" stroke-width="1.4"/>')
    s.text(35, 122, "dma_env", size=14, weight="700")
    agents = [("apb_agent", "register programming", "blue", 40), ("strm_agent x4", "camera, radar, LiDAR, diag", "teal", 285),
              ("axi_agent", "reactive memory slave", "purple", 530)]
    for n, d, c, x in agents:
        f, stc = C[c]
        s.raw(f'<rect x="{x}" y="135" width="220" height="200" rx="8" fill="{f}" stroke="{stc}" stroke-width="1.5"/>')
        s.text(x + 110, 157, n, size=13.5, weight="700", anchor="middle")
        s.text(x + 110, 174, d, size=11, anchor="middle", color=MUTED)
        if c != "purple":
            s.box(x + 15, 188, 190, 36, ["sequencer"], "grey", size=12)
            s.box(x + 15, 238, 190, 36, ["driver"], "grey", size=12)
            s.arrow([(x + 110, 224), (x + 110, 238)])
        else:
            s.box(x + 15, 188, 190, 86, ["slave driver", "latency, back-pressure,", "error injection"], "grey", size=12)
        s.box(x + 15, 288, 190, 36, ["monitor"], "grey", size=12)
    s.box(775, 135, 190, 90, ["dma_vsqr", "virtual sequencer", "runs a scenario vseq"], "orange", size=12.5)
    s.box(775, 245, 190, 90, ["arb_monitor", "requests + grants", "via dbg_if"], "yellow", size=12.5)
    s.arrow([(775, 170), (762, 170), (762, 115), (150, 115), (150, 188)], dash=True)
    s.arrow([(395, 115), (395, 188)], dash=True)
    s.note(470, 130, "handles to sub-sequencers", size=11)
    s.box(120, 400, 330, 110, ["dma_scoreboard", "independent reference model", "address, length, data, IRQ,", "stray traffic, completeness"], "green")
    s.box(560, 400, 330, 110, ["dma_coverage", "7 covergroups", "cfg, axi, arb, irq, err, sensor, apb"], "orange")
    for x in (150, 395, 640):
        s.arrow([(x, 335), (285, 400)])
        s.arrow([(x, 335), (725, 400)])
    s.arrow([(870, 335), (870, 360), (725, 400)])
    s.arrow([(870, 360), (285, 400)])
    s.note(500, 532, "arrows = analysis ports (monitor -> subscribers)", size=11.5, anchor="middle")
    s.save("m3_uvm")


def m3_seq_flow():
    s = Svg(1000, 250, "How one stimulus flows: sequence -> driver -> DUT -> monitor -> checkers")
    st = [("virtual sequence", "e.g. dma_priority_vseq", "orange"), ("sub-sequence", "apb write CHn_CTRL", "orange"),
          ("sequencer", "arbitrates items", "grey"), ("driver", "drives the pins", "blue"),
          ("DUT", "dma_top", "green"), ("monitor", "pins -> item", "blue"), ("scoreboard", "+ coverage", "purple")]
    for i, (a, b, c) in enumerate(st):
        x = 12 + i * 141
        s.box(x, 80, 125, 70, [a, b], c, size=12)
        if i:
            s.arrow([(x - 16, 115), (x, 115)])
    s.note(12, 195, "start_item() / finish_item() hand the transaction to the driver; item_done() releases the next one.", size=12)
    s.note(12, 218, "The AXI side is reactive: the slave driver answers DUT requests from a memory model, with random latency and injected errors.", size=12)
    s.save("m3_seq_flow")


def m3_scoreboard():
    s = Svg(1000, 470, "Scoreboard and checking - independent reference model")
    s.box(20, 60, 200, 70, ["APB monitor", "every register write"], "blue")
    s.box(20, 170, 200, 70, ["Stream monitors x4", "every word a sensor sent"], "teal")
    s.box(20, 280, 200, 70, ["AXI monitor", "every burst + response"], "purple")
    s.box(290, 50, 260, 120, ["Channel model x4 (ch_model)", "built ONLY from APB writes:", "expected address, remaining,", "burst size = own min() formula"], "green")
    s.box(290, 190, 260, 70, ["Expected data", "memory snapshot at START / sensor queue"], "green")
    s.arrow([(220, 95), (290, 110)])
    s.arrow([(220, 205), (290, 225)])
    checks = ["address of every burst", "burst length = min(BLEN+1, rem, 4 KB)",
              "data of every beat, in order", "no stray burst outside a window",
              "DONE only when all words written", "ERR only when an error was injected", "end of test: every channel complete"]
    s.raw('<rect x="620" y="50" width="360" height="300" rx="10" fill="#fdf0e2" stroke="#c05621" stroke-width="1.5"/>')
    s.text(800, 75, "Checks (any mismatch = UVM_ERROR)", size=13.5, weight="700", anchor="middle")
    for i, c in enumerate(checks):
        s.text(640, 105 + i * 34, f"{i+1}.  {c}", size=12.5)
    s.arrow([(550, 110), (620, 120)])
    s.arrow([(550, 225), (620, 220)])
    s.arrow([(220, 315), (620, 300)], "actual traffic", 420, 300)
    s.box(290, 380, 690, 60, ["Mutation check: 4 deliberate RTL bugs injected (data bit flip, ignore priority, no 4 KB split,", "wrong error code) - every one was caught.  Proof the checker really checks."], "red", size=12.5, bold_first=False)
    s.save("m3_scoreboard")


def m3_assert_map():
    s = Svg(1000, 420, "Where the assertions watch the design (bound with SV 'bind')")
    s.box(330, 140, 340, 170, ["dma_top", "", "dma_channel x4   dma_arbiter", "dma_engine"], "green")
    groups = [(30, 60, "APB protocol (4)", ["setup -> access", "stable in setup", "PREADY, PSLVERR phase"], "blue"),
              (30, 250, "IRQ (1 + 4)", ["irq = OR(irq_ch)", "irq_ch = OR(STAT & EN)"], "red"),
              (720, 40, "AXI handshake (3)", ["AW / AR / W stable", "while VALID & !READY"], "purple"),
              (720, 160, "AXI legality (6)", ["size 4 B, INCR, aligned", "no 4 KB crossing", "WLAST position, one phase"], "purple"),
              (720, 300, "Arbitration (6)", ["grant only to requester", "winner has the highest", "priority (x4)"], "orange"),
              (330, 330, "Channel (8 x 4)", ["FIFO no under/overflow, s_ready legal,", "req legal, bad START never activates"], "teal")]
    for x, y, t, ls, c in groups:
        w = 340 if x == 330 else 250
        s.box(x, y, w, 80 if len(ls) < 3 else 96, [t] + ls, c, size=12.5)
    s.arrow([(280, 100), (330, 180)])
    s.arrow([(280, 290), (330, 260)])
    s.arrow([(720, 80), (670, 170)])
    s.arrow([(720, 208), (670, 220)])
    s.arrow([(720, 348), (670, 280)])
    s.arrow([(500, 330), (500, 310)])
    s.save("m3_assert_map")


def m3_cov_chart():
    data = [("cg_cfg  (configuration)", 100), ("cg_axi  (bursts, responses)", 100), ("cg_arb  (arbitration)", 100),
            ("cg_irq  (interrupt causes)", 100), ("cg_err  (error codes)", 100), ("cg_sensor  (back-pressure)", 100),
            ("cg_apb  (register access)", 100)]
    s = Svg(1000, 380, "Functional coverage per covergroup (merged over 13 runs) - overall 100 %")
    x0, W = 280, 620
    for t in (0, 25, 50, 75, 100):
        x = x0 + W * t / 100
        s.line(x, 50, x, 330, color="#e5e7eb", w=1)
        s.text(x, 348, f"{t} %", size=11, anchor="middle", color=MUTED)
    for i, (n, v) in enumerate(data):
        y = 58 + i * 39
        s.text(x0 - 12, y + 18, n, size=12.5, anchor="end")
        s.raw(f'<rect x="{x0}" y="{y+2}" width="{W*v/100:.1f}" height="24" rx="4" fill="#2f5d9a"/>')
        s.text(x0 + W * v / 100 + 8, y + 19, f"{v:g} %", size=12, weight="700")
    s.save("m3_cov_chart")


def f_flow():
    s = Svg(1000, 330, "The end-to-end project flow")
    steps = [("Problem", "ADAS sensors,", "CPU bottleneck", "orange"), ("Requirements", "R1 - R10", "", "orange"),
             ("Architecture", "blocks, registers,", "arbiter, FSM", "blue"), ("RTL", "6 SystemVerilog", "modules", "blue"),
             ("Testbench", "UVM agents,", "scoreboard", "green"), ("Tests", "8 directed +", "random x 5 seeds", "green"),
             ("Assertions", "25 SVA", "properties", "green"), ("Mutation check", "4 injected bugs,", "4 caught", "purple"),
             ("Coverage", "100 % functional,", "100 % statement", "purple"), ("Synthesis", "Artix-7,", "100 MHz met", "teal")]
    for i, (a, b, c, col) in enumerate(steps):
        row, k = divmod(i, 5)
        x = 30 + k * 192 if row == 0 else 30 + (4 - k) * 192
        y = 70 + row * 140
        s.box(x, y, 160, 80, [a, b, c] if c else [a, b], col, size=13)
        if k < 4:
            if row == 0:
                s.arrow([(x + 160, y + 40), (x + 192, y + 40)])
            else:
                s.arrow([(x, y + 40), (x - 32, y + 40)])
    s.arrow([(30 + 4 * 192 + 80, 150), (30 + 4 * 192 + 80, 210)])
    s.note(30, 318, "Any RTL change (e.g. after synthesis) sends the flow back to the full regression before the next step.", size=12)
    s.save("f_flow")


ALL = [m1_cpu_vs_dma, m1_soc_context, m1_address_map, m1_ctrl_bits, m1_arb_flow, m1_arb_example, m1_datapath,
       m1_controller, m1_hierarchy, m2_channel_internal, m2_channel_fsm, m2_arbiter_hw, m2_engine_fsm, m2_irq_logic,
       m2_sim_flow, m3_tb_arch, m3_uvm, m3_seq_flow, m3_scoreboard, m3_assert_map, m3_cov_chart, f_flow]

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for f in ALL:
        f()
    print(len(ALL), "diagrams written to", os.path.normpath(OUT))
