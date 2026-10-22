"""Render crossing.npz: the naive straight-line paths (left panel) and the
ArmGroup plan (right panel) on the OpenArm model, offscreen with MuJoCo.

  render_crossing.py <crossing.npz> <out_dir> [still]
Writes naive/frame_%04d.png and planned/frame_%04d.png (or one still per side).
"""
import os
import sys

os.environ.setdefault("MUJOCO_GL", "egl")
import mujoco  # noqa: E402
import numpy as np  # noqa: E402

from openarm.config import OpenarmConfig  # noqa: E402
from openarm.robot import Openarm  # noqa: E402

src, out = sys.argv[1], sys.argv[2]
still = len(sys.argv) > 3
z = np.load(src)
robot = Openarm(config=OpenarmConfig.default())
m, d = robot.model, robot.data
adr = lambda arm: [m.joint(n).qposadr[0] for n in arm.config.joint_names]  # noqa: E731
la, ra = adr(robot.left.arm), adr(robot.right.arm)

# Plain backdrop: dark sky, no fog, soft headlight.
m.vis.headlight.ambient[:] = 0.35
m.vis.headlight.diffuse[:] = 0.6
m.vis.rgba.haze[:] = [0.07, 0.08, 0.1, 1]
m.vis.quality.offsamples = 8

# Left arm blue, right arm orange (materials off so the rgba shows).
for g in range(m.ngeom):
    body = m.body(m.geom_bodyid[g]).name
    if m.geom_group[g] > 2:
        continue
    for side, rgba in (("openarm_left", (0.30, 0.55, 0.95, 1)), ("openarm_right", (0.95, 0.55, 0.25, 1))):
        if body.startswith(side):
            m.geom_matid[g] = -1
            m.geom_rgba[g] = rgba

m.vis.global_.offwidth = max(m.vis.global_.offwidth, 720)
m.vis.global_.offheight = max(m.vis.global_.offheight, 720)
W, H = 720, 720
renderer = mujoco.Renderer(m, H, W)
cam = mujoco.MjvCamera()
cam.type = mujoco.mjtCamera.mjCAMERA_FREE
cam.lookat[:] = [float(v) for v in os.environ.get("LOOKAT", "0.25 0 0.45").split()]
cam.distance = float(os.environ.get("DIST", "1.6"))
cam.azimuth = float(os.environ.get("AZ", "180"))
cam.elevation = float(os.environ.get("EL", "-18"))
opt = mujoco.MjvOption()

n = len(z["left"])
fps, speed = 30, 2.0
dur = float(z["times"][-1]) if z["times"][-1] > 0 else 22.4
idx = np.linspace(0, n - 1, int(dur / speed * fps)).round().astype(int)
if still:
    idx = np.array([int(os.environ.get("STILL", n // 2))])

for name, L, R, hits in [("naive", z["naive_left"], z["naive_right"], z["naive_hits"]),
                         ("planned", z["left"], z["right"], z["planned_hits"])]:
    os.makedirs(f"{out}/{name}", exist_ok=True)
    for k, i in enumerate(idx):
        d.qpos[la] = L[i]
        d.qpos[ra] = R[i]
        mujoco.mj_forward(m, d)
        renderer.update_scene(d, cam, opt)
        img = renderer.render().copy()
        if hits[i]:  # red outline while the two arms intersect
            b = 10
            img[:b], img[-b:], img[:, :b], img[:, -b:] = (230, 60, 60), (230, 60, 60), (230, 60, 60), (230, 60, 60)
        from PIL import Image
        Image.fromarray(img).save(f"{out}/{name}/frame_{k:04d}.png")
print("frames", len(idx), "samples", n)
