"""SIMD chart: Achilles robot-steps/s vs robots stepped together, 4-lane SSE2 vs 8-lane AVX2 (seven-link arm, Euler).
usage: make_simd_chart.py throughput_summary.md out.svg"""
import re, sys
from svgchart import Chart
src, out = sys.argv[1], sys.argv[2]
rows, on = [], False
for line in open(src):
    if line.startswith("### "): on = line.strip() == "### seven_joint_arm / euler"; continue
    if on and re.match(r"\| \d", line):
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        rows.append((int(c[0]), float(c[1].replace(",", "")), float(c[3].replace(",", ""))))
N = [r[0] for r in rows]; avx = [r[1] for r in rows]; sse = [r[2] for r in rows]
print(rows)
c = Chart("Seven-link arm throughput by SIMD width",
          "Robot-steps per second on one laptop core, by how many robots Achilles steps together, for a seven-link arm at a 2 ms step. "
          "With one robot, most SIMD lanes are padding: 0.75 million steps per second with 8-lane AVX2 and 0.94 million with 4-lane SSE. "
          "Filling the lanes multiplies throughput: at 64 robots, AVX2 reaches 5.45 million, 7.2 times its one-robot rate, and SSE reaches 3.56 million.",
          h=400, mt=70)
c.xscale(1, 4096, log=True); c.yscale(0, 6e6)
c.axes([1, 4, 16, 64, 256, 1024, 4096], [0, 1e6, 2e6, 3e6, 4e6, 5e6, 6e6], "robots stepped together (log scale)", "robot-steps per second",
       xfmt=lambda v: f"{int(v):,}", yfmt=lambda v: "0" if v == 0 else f"{v/1e6:g}M")
c.line(N, sse, "--s2", width=2.25)
c.line(N, avx, "--s1", width=2.5)
for n, a, s in zip(N, avx, sse):
    c.body.append(f'<circle cx="{c.X(n):.1f}" cy="{c.Y(a):.1f}" r="3.5" style="fill:var(--s1)"/>')
    c.body.append(f'<circle cx="{c.X(n):.1f}" cy="{c.Y(s):.1f}" r="3.5" style="fill:var(--s2)"/>')
i = N.index(64)
c.label(c.X(64), c.Y(avx[i]) - 12, "5.45M: 7.2× one robot", anchor="middle", cls="s b")
c.label(c.X(1) + 10, c.Y(0.3e6), "1 robot: lanes mostly padding", cls="s m")
c.legend([("AVX2, 8 lanes", "--s1", False), ("SSE2, 4 lanes (default build)", "--s2", False)])
open(out, "w").write(c.svg())
