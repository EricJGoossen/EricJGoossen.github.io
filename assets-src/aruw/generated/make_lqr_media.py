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


# Compact: the two measures side by side as horizontal bars, drawn at about the size it is shown.
W, H = 600, 236
c = Chart("LQR against pure pursuit on three paths", desc, w=W, h=H)
c.body = []
panels = [("time to finish (s)", 0, 12, [0, 4, 8, 12], 104, 330, lambda v: f"{v:.1f}"),
          ("farthest from the path (cm)", 2, 50, [0, 25, 50], 368, 580, lambda v: f"{v:.0f}" if v >= 10 else f"{v:.1f}")]
top, bar, pair_gap, group = 70, 13, 3, 50
for title, idx, hi, ticks, x0, x1, fmt in panels:
    X = lambda v: x0 + (x1 - x0) * v / hi  # noqa: E731
    c.label(x0, top - 14, title, cls="s m")
    for tv in ticks:
        c.body.append(f'<line class="grid" x1="{X(tv):.1f}" x2="{X(tv):.1f}" y1="{top - 4}" y2="{top + 3 * group - 10}"/>')
        c.label(X(tv), top + 3 * group + 4, f"{tv:g}", anchor="middle", cls="s m")
    for j, (n, lab) in enumerate(names):
        for k_, (who, var) in enumerate((("pure_pursuit", "--s2"), ("lqr", "--s1"))):
            v = S[n][who][idx]
            y = top + j * group + k_ * (bar + pair_gap)
            c.body.append(f'<rect x="{x0}" y="{y}" width="{X(v) - x0:.1f}" height="{bar}" rx="2" style="fill:var({var})"/>')
            c.label(X(v) + 5, y + bar - 2, fmt(v), cls="s")
        if x0 == panels[0][4]:
            name, length = lab.split(", ")
            c.label(x0 - 10, top + j * group + 12, name, anchor="end", cls="s")
            c.label(x0 - 10, top + j * group + 27, length, anchor="end", cls="s m")
c.body.append(f'<rect x="{panels[0][4]}" y="12" width="12" height="12" rx="2" style="fill:var(--s2)"/>')
c.label(panels[0][4] + 18, 23, "pure pursuit (the team's)")
c.body.append(f'<rect x="{panels[0][4] + 200}" y="12" width="12" height="12" rx="2" style="fill:var(--s1)"/>')
c.label(panels[0][4] + 218, 23, "LQR")
open(f"{out}/lqr-vs-pure-pursuit.svg", "w").write(c.svg())
print({n: S[n] for n, _ in names})
