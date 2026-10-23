"""Render teleop.npz (sim_teleop.py): the two arms following the scripted hands,
each hand's target drawn as a small sphere in its arm's color.

  render_teleop.py <teleop.npz> <out_dir>
"""
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
adr = {s: [m.joint(f"openarm_{s}_joint{i}").qposadr[0] for i in range(1, 8)] for s in ("left", "right")}
fin = {s: [m.joint(f"openarm_{s}_finger_joint{i}").qposadr[0] for i in (1, 2)] for s in ("left", "right")}
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
W, H = 1000, 800
m.vis.global_.offwidth = max(m.vis.global_.offwidth, W)
m.vis.global_.offheight = max(m.vis.global_.offheight, H)
renderer = mujoco.Renderer(m, H, W)
cam = mujoco.MjvCamera()
cam.type = mujoco.mjtCamera.mjCAMERA_FREE
cam.lookat[:] = [0.22, 0, 0.45]
cam.distance, cam.azimuth, cam.elevation = 1.5, 205, -18
opt = mujoco.MjvOption()
BG = np.array([15, 17, 20], float)
os.makedirs(out, exist_ok=True)
for k in range(len(z["left"])):
    d.qpos[adr["left"]], d.qpos[adr["right"]] = z["left"][k], z["right"][k]
    d.qpos[fin["left"]], d.qpos[fin["right"]] = 0.03, 0.03
    mujoco.mj_forward(m, d)
    renderer.update_scene(d, cam, opt)
    for key, rgb in (("tL", BLUE), ("tR", ORANGE)):
        p = z[key][k]
        if np.all(np.isfinite(p)) and renderer.scene.ngeom < renderer.scene.maxgeom:
            g = renderer.scene.geoms[renderer.scene.ngeom]
            mujoco.mjv_initGeom(g, mujoco.mjtGeom.mjGEOM_SPHERE, np.full(3, 0.022), p, np.eye(3).ravel(),
                                np.array([*(0.55 + 0.45 * rgb), 0.55], np.float32))
            renderer.scene.ngeom += 1
    img = renderer.render().astype(float)
    Image.fromarray((BG + img * (1 - BG / 255)).astype(np.uint8)).save(f"{out}/frame_{k:04d}.png")
print("frames", len(z["left"]))
