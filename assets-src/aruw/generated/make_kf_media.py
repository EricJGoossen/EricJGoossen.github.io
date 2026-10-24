"""Kalman-filter odometry media from Eric's competition logs (the odom_data.zip he sent, Oct 24;
not in the repo). Writes frames; ffmpeg turns them into the two clips (see README).

  make_kf_media.py <odom_data dir> <out dir>

1. auto/frame_NNNN.png: the engineer's autonomous drive at competition (Ozone_DataSampling_260630.csv,
   Jun 30): the filter's own logged pose, replayed at real time over the 5 m field image, with the
   planned stops from path.yaml. The log's first rows are a position reset (a jump from the origin
   to the start pose), which is cut.
2. sweep/frame_NNNN.png: offline tuning, with Eric's own replay tool (odo_tuner/field_odometry_replay.py,
   imported unchanged): his logged square run (deadwheel_log.csv) replayed while one tracking wheel's
   radius sweeps from 85% of its tuned value up to the tuned value. The closure error (distance from
   the end of the estimated path to its start) falls to its minimum at the tuned radius.
"""
import csv
import importlib.util
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import yaml  # noqa: E402
from matplotlib.patches import Polygon  # noqa: E402
from PIL import Image  # noqa: E402

src, out = sys.argv[1], sys.argv[2]
BG, FG, MUTED = "#0f1114", "#e6e8eb", "#a39d97"
BLUE, ORANGE, GREEN = "#3987e5", "#e8703a", "#2fbf8a"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "text.color": FG,
                     "axes.edgecolor": "#33312e", "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED})
field = Image.open(os.path.join(src, "field.png"))

# ---------------------------------------------------------------- 1. the autonomous drive
r = list(csv.DictReader(open(os.path.join(src, "Ozone_DataSampling_260630.csv"))))
col = lambda s: [c for c in r[0] if s in c][0]  # noqa: E731
t = np.array([float(a["Time"]) for a in r])
x = np.array([float(a[col("position).x")]) for a in r])
y = np.array([float(a[col("position).y")]) for a in r])
th = np.array([float(a[col("orientation")]) for a in r])
jump = np.argmax(np.hypot(np.diff(x), np.diff(y)) > 0.3) + 1        # the reset to the start pose
t, x, y, th = t[jump:] - t[jump], x[jump:], y[jump:], th[jump:]
stops = np.array(yaml.safe_load(open(os.path.join(src, "path.yaml")))["points"])
R = 0.2794                                                           # ROBOT_RADIUS in path.yaml's note
os.makedirs(f"{out}/auto", exist_ok=True)
fps = 30
for k, tk in enumerate(np.arange(0, t[-1] + 1.0, 1 / fps)):
    i = min(np.searchsorted(t, tk), len(t) - 1)
    fig = plt.figure(figsize=(6.4, 6.4), dpi=150, facecolor=BG)
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
    ax.imshow(field, extent=[0, 5, 0, 5], origin="upper", alpha=0.55)
    ax.set_xlim(0.2, 4.8); ax.set_ylim(0.2, 4.8); ax.axis("off")
    ax.plot(stops[:, 0], stops[:, 1], "o", ms=7, mfc="none", mec=FG, mew=1.5)
    for n, (sx, sy) in enumerate(stops):
        ax.text(sx + (-0.14 if sx < 2 else 0.14), sy, ("pickup " if n % 2 == 0 else "drop-off ") + str(n // 2 + 1),
                ha="right" if sx < 2 else "left", va="center", fontsize=9, color=MUTED)
    ax.plot(x[: i + 1], y[: i + 1], color=BLUE, lw=2.5)
    c, s = np.cos(th[i]), np.sin(th[i])
    corners = np.array([[R, R], [-R, R], [-R, -R], [R, -R]]) @ np.array([[c, s], [-s, c]]) + [x[i], y[i]]
    ax.add_patch(Polygon(corners, closed=True, fc=BLUE, ec=FG, alpha=0.35, lw=1.2))
    ax.annotate("", xy=(x[i] + 0.32 * c, y[i] + 0.32 * s), xytext=(x[i], y[i]),
                arrowprops=dict(arrowstyle="-|>", color=FG, lw=1.6))
    ax.text(0.3, 0.32, f"{t[i]:4.1f} s", fontsize=12, color=FG)
    fig.savefig(f"{out}/auto/frame_{k:04d}.png", facecolor=BG)
    plt.close(fig)
end = np.hypot(x[-1] - stops[-1, 0], y[-1] - stops[-1, 1])
print(f"auto: {t[-1]:.1f} s, {np.sum(np.hypot(np.diff(x), np.diff(y))):.2f} m, ends {end * 100:.1f} cm from the last stop")

# ---------------------------------------------------------------- 2. the radius sweep
sys.path.insert(0, os.path.join(src, "odo_tuner"))
spec = importlib.util.spec_from_file_location("replay", os.path.join(src, "odo_tuner", "field_odometry_replay.py"))
rp = importlib.util.module_from_spec(spec); spec.loader.exec_module(rp)
data = rp.load_csv(os.path.join(src, "odo_tuner", "deadwheel_log.csv"))
tuned = rp.PODS["p1"]["radius"]
fracs = np.r_[np.linspace(0.85, 1.0, 31), np.ones(1)]
paths = []
for f in fracs:
    pods = {k_: dict(v) for k_, v in rp.PODS.items()}
    pods["p1"]["radius"] = tuned * f
    xs, ys, _ = rp.simulate(data, pods=pods)
    paths.append((f, xs, ys, np.hypot(xs[-1] - xs[0], ys[-1] - ys[0])))
gt = np.array(rp.GROUND_TRUTH_PATH)
os.makedirs(f"{out}/sweep", exist_ok=True)
hold = {0: 20, len(fracs) - 1: 75}                                  # frames to hold first and last
k = 0
for j, (f, xs, ys, closure) in enumerate(paths):
    for _ in range(hold.get(j, 3)):
        fig = plt.figure(figsize=(6.4, 6.4), dpi=150, facecolor=BG)
        ax = fig.add_axes([0.06, 0.30, 0.88, 0.66])
        ax.set_facecolor(BG)
        ax.plot(gt[:, 0], gt[:, 1], "--", color=MUTED, lw=1.5)
        ax.plot(xs, ys, color=BLUE, lw=2.2)
        ax.plot(xs[0], ys[0], "o", color=GREEN, ms=8); ax.plot(xs[-1], ys[-1], "o", color=ORANGE, ms=8)
        ax.set_xlim(-0.35, 2.65); ax.set_ylim(-1.4, 1.8); ax.set_aspect("equal"); ax.axis("off")
        ax.text(-0.3, 1.68, "the square driven (dashed) and the filter's replayed estimate", fontsize=10, color=MUTED)
        ax2 = fig.add_axes([0.14, 0.08, 0.80, 0.17], facecolor=BG)
        fr = [p[0] for p in paths[:-1]]; cl = [p[3] * 100 for p in paths[:-1]]
        ax2.plot(fr, cl, color="#33312e", lw=1.5)
        ax2.plot(fr[: j + 1], cl[: j + 1], color=BLUE, lw=2)
        ax2.plot(f, closure * 100, "o", color=ORANGE, ms=7)
        ax2.set_xlim(0.845, 1.005); ax2.set_ylim(0, max(cl) * 1.1)
        ax2.set_xticks([0.85, 0.9, 0.95, 1.0]); ax2.set_xticklabels(["85%", "90%", "95%", "tuned"])
        ax2.set_ylabel("closure error (cm)", fontsize=9)
        for sp in ("top", "right"):
            ax2.spines[sp].set_visible(False)
        ax.text(-0.3, -1.33, f"wheel radius {tuned * f * 1000:.2f} mm ({f * 100:.0f}% of tuned)    "
                f"closure error {closure * 100:.0f} cm", fontsize=11, color=FG)
        fig.savefig(f"{out}/sweep/frame_{k:04d}.png", facecolor=BG)
        plt.close(fig)
        k += 1
print("sweep: closure from %.0f cm at 85%% to %.0f cm at the tuned radius" % (paths[0][3] * 100, paths[-1][3] * 100))
