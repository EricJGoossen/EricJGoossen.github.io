"""Charts of the optical-flow SITL runs (sitl_flow.py), in the site's chart style.

usage: make_flow_sim_charts.py <dir with flow-missing.npz, flow-fixed.npz, flow-tuned.npz> <images dir>
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../achilles/generated/scripts"))
from svgchart import Chart  # noqa: E402

src, out = sys.argv[1], sys.argv[2]
runs = [("missing", "mount missing from the config", "--s2"),
        ("fixed", "mount fixed", "--s4"),
        ("tuned", "mount fixed, flow gain tuned", "--s1")]
Z = {k: np.load(f"{src}/flow-{k}.npz") for k, _, _ in runs}

# Rotate every run into the drive's own frame: x forward along the drive, y to the right.
tr = Z["tuned"]["truth"]
far = tr[np.argmax(np.linalg.norm(tr, axis=1))]
a = np.arctan2(far[1], far[0])
Rm = np.array([[np.cos(a), np.sin(a)], [-np.sin(a), np.cos(a)]])


def frame(p):
    q = p @ Rm.T
    return q[:, 0], q[:, 1]           # x forward, y to the right (north-east, turned)


def err(z):
    return np.linalg.norm(z["truth"] - z["ekf"], axis=1)


E = {k: err(z) for k, z in Z.items()}
dist = np.abs(frame(tr)[0]).max()

# --- From above ---------------------------------------------------------------
c = Chart(
    "Simulated drive from above: true path and three estimates",
    f"Top-down view of a simulated run in ArduPilot SITL: the robot drives {dist:.1f} meters forward and back, then "
    "spins in place, navigating on optical flow alone. With the sensor's mounting missing from the config, the "
    f"estimate (orange) reads the drive as sideways motion and ends up {E['missing'].max():.1f} meters off. With the "
    f"mounting fixed (yellow) it follows the true path (dashed) but runs {E['fixed'].max():.1f} meters long; with the "
    f"flow gain tuned (blue), it stays within {E['tuned'].max():.1f} meters.",
    w=680, h=720, ml=56, mr=24, mt=84, mb=48,
)
c.xscale(-0.8, 9.6)
c.yscale(-1.0, 11.0)
c.axes([0, 2, 4, 6, 8], [0, 2, 4, 6, 8, 10], "forward (m)", "to the right (m)", xfmt=lambda v: f"{v:g}", yfmt=lambda v: f"{v:g}")
for v in [0, 2, 4, 6, 8]:
    c.body.insert(0, f'<line class="grid" x1="{c.X(v):.1f}" x2="{c.X(v):.1f}" y1="{c.mt}" y2="{c.h - c.mb}"/>')
k = slice(None, None, 10)
for name, label, var in runs:
    x, y = frame(Z[name]["ekf"])
    c.line(x[k], y[k], var, width=2.5)
x, y = frame(tr)
c.line(x[k], y[k], "--text", width=2, dash=True)
xm, ym = frame(Z["missing"]["ekf"])
i = np.argmax(np.hypot(xm, ym))
c.label(c.X(xm[i]) + 10, c.Y(ym[i]) + 4, "reads forward as sideways", cls="s b")
c.legend([("true path", "--text", True)] + [(lab, var, False) for _, lab, var in runs])
open(f"{out}/flow-sim-paths.svg", "w").write(c.svg())

# --- Error over time ------------------------------------------------------------
t = Z["tuned"]["t"]
c = Chart(
    "Simulated position error, three configurations",
    "Distance between ArduPilot's position estimate and the simulator's true position over the same simulated "
    "run (log scale): drive forward, drive back, spin in place. Mounting missing: "
    f"{E['missing'].max():.1f} m at worst. Mounting fixed: {E['fixed'].max():.2f} m. Flow gain tuned: "
    f"{E['tuned'].max():.2f} m, and {E['tuned'][-1]:.2f} m at the end.",
    h=380, mt=64, mb=56,
)
T = max(z["t"][-1] for z in Z.values())
c.xscale(0, T)
c.yscale(0.01, 30, log=True)
c.axes([0, 20, 40, 60], [0.01, 0.1, 1, 10], "time (s)", "position error (m, log scale)", yfmt=lambda v: f"{v:g}")
# phases from the tuned run's true motion
spd = np.r_[0, np.linalg.norm(np.diff(tr, axis=0), axis=1) / np.maximum(np.diff(t), 1e-3)]
yaw = Z["tuned"]["yaw"]
yr = np.r_[0, np.abs(np.diff(yaw)) / np.maximum(np.diff(t), 1e-3)]
moving = np.where(spd > 0.05)[0]
spinning = np.where((yr > 0.05) & (t > t[moving[-1]]))[0]
for a_, b_, text, fill in [(t[moving[0]], t[moving[-1]], "driving out and back", "var(--grid)"),
                           (t[spinning[0]], T, "spinning in place", "var(--s5)")]:
    x0, x1 = c.X(a_), c.X(b_)
    c.body.insert(0, f'<rect x="{x0:.1f}" y="{c.mt}" width="{x1 - x0:.1f}" height="{c.h - c.mt - c.mb}" '
                     f'style="fill:{fill}" fill-opacity="{0.55 if "grid" in fill else 0.12}"/>')
    c.label((x0 + x1) / 2, c.mt + 16, text, anchor="middle", cls="s m")
for name, label, var in runs:
    z = Z[name]
    k = slice(None, None, 10)
    c.line(z["t"][k], np.maximum(E[name][k], 0.01), var, width=2.5)
c.legend([(lab, var, False) for _, lab, var in runs])
open(f"{out}/flow-sim-error.svg", "w").write(c.svg())
print("missing %.2f fixed %.2f tuned %.2f (final %.2f) distance %.2f" % (
    E["missing"].max(), E["fixed"].max(), E["tuned"].max(), E["tuned"][-1], dist))
