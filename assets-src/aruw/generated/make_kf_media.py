"""Kalman-filter odometry media from Eric's competition logs (the odom_data.zip he sent, Oct 24;
not in the repo). Writes frames; ffmpeg turns them into the two clips (see README).

  make_kf_media.py <odom_data dir> <out dir>

1. auto/frame_NNNN.png: the engineer's autonomous drive at competition (Ozone_DataSampling_260630.csv,
   Jun 30): the filter's own logged pose, replayed at real time over the 5 m field image, with the
   planned stops from path.yaml, cut to the drive itself. The log's first rows are a position reset (a jump from the origin
   to the start pose), which is cut.
2. sweep/frame_NNNN.png: offline tuning, with Eric's own replay tool (odo_tuner/field_odometry_replay.py,
   imported unchanged): his logged 5 m sideways push (strafe.csv) replayed with the pods moving from
   their design values to his tuned ones, against the IMU heading in the same log. (The square run,
   deadwheel_log.csv, isn't used: its loop is about 1.5-1.7 m, not the 1.3 m square in the tool, so
   its closure has no reliable ground truth.)
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
# The robot waits about 10 s before it drives and about 10 s after it stops; keep the
# 4.2 s drive with half a second either side, and the clock counts from there.
speed = np.hypot(np.gradient(x, t), np.gradient(y, t))
moving = np.convolve(speed > 0.05, np.ones(25), "same") > 0       # bridge brief dips
edges = np.flatnonzero(np.diff(np.r_[0, moving.astype(int), 0]))
go_i, stop_i = max(zip(edges[::2], edges[1::2] - 1), key=lambda e: e[1] - e[0])   # the longest drive
go, stop = t[go_i], t[stop_i]
keep = (t >= go - 0.5) & (t <= stop + 0.5)
t, x, y, th = t[keep] - t[keep][0], x[keep], y[keep], th[keep]
stops = np.array(yaml.safe_load(open(os.path.join(src, "path.yaml")))["points"])
R = 0.2794                                                           # ROBOT_RADIUS in path.yaml's note
os.makedirs(f"{out}/auto", exist_ok=True)
fps = 30
for k, tk in enumerate(np.arange(0, t[-1] + 1.5, 1 / fps)):
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

# ---------------------------------------------------------------- 2. design values to tuned, on the strafe
# Eric's 5 m sideways push (strafe.csv), replayed through his own filter replica with the pods
# interpolated from their design values (rolling straight along the axes, 15.2 mm wheels, CAD
# positions) to his tuned ones. The log's IMU heading is the check: the robot really turned
# about 13 degrees while being pushed, and the wheels alone should say the same. The dashed
# reference is the IMU's version of the push: moving straight sideways in the robot's own frame
# (at the tuned wheels' speed) while turning as the IMU says, scaled to 5 m. A straight line
# along the starting heading would ignore that turn and leave even a perfect estimate ~10 degrees off it.
sys.path.insert(0, os.path.join(src, "odo_tuner"))
spec = importlib.util.spec_from_file_location("replay", os.path.join(src, "odo_tuner", "field_odometry_replay.py"))
rp = importlib.util.module_from_spec(spec); spec.loader.exec_module(rp)
data = rp.load_csv(os.path.join(src, "odo_tuner", "strafe.csv"))
rows = list(csv.DictReader(open(os.path.join(src, "odo_tuner", "strafe.csv"))))
imu = np.unwrap([float(a["((odometrySubsystem).imuTheta).wrapped"]) for a in rows])
imu = np.degrees(imu - imu[0])
ts = data["t"] - data["t"][0]
tuned = rp.PODS
design = {"p1": dict(theta=0.0, x=0.0, y=0.0777, radius=0.0152), "p2": dict(theta=0.0, x=0.0, y=-0.081, radius=0.0152),
          "perp": dict(theta=np.pi / 2, x=-0.1442, y=0.0, radius=0.0152)}
def body_side_speed(pods):
    AI = rp.build_AI(pods, rp.POD_ORDER)
    raw = np.stack([data[n] for n in rp.POD_ORDER], 1) * np.array([pods[n]["radius"] for n in rp.POD_ORDER])
    dt = np.minimum(np.diff(data["t"], prepend=data["t"][0]), rp.MAX_GAP_S)
    return (raw @ AI.T)[:, 1] * dt
step = body_side_speed(tuned)
ref_x, ref_y = np.cumsum(-step * np.sin(np.radians(imu))), np.cumsum(step * np.cos(np.radians(imu)))
scale = 5.0 / np.hypot(ref_x[-1], ref_y[-1]); ref_x, ref_y = ref_x * scale, ref_y * scale
fracs = np.r_[0.0, (1 - np.cos(np.linspace(0, np.pi, 40))) / 2]
runs = []
for f in fracs:
    pods = {n: {k_: design[n][k_] + f * (tuned[n][k_] - design[n][k_]) for k_ in design[n]} for n in design}
    xs, ys, yaws = rp.simulate(data, pods=pods, init_yaw=0.0, init_pos=(0.0, 0.0))
    runs.append((f, xs, ys, np.degrees(yaws), np.hypot(xs[-1], ys[-1]), np.hypot(xs[-1] - ref_x[-1], ys[-1] - ref_y[-1])))
os.makedirs(f"{out}/sweep", exist_ok=True)
hold = {0: 30, len(fracs) - 1: 90}                                  # frames to hold first and last
k = 0
for j, (f, xs, ys, yd, dist, miss) in enumerate(runs):
    for _ in range(hold.get(j, 2)):
        fig = plt.figure(figsize=(6.4, 6.4), dpi=150, facecolor=BG)
        ax = fig.add_axes([0.06, 0.36, 0.88, 0.58]); ax.set_facecolor(BG)
        ax.plot(ref_x, ref_y, "--", color=FG, lw=1.4)
        ax.plot(xs, ys, color=BLUE, lw=2.4)
        ax.plot(xs[0], ys[0], "o", color=GREEN, ms=8); ax.plot(xs[-1], ys[-1], "o", color=ORANGE, ms=8)
        ax.set_xlim(-3.3, 3.3); ax.set_ylim(-5.6, 0.6); ax.set_aspect("equal"); ax.axis("off")
        ax.text(-3.25, 0.35, "the 5 m push sideways, as the wheels see it", fontsize=10, color=MUTED)
        m = np.searchsorted(-ref_y, 3.0)
        ax.text(ref_x[m] + 0.25, ref_y[m], "dashed: where the\nIMU's heading\nsays it went", fontsize=9, color=MUTED, va="center")
        ax2 = fig.add_axes([0.13, 0.08, 0.82, 0.22], facecolor=BG)
        ax2.plot(ts, imu, "--", color=FG, lw=1.4, label="IMU")
        ax2.plot(ts, yd, color=BLUE, lw=2, label="wheels")
        ax2.set_ylim(-30, 100); ax2.set_xlim(0, ts[-1])
        ax2.set_ylabel("heading (°)", fontsize=9); ax2.set_xlabel("time (s)", fontsize=9)
        ax2.legend(loc="upper left", frameon=False, fontsize=9, ncol=2)
        for sp in ("top", "right"):
            ax2.spines[sp].set_visible(False)
        label = "design values" if f == 0 else ("tuned" if f == 1 else f"{f * 100:.0f}% of the way to tuned")
        ax.text(-3.25, -5.5, f"pods: {label}    distance {dist:.2f} m    heading {yd[-1]:+.0f}° (IMU {imu[-1]:+.0f}°)",
                fontsize=10.5, color=FG)
        fig.savefig(f"{out}/sweep/frame_{k:04d}.png", facecolor=BG)
        plt.close(fig)
        k += 1
print("strafe: design %.2f m, heading %+.1f, %.0f cm off the IMU's path; tuned %.2f m, heading %+.1f, %.0f cm off; IMU %+.1f" %
      (runs[0][4], runs[0][3][-1], 100 * runs[0][5], runs[-1][4], runs[-1][3][-1], 100 * runs[-1][5], imu[-1]))
