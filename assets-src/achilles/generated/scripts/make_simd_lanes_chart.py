"""SIMD lanes chart: time per step for 1 robot, 4 robots (4 lanes) and 8 robots (8 lanes), each bar split into lanes.
usage: make_simd_lanes_chart.py simd_lanes_cloud.json out.svg"""
import json, sys
from html import escape
from svgchart import STYLE
d = json.load(open(sys.argv[1]))
best = lambda r: min(r["us_per_step"])
rows = [r for r in d["runs"] if (r["robots"], r["lanes"]) in ((1, 4), (4, 4), (8, 8))]
base = best(rows[0])
W, X0, X1, TMAX = 680, 196, 560, 5.0
xs = lambda t: X0 + (X1 - X0) * t / TMAX
LANE, GAP, ROWGAP = 8, 3, 34
body, y = [], 84
for r in rows:
    t, n, lanes = best(r), r["robots"], r["lanes"]
    h = lanes * LANE + (lanes - 1) * GAP
    body.append(f'<text class="b" x="0" y="{y + 12}">{escape(r["label"])}</text>')
    body.append(f'<text class="s m" x="0" y="{y + 30}">{escape(r["build"])}</text>')
    for k in range(lanes):
        yy = y + k * (LANE + GAP)
        if k < n:
            body.append(f'<rect x="{X0}" y="{yy}" width="{xs(t) - X0:.1f}" height="{LANE}" rx="2" style="fill:var(--s1)"/>')
        else:
            body.append(f'<rect x="{X0 + 0.5}" y="{yy + 0.5}" width="{xs(t) - X0 - 1:.1f}" height="{LANE - 1}" rx="2" fill="none" style="stroke:var(--axis)" stroke-dasharray="3 2"/>')
    body.append(f'<text class="s m" x="{xs(t) + 8:.1f}" y="{y + h / 2 + 4:.1f}">{t:.1f} µs</text>')
    mult = n * base / t
    body.append(f'<text class="b" x="{W}" y="{y + h / 2 + 2:.1f}" text-anchor="end" font-size="20">{"1" if abs(mult - 1) < 1e-9 else f"{mult:.1f}"}×</text>')
    y += h + ROWGAP
yax = y - ROWGAP + 16
body.append(f'<line class="axis" x1="{X0}" x2="{X1}" y1="{yax}" y2="{yax}"/>')
for t in range(0, 6):
    body.append(f'<line class="axis" x1="{xs(t):.1f}" x2="{xs(t):.1f}" y1="{yax}" y2="{yax + 4}"/>')
    body.append(f'<text class="s m c" x="{xs(t):.1f}" y="{yax + 18}">{t}</text>')
body.append(f'<text class="s m c" x="{(X0 + X1) / 2}" y="{yax + 38}">time for one step (µs)</text>')
body.append(f'<text class="s m e" x="{W}" y="44">robot-steps per</text>')
body.append(f'<text class="s m e" x="{W}" y="59">second, vs 1 robot</text>')
# legend
body.insert(0, f'<rect x="0" y="16" width="22" height="{LANE}" rx="2" style="fill:var(--s1)"/><text class="s" x="30" y="24">lane stepping a robot</text>'
               f'<rect x="200.5" y="16.5" width="21" height="{LANE - 1}" rx="2" fill="none" style="stroke:var(--axis)" stroke-dasharray="3 2"/><text class="s" x="230" y="24">idle lane</text>')
H = yax + 48
desc = (f"Time for one simulation step of a seven-link arm, drawn as one bar per SIMD lane. One robot in the default 4-lane build takes {best(rows[0]):.1f} microseconds with three lanes idle. "
        f"Four robots fill those lanes in {best(rows[1]):.1f} microseconds, {4*base/best(rows[1]):.1f} times the robot-steps per second. "
        f"Eight robots in the 8-lane AVX2 build take {best(rows[2]):.1f} microseconds, {8*base/best(rows[2]):.1f} times.")
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-8 0 {W + 16} {H}" role="img" aria-labelledby="t d">\n'
       f'  <title id="t">Robots per step by SIMD width</title>\n  <desc id="d">{escape(desc)}</desc>\n' + STYLE + "  " + "\n  ".join(body) + "\n</svg>\n")
open(sys.argv[2], "w").write(svg)
print(desc)
