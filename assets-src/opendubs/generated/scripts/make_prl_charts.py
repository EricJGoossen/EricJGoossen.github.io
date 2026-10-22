"""Charts for the OpenDubs log, in the site's chart style (Achilles' svgchart).

usage: make_prl_charts.py <data dir> <images dir>
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../achilles/generated/scripts"))
from svgchart import Chart  # noqa: E402

data, out = sys.argv[1], sys.argv[2]

# --- Optical flow EKF vs mocap, 2026-03-29 -----------------------------------
z = np.load(f"{data}/flow-ekf-vs-mocap-2026-03-29.npz")
t, err = z["t"], z["err"]
keep = np.arange(0, len(t), 5)  # 10 Hz is plenty for the line
drive = (t >= 60) & (t < 120)
spin_end = 135
c = Chart(
    "ArduPilot's position estimate against mocap, March 29 run",
    "Distance between the robot's position as estimated by ArduPilot's EKF, fusing the optical flow sensor, and its "
    f"true position from motion capture, over a 200-second run (log scale). While the robot drove 5.5 meters, the "
    f"estimate stayed within {err[drive].max():.2f} meters (mean {err[drive].mean():.2f}). The robot then spun about "
    f"205 degrees in place, and the estimate ran away to {err.max():.0f} meters while the robot itself moved less than "
    "half a meter.",
    h=360, mt=56, mb=56,
)
c.xscale(0, 202)
c.yscale(0.01, 300, log=True)
c.axes([0, 30, 60, 90, 120, 150, 180], [0.01, 0.1, 1, 10, 100], "time (s)", "position error vs mocap (m, log scale)",
       yfmt=lambda v: f"{v:g}")
for a, b, text, fill in [(0, 60, "parked", None), (60, 120, "driving, 5.5 m", "var(--grid)"),
                        (120, spin_end, "spin", "var(--s2)")]:
    x0, x1 = c.X(a), c.X(b)
    if fill:
        c.body.insert(0, f'<rect x="{x0:.1f}" y="{c.mt}" width="{x1 - x0:.1f}" height="{c.h - c.mt - c.mb}" '
                         f'style="fill:{fill}" fill-opacity="{0.55 if "grid" in fill else 0.18}"/>')
    c.label((x0 + x1) / 2, c.mt + 16, text, anchor="middle", cls="s m")
c.line(t[keep], np.maximum(err[keep], 0.01), "--s1")
c.label(c.X(202) - 4, c.Y(err.max()) - 8, f"{err.max():.0f} m", anchor="end", cls="s b")
open(f"{out}/flow-ekf-vs-mocap.svg", "w").write(c.svg())

# --- Bimanual plan executed one arm at a time vs together ----------------------
cz = np.load(f"{data}/bimanual-crossing.npz")
sz = np.load(f"{data}/bimanual-sequential.npz")
dur = float(cz["times"][-1])
hitsA, hitsB, planned = sz["hitsA"], sz["hitsB"], cz["planned_hits"]
rows = [
    ("Before: left arm, then right", [("left", 0, dur), ("right", dur, 2 * dur)], hitsA),
    ("Before: right arm, then left", [("right", 0, dur), ("left", dur, 2 * dur)], hitsB),
    ("After: both, one start stamp", [("left + right", 0, dur)], planned),
]
c = Chart(
    "One bimanual plan, executed one arm at a time and together",
    f"The same collision-free plan for both OpenArm arms ({dur:.1f} seconds), executed three ways and checked for "
    f"left-arm-against-right-arm contact at every step. Run one arm after the other, as multi-arm plans used to run, "
    f"it takes {2 * dur:.1f} seconds and the arms intersect at {hitsA.sum()} of {len(hitsA)} checked states "
    f"(left first) or {hitsB.sum()} of {len(hitsB)} (right first). Run together from one shared start time, it takes "
    f"{dur:.1f} seconds with no contact at any of {len(planned)} states.",
    w=680, h=250, ml=210, mr=24, mt=40, mb=48,
)
c.xscale(0, 2 * dur)
c.yscale(0, len(rows))
c.axes([0, 10, 20, 30, 40], [], "time (s)", "", xfmt=lambda v: f"{v:g}")
bar_h = 26
for r, (name, bars, hits) in enumerate(rows):
    yc = c.Y(len(rows) - r - 0.5)
    c.label(c.ml - 12, yc + 4, name, anchor="end")
    for label, a, b in bars:
        var = "--s3" if "+" in label else ("--s1" if label == "left" else "--s2")
        c.body.append(f'<rect x="{c.X(a):.1f}" y="{yc - bar_h / 2:.1f}" width="{c.X(b) - c.X(a) - 2:.1f}" '
                      f'height="{bar_h}" rx="4" style="fill:var({var})" fill-opacity="0.85"/>')
        c.body.append(f'<text class="s b" x="{(c.X(a) + c.X(b)) / 2:.1f}" y="{yc + 4:.1f}" text-anchor="middle" '
                      f'style="fill:#fff">{label}</text>')
    total = 2 * dur if len(bars) == 2 else dur
    for i in np.nonzero(hits)[0]:
        x = c.X(total * i / len(hits))
        c.body.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{yc + bar_h / 2 + 3:.1f}" y2="{yc + bar_h / 2 + 9:.1f}" '
                      'stroke="#dc2626" stroke-width="1.6"/>')
c.body.append(f'<line x1="{c.ml}" x2="{c.ml + 16}" y1="18" y2="18" stroke="#dc2626" stroke-width="2"/>')
c.label(c.ml + 22, 22, "left and right arm intersect", cls="s m")
open(f"{out}/bimanual-sequential-vs-sync.svg", "w").write(c.svg())
print("wrote charts")
