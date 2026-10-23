"""Stills from a recorded tour (tour.py), in the replay video's colors:
  merge.png  one moment: the front scan, the back scan, and the merged scan the
             merger publishes, side by side, around the robot
  map.png    the slam_toolbox map at the end of the run, with the robot's path

usage: render_stills.py tour.pkl out_dir [frame index for merge.png]
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
d = pickle.load(open(src, 'rb'))
F = d['frames']
k = int(sys.argv[3]) if len(sys.argv) > 3 else len(F) // 2
os.makedirs(out, exist_ok=True)
BG, UNKNOWN, FREE, OCC = '#0f1114', (0.13, 0.14, 0.16), (0.30, 0.31, 0.34), (0.92, 0.92, 0.90)
FRONT, BACK, MERGED, ROBOT, PATH = '#f28c38', '#3d8bfd', '#ffffff', '#e8e8e8', '#3ddc84'
L, W = 0.43, 0.36


def robot(ax, pose):
    x, y, th = pose
    c, s = np.cos(th), np.sin(th)
    corners = np.array([[L / 2, W / 2], [L / 2, -W / 2], [-L / 2, -W / 2], [-L / 2, W / 2]])
    ax.add_patch(Polygon(corners @ np.array([[c, s], [-s, c]]) + [x, y], closed=True, fc=ROBOT, ec=BG, lw=1))
    ax.plot([x, x + 0.3 * c], [y, y + 0.3 * s], color=BG, lw=2)


# --- merge.png ---------------------------------------------------------------
f = F[k]
fig, axs = plt.subplots(1, 3, figsize=(15, 5.4), dpi=100, facecolor=BG)
x, y, _ = f['pose']
for ax, (title, keys) in zip(axs, [('front lidar', [('front', FRONT)]), ('back lidar', [('back', BACK)]),
                                   ('merged scan', [('merged', MERGED)])]):
    ax.set_facecolor(BG)
    for key, color in keys:
        if f.get(key) is not None:
            ax.scatter(f[key][:, 0], f[key][:, 1], s=7, c=color, linewidths=0)
    robot(ax, f['pose'])
    ax.set_xlim(x - 4.2, x + 4.2)
    ax.set_ylim(y - 3.2, y + 3.2)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(title, color={'front lidar': FRONT, 'back lidar': BACK}.get(title, MERGED), fontsize=17,
                 weight='bold', loc='left')
fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.02, wspace=0.04)
fig.savefig(f'{out}/merge.png', facecolor=BG)
plt.close(fig)

# --- map.png -----------------------------------------------------------------
grid = next(fr['map'] for fr in reversed(F) if 'map' in fr)
g, res, ox, oy = grid
rgb = np.empty(g.shape + (3,))
rgb[:] = UNKNOWN
rgb[g == 0] = FREE
rgb[g > 50] = OCC
fig = plt.figure(figsize=(10.8, 7.8), dpi=100, facecolor=BG)
ax = fig.add_axes([0, 0, 1, 1], facecolor=BG)
ax.imshow(rgb, origin='lower', interpolation='nearest', extent=[ox, ox + g.shape[1] * res, oy, oy + g.shape[0] * res])
p = np.array([fr['pose'][:2] for fr in F])
ax.plot(p[:, 0], p[:, 1], color=PATH, lw=1.8, alpha=0.9)
robot(ax, F[-1]['pose'])
ax.set_xlim(-5.4, 5.4)
ax.set_ylim(-3.9, 3.9)
ax.set_aspect('equal')
ax.axis('off')
fig.savefig(f'{out}/map.png', facecolor=BG)
print('frame', k, 'of', len(F))
