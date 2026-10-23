"""Render a recorded tour (tour.py) as a top-down video: slam_toolbox's map as it
grows, the front and back lidar scans, Eric's merged scan, Nav2's plan and goal,
and the robot's footprint.

usage: render_tour.py tour.pkl out_dir [speedup]
Writes out_dir/frame_%05d.png at 10 fps (speedup x real time, default 6).
"""
import os
import pickle
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Polygon  # noqa: E402

src, out = sys.argv[1], sys.argv[2]
speedup = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0
os.makedirs(out, exist_ok=True)
d = pickle.load(open(src, 'rb'))
F = d['frames']
stride = max(1, int(round(speedup / 2)))  # frames were recorded at 5 Hz; video is 10 fps
BG, UNKNOWN, FREE, OCC = '#0f1114', (0.13, 0.14, 0.16), (0.30, 0.31, 0.34), (0.92, 0.92, 0.90)
FRONT, BACK, MERGED, PLAN, ROBOT = '#f28c38', '#3d8bfd', '#ffffff', '#3ddc84', '#e8e8e8'
L, W = 0.43, 0.36  # Eric's frame_length / frame_width

fig = plt.figure(figsize=(9.6, 7.2), dpi=100, facecolor=BG)
ax = fig.add_axes([0, 0, 1, 1], facecolor=BG)
grid = None
trail = []
for k, f in enumerate(F[::stride]):
    i = k * stride
    for j in range(max(0, i - stride + 1), i + 1):  # newest map at or before this frame
        if 'map' in F[j]:
            grid = F[j]['map']
    trail.append(f['pose'][:2])
    ax.clear()
    ax.set_facecolor(BG)
    if grid is not None:
        g, res, ox, oy = grid
        rgb = np.empty(g.shape + (3,))
        rgb[:] = UNKNOWN
        rgb[g == 0] = FREE
        rgb[g > 50] = OCC
        ax.imshow(rgb, origin='lower', interpolation='nearest',
                  extent=[ox, ox + g.shape[1] * res, oy, oy + g.shape[0] * res])
    t = np.array(trail)
    ax.plot(t[:, 0], t[:, 1], color=ROBOT, lw=1, alpha=0.35)
    if f.get('plan') is not None and len(f['plan']):
        ax.plot(f['plan'][:, 0], f['plan'][:, 1], color=PLAN, lw=2, alpha=0.9)
    if f.get('goal'):
        ax.plot(*f['goal'], marker='*', ms=16, color=PLAN, mec=BG)
    for key, color, size in (('front', FRONT, 3), ('back', BACK, 3)):
        if f.get(key) is not None:
            ax.scatter(f[key][:, 0], f[key][:, 1], s=size, c=color, linewidths=0, alpha=0.9)
    x, y, th = f['pose']
    c, s = np.cos(th), np.sin(th)
    corners = np.array([[L / 2, W / 2], [L / 2, -W / 2], [-L / 2, -W / 2], [-L / 2, W / 2]])
    ax.add_patch(Polygon(corners @ np.array([[c, s], [-s, c]]) + [x, y], closed=True,
                         fc=ROBOT, ec=BG, lw=1, alpha=0.95))
    ax.plot([x, x + 0.3 * c], [y, y + 0.3 * s], color=BG, lw=2)
    ax.set_xlim(-5.4, 5.4)
    ax.set_ylim(-3.9, 3.9)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.text(0.015, 0.97, 'front lidar', color=FRONT, transform=ax.transAxes, fontsize=13, va='top', weight='bold')
    ax.text(0.015, 0.925, 'back lidar', color=BACK, transform=ax.transAxes, fontsize=13, va='top', weight='bold')
    ax.text(0.015, 0.88, 'Nav2 plan', color=PLAN, transform=ax.transAxes, fontsize=13, va='top', weight='bold')
    ax.text(0.985, 0.97, f'{speedup:g}× speed', color='#9a9a9a', transform=ax.transAxes, fontsize=12, va='top', ha='right')
    fig.savefig(f'{out}/frame_{k:05d}.png', facecolor=BG)
print('frames', k + 1)
