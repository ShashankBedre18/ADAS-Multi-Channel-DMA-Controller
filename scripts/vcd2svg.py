"""
vcd2svg.py - render selected signals of a VCD file as a waveform SVG (for the report).

Usage:  python scripts/vcd2svg.py <file.vcd> <out.svg> <t0_ns> <t1_ns> "<title>" sig[=label][:enum] ...
  sig    full hierarchical name, e.g. tb_top.dut.awvalid
  :fsm   decode the value with the dma_engine state names
No third-party packages needed.
"""
import sys
from html import escape

FSM = ["IDLE", "RD_AR", "RD_DATA", "STR_RD", "WR_AW", "WR_W", "WR_B", "UPD", "SETTLE", "LATCH"]


def parse_vcd(path, wanted):
    ids, scope, changes = {}, [], {w: [] for w in wanted}
    t = 0
    with open(path) as f:
        for line in f:
            tok = line.split()
            if not tok:
                continue
            if tok[0] == "$scope":
                scope.append(tok[2])
            elif tok[0] == "$upscope":
                scope.pop()
            elif tok[0] == "$var":
                name = ".".join(scope + [tok[4]])
                if name in wanted:
                    ids.setdefault(tok[3], []).append((name, int(tok[2])))
            elif tok[0] == "$enddefinitions":
                break
        for line in f:
            line = line.strip()
            if not line:
                continue
            c = line[0]
            if c == "#":
                t = int(line[1:])
            elif c in "01xzXZ" and line[1:] in ids:
                for n, _ in ids[line[1:]]:
                    changes[n].append((t, c))
            elif c == "b":
                val, code = line[1:].split()
                for n, _ in ids.get(code, []):
                    changes[n].append((t, val))
    width = {n: w for v in ids.values() for n, w in v}
    return changes, width


def fmt(val, width, fsm):
    if any(ch in "xXzZ" for ch in val):
        return "x"
    v = int(val, 2)
    if fsm:
        return FSM[v] if v < len(FSM) else str(v)
    if width <= 4:
        return str(v)
    return f"{v:X}"


def main():
    vcd, out, t0, t1, title = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
    specs = []
    for a in sys.argv[6:]:
        fsm = a.endswith(":fsm")
        a = a[:-4] if fsm else a
        sig, _, label = a.partition("=")
        specs.append((sig, label or sig.split(".")[-1], fsm))
    changes, width = parse_vcd(vcd, {s for s, _, _ in specs})
    t0p, t1p = t0 * 1000, t1 * 1000  # ps

    LW, W, RH, TOP = 150, 1050, 30, 46
    H = TOP + RH * len(specs) + 34
    sx = lambda t: LW + (min(max(t, t0p), t1p) - t0p) / (t1p - t0p) * (W - LW - 10)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
         f'font-family="Consolas, monospace" font-size="11">',
         f'<rect width="{W}" height="{H}" fill="#0f1720"/>',
         f'<text x="12" y="24" fill="#e6edf3" font-family="Segoe UI, Arial" font-size="15" font-weight="600">{escape(title)}</text>']
    # time grid
    step = 10 ** len(str(int((t1 - t0) / 10))) / 10
    while (t1 - t0) / step > 14:
        step *= 2
    g = (int(t0 / step) + 1) * step
    while g < t1:
        x = sx(g * 1000)
        o.append(f'<line x1="{x:.1f}" y1="{TOP-6}" x2="{x:.1f}" y2="{H-28}" stroke="#263241" stroke-width="1"/>')
        o.append(f'<text x="{x:.1f}" y="{H-12}" fill="#8b98a5" text-anchor="middle">{g:g} ns</text>')
        g += step
    for i, (sig, label, fsm) in enumerate(specs):
        y = TOP + i * RH
        hi, lo = y + 5, y + RH - 7
        o.append(f'<text x="10" y="{(hi+lo)/2+4:.1f}" fill="#9fd3ff">{escape(label)}</text>')
        ch = changes.get(sig, [])
        w = width.get(sig, 1)
        # value at t0, then changes inside window
        cur = "x"
        seg = []
        for t, v in ch:
            if t <= t0p:
                cur = v
            elif t < t1p:
                seg.append((t, v))
        pts = [(t0p, cur)] + seg + [(t1p, None)]
        for (ta, va), (tb, _) in zip(pts, pts[1:]):
            xa, xb = sx(ta), sx(tb)
            if w == 1:
                yy = hi if va == "1" else lo if va == "0" else (hi + lo) / 2
                col = "#4ade80" if va in "01" else "#f87171"
                o.append(f'<line x1="{xa:.1f}" y1="{yy}" x2="{xb:.1f}" y2="{yy}" stroke="{col}" stroke-width="1.6"/>')
                if (ta, va) != pts[0]:
                    o.append(f'<line x1="{xa:.1f}" y1="{hi}" x2="{xa:.1f}" y2="{lo}" stroke="{col}" stroke-width="1.2"/>')
            else:
                txt = fmt(va, w, fsm)
                d = min(3, (xb - xa) / 2)
                col = "#f87171" if txt == "x" else "#fbbf24"
                o.append(f'<polygon points="{xa:.1f},{(hi+lo)/2} {xa+d:.1f},{hi} {xb-d:.1f},{hi} {xb:.1f},{(hi+lo)/2} '
                         f'{xb-d:.1f},{lo} {xa+d:.1f},{lo}" fill="none" stroke="{col}" stroke-width="1.2"/>')
                if xb - xa > 7 * len(txt) + 6:
                    o.append(f'<text x="{(xa+xb)/2:.1f}" y="{(hi+lo)/2+4:.1f}" fill="#e6edf3" text-anchor="middle">{escape(txt)}</text>')
    o.append("</svg>")
    open(out, "w").write("\n".join(o))
    print("wrote", out)


if __name__ == "__main__":
    main()
