"""Chart of ik_deadzone.py's runs: Eric's July 13 OpenArm IK artifact with ssik just before
his fix (d0f8d21) and with it (38d1c7b), in the site's chart style.

usage: make_ik_fix_chart.py <ik-deadzone-pre.npz> <ik-deadzone-post.npz> <out.svg>
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../achilles/generated/scripts"))
from svgchart import Chart  # noqa: E402

pre, post = np.load(sys.argv[1]), np.load(sys.argv[2])
R, n = pre["r"], pre["ok"].shape[1]
a, b = pre["ok"].sum(1), post["ok"].sum(1)
c = Chart(
    "IK targets solved on the OpenArm, before and after the fix",
    f"For each distance from the straight-arm home configuration, {n} random joint configurations "
    "(every joint within that many radians of home, and within its limits), with their forward kinematics "
    "as the IK target. Before the fix, the solver found a solution for "
    f"{a.sum()} of {pre['ok'].size}; after it, {b.sum()} of {post['ok'].size}, including every target within "
    f"{R[np.flatnonzero(b < n)[0] - 1]:g} rad of home.",
    h=380, mt=96, mb=58,
)
c.xscale(-0.5, len(R) - 0.5)
c.yscale(0, n)
c.axes([], [0, 5, 10, 15, 20, 25], "every joint within ± this many radians of the straight arm", "")
c.label(c.ml - 8, c.mt - 30, f"targets solved (of {n})", cls="s m")
bw = (c.X(1) - c.X(0)) * 0.34
for i, r in enumerate(R):
    x = c.X(i)
    c.label(x, c.h - c.mb + 18, "0 (home)" if r == 0 else f"{r:g}", anchor="middle", cls="s m")
    for k, (v, var) in enumerate(((a[i], "--s2"), (b[i], "--s1"))):
        x0 = x - bw - 2 + k * (bw + 4)
        y = c.Y(v)
        h = max(c.Y(0) - y, 1.5)
        c.body.append(f'<rect x="{x0:.1f}" y="{c.Y(0) - h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="2" style="fill:var({var})"/>')
        c.label(x0 + bw / 2, c.Y(0) - h - 5, str(v), anchor="middle", cls="s m")
for k, (text, var) in enumerate((("before the fix", "--s2"), ("after the fix", "--s1"))):
    x = c.ml + k * 150
    c.body.append(f'<rect x="{x}" y="12" width="14" height="14" rx="2" style="fill:var({var})"/>')
    c.label(x + 20, 24, text)
open(sys.argv[3], "w").write(c.svg())
print("before", a, "after", b)
