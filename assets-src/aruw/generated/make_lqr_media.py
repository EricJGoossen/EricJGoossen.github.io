"""LQR against the team's pure pursuit, from EricJGoossen/LQRPathing's tools/compare_pure_pursuit
(branch finish-mvp), in the site's style.

  make_lqr_media.py <csv dir> <out dir>
<csv dir> holds slalom.csv, engineer.csv and square.csv (the tool's output for the waypoints in the
README). Writes <out>/frames/frame_NNNN.png (the slalom, both robots as dots, real time) and
<out>/lqr-vs-pure-pursuit.svg (time to finish and worst distance from the path, three paths).
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../achilles/generated/scripts"))
from svgchart import Chart  # noqa: E402

src, out = sys.argv[1], sys.argv[2]
BG, FG, MUTED, GRID = "#0f1114", "#e6e8eb", "#a39d97", "#2a2826"
BLUE, ORANGE = "#3987e5", "#e8703a"


def load(name):
    rows, summary = [], {}
    for line in open(os.path.join(src, name + ".csv")):
        if line.startswith("#"):
            who, rest = line[2:].split(" ", 1)
            nums = [float(w.rstrip(",")) for w in rest.replace("s,", "").split() if w.rstrip(",").replace(".", "").replace("-", "").isdigit()]
            summary[who] = nums
        elif not line.startswith("t,"):
            rows.append([float(v) for v in line.split(",")])
    return np.array(rows), summary


# ---------------------------------------------------------------- the slalom, animated
d, summ = load("slalom")
t, ppx, ppy, lqx, lqy, rx, ry = d.T
plan = np.array([rx, ry])
pp_done, lq_done = summ["pure_pursuit"][0], summ["lqr"][0]
os.makedirs(f"{out}/frames", exist_ok=True)
fps, step = 30, 1 / 30
frames = np.arange(0, t[-1] + 1.0, step)
xmin, xmax = min(ppx.min(), lqx.min()) - 0.35, max(ppx.max(), lqx.max()) + 0.35
ymin, ymax = min(ppy.min(), lqy.min()) - 0.35, max(ppy.max(), lqy.max()) + 0.95
for k, tk in enumerate(frames):
    i = min(np.searchsorted(t, tk), len(t) - 1)
    fig = plt.figure(figsize=(6.4, 6.4), dpi=150, facecolor=BG)
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96]); ax.set_facecolor(BG)
    ax.plot(rx, ry, color=GRID, lw=10, solid_capstyle="round")                 # the path
    ax.plot(rx, ry, color="#4a4744", lw=1.2, ls="--")
    ax.plot(ppx[: i + 1], ppy[: i + 1], color=ORANGE, lw=2, alpha=0.9)
    ax.plot(lqx[: i + 1], lqy[: i + 1], color=BLUE, lw=2, alpha=0.9)
    ax.plot(ppx[i], ppy[i], "o", ms=13, color=ORANGE, mec=FG, mew=1.2)
    ax.plot(lqx[i], lqy[i], "o", ms=13, color=BLUE, mec=FG, mew=1.2)
    ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax); ax.set_aspect("equal"); ax.axis("off")
    ax.text(xmin + 0.1, ymax - 0.12, f"{t[i]:4.1f} s", fontsize=13, color=FG, family="DejaVu Sans")
    lab = lambda done, name: f"{name}: done in {done:.1f} s" if t[i] >= done else name  # noqa: E731
    ax.text(xmin + 0.1, ymax - 0.32, lab(lq_done, "LQR"), fontsize=11, color=BLUE, family="DejaVu Sans")
    ax.text(xmin + 0.1, ymax - 0.50, lab(pp_done, "pure pursuit"), fontsize=11, color=ORANGE, family="DejaVu Sans")
    fig.savefig(f"{out}/frames/frame_{k:04d}.png", facecolor=BG)
    plt.close(fig)

# ---------------------------------------------------------------- the three paths, charted
names = [("slalom", "slalom, 11.7 m"), ("square", "square, 11.1 m"), ("engineer", "engineer's drive, 3.0 m")]
S = {n: load(n)[1] for n, _ in names}
desc = ("Both controllers on the same simulated chassis and the same three paths, at the same 2 m/s top speed. " +
        " ".join(f"{lab}: pure pursuit {S[n]['pure_pursuit'][0]:.1f} s and {S[n]['pure_pursuit'][2]:.0f} cm at worst, "
                 f"LQR {S[n]['lqr'][0]:.1f} s and {S[n]['lqr'][2]:.1f} cm." for n, lab in names))


def bars(c, key, idx, fmt, top):
    gap = (c.w - c.ml - c.mr) / len(names)
    for j, (n, lab) in enumerate(names):
        x0 = c.ml + j * gap + gap * 0.22
        for k_, (who, var) in enumerate((("pure_pursuit", "--s2"), ("lqr", "--s1"))):
            v = S[n][who][idx]
            x = x0 + k_ * gap * 0.3
            y = c.Y(v)
            c.body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{gap * 0.26:.1f}" height="{c.Y(0) - y:.1f}" rx="3" style="fill:var({var})"/>')
            c.label(x + gap * 0.13, y - 6, fmt(v), anchor="middle", cls="s")
        c.label(x0 + gap * 0.28, c.h - c.mb + 18, lab, anchor="middle", cls="s m")


c = Chart("LQR against pure pursuit on three paths", desc, w=680, h=560, ml=56, mr=20, mt=70, mb=290)
c.yscale(0, 12)
c.axes([], [0, 4, 8, 12], "", "time to finish (s)", yfmt=lambda v: f"{v:g}")
bars(c, "t", 0, lambda v: f"{v:.1f} s", 12)
top = c.body
c2 = Chart("", "", w=680, h=560, ml=56, mr=20, mt=330, mb=40)
c2.yscale(0, 50)
c2.axes([], [0, 10, 20, 30, 40, 50], "", "farthest from the path (cm)", yfmt=lambda v: f"{v:g}")
bars(c2, "max", 2, lambda v: f"{v:.0f}" if v >= 10 else f"{v:.1f}", 50)
c.body = top + c2.body
c.body.append('<rect x="56" y="14" width="14" height="14" rx="2" style="fill:var(--s2)"/>')
c.label(76, 26, "pure pursuit (the team's)")
c.body.append('<rect x="260" y="14" width="14" height="14" rx="2" style="fill:var(--s1)"/>')
c.label(280, 26, "LQR")
open(f"{out}/lqr-vs-pure-pursuit.svg", "w").write(c.svg())
print({n: S[n] for n, _ in names})
