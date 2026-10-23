"""Render the OpenDubs page hero: the two OpenArms running the ArmGroup plan from
crossing.npz on a dark background, framed with the arms on the right so the
project intro can sit over the left. Offscreen with MuJoCo.

  render_hero.py <crossing.npz> <out_dir> [still]
Writes out_dir/frame_%04d.png (1280x720), or one still with `still`.
"""
import os
import sys

os.environ.setdefault("MUJOCO_GL", "egl")
import mujoco  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from openarm.config import OpenarmConfig  # noqa: E402
from openarm.robot import Openarm  # noqa: E402

src, out = sys.argv[1], sys.argv[2]
still = len(sys.argv) > 3
z = np.load(src)
robot = Openarm(config=OpenarmConfig.default())
m, d = robot.model, robot.data
adr = lambda arm: [m.joint(n).qposadr[0] for n in arm.config.joint_names]  # noqa: E731
la, ra = adr(robot.left.arm), adr(robot.right.arm)

# Dark backdrop matching the site's hero panel (#0f1114), soft key light.
m.vis.headlight.ambient[:] = 0.3
m.vis.headlight.diffuse[:] = 0.65
m.vis.headlight.specular[:] = 0.2
m.vis.quality.offsamples = 8
COLORS = os.environ.get("COLORS", "1") == "1"
for g in range(m.ngeom):
    body = m.body(m.geom_bodyid[g]).name
    if m.geom_group[g] > 2:
        continue
    if COLORS:  # left arm blue, right arm orange, as in the log's crossing clip
        for side, rgba in (("openarm_left", (0.30, 0.55, 0.95, 1)), ("openarm_right", (0.95, 0.55, 0.25, 1))):
            if body.startswith(side):
                m.geom_matid[g] = -1
                m.geom_rgba[g] = rgba

W, H = 1280, 720
m.vis.global_.offwidth = max(m.vis.global_.offwidth, W)
m.vis.global_.offheight = max(m.vis.global_.offheight, H)
renderer = mujoco.Renderer(m, H, W)
cam = mujoco.MjvCamera()
cam.type = mujoco.mjtCamera.mjCAMERA_FREE
cam.lookat[:] = [float(v) for v in os.environ.get("LOOKAT", "0.25 -0.38 0.5").split()]
cam.distance = float(os.environ.get("DIST", "1.7"))
cam.azimuth = float(os.environ.get("AZ", "200"))
cam.elevation = float(os.environ.get("EL", "-14"))
opt = mujoco.MjvOption()
BG = np.array([15, 17, 20])  # empty space renders black; lift it to the panel color


def shade(img):
    return (BG + img * (1 - BG / 255)).round().astype(np.uint8)

n = len(z["left"])
fps, speed = 30, 1.5
dur = float(z["times"][-1]) if z["times"][-1] > 0 else 22.4
idx = np.linspace(0, n - 1, int(dur / speed * fps)).round().astype(int)
idx = np.r_[idx, idx[::-1]]  # there and back, so the loop has no jump
if still:
    idx = np.array([int(os.environ.get("STILL", n // 2))])

os.makedirs(out, exist_ok=True)
for k, i in enumerate(idx):
    d.qpos[la] = z["left"][i]
    d.qpos[ra] = z["right"][i]
    mujoco.mj_forward(m, d)
    renderer.update_scene(d, cam, opt)
    Image.fromarray(shade(renderer.render())).save(f"{out}/frame_{k:04d}.png")
print("frames", len(idx), "samples", n)
