"""Render gravcomp.npz (sim_gravcomp.py): the two arms from the front, blue left
arm with stiffness only, orange right arm with gravity compensation; the frames
turn a red border while both wrists are pushed. usage: render_gravcomp.py <npz> <out_dir>"""
import os
import sys

os.environ.setdefault("MUJOCO_GL", "egl")
import mujoco  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from openarm.config import OpenarmConfig  # noqa: E402

src, out = sys.argv[1], sys.argv[2]
z = np.load(src)
m = mujoco.MjModel.from_xml_path(str(OpenarmConfig.default().model_path))
d = mujoco.MjData(m)
J = {s: [m.joint(f"openarm_{s}_joint{i}").qposadr[0] for i in range(1, 8)] for s in ("left", "right")}
BLUE, ORANGE = np.array([0.30, 0.55, 0.95]), np.array([0.95, 0.55, 0.25])
m.vis.headlight.ambient[:] = 0.35
m.vis.headlight.diffuse[:] = 0.6
m.vis.quality.offsamples = 8
for g in range(m.ngeom):
    body = m.body(m.geom_bodyid[g]).name
    if m.geom_group[g] > 2:
        continue
    for side, rgb in (("openarm_left", BLUE), ("openarm_right", ORANGE)):
        if body.startswith(side):
            m.geom_matid[g] = -1
            m.geom_rgba[g] = (*rgb, 1)
W, H = 1000, 640
m.vis.global_.offwidth, m.vis.global_.offheight = W, H
r = mujoco.Renderer(m, H, W)
cam = mujoco.MjvCamera()
cam.type = mujoco.mjtCamera.mjCAMERA_FREE
cam.lookat[:] = [0.3, 0, 0.45]
cam.distance, cam.azimuth, cam.elevation = 1.5, 112, -24
opt = mujoco.MjvOption()
BG = np.array([15, 17, 20], float)
os.makedirs(out, exist_ok=True)
p0, p1 = z["push"]
for k in range(len(z["t"])):
    d.qpos[J["left"]], d.qpos[J["right"]] = z["left"][k], z["right"][k]
    mujoco.mj_forward(m, d)
    r.update_scene(d, cam, opt)
    img = (BG + r.render().astype(float) * (1 - BG / 255)).astype(np.uint8)
    if p0 <= z["t"][k] < p1:
        b = 8
        img[:b], img[-b:], img[:, :b], img[:, -b:] = (230, 60, 60), (230, 60, 60), (230, 60, 60), (230, 60, 60)
    Image.fromarray(img).save(f"{out}/frame_{k:04d}.png")
print("frames", len(z["t"]))
