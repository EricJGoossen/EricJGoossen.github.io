"""Render impedance4.npz (sim_impedance4.py) as four panels, one per controller:
the left arm in blue over a faint ghost of the pose it is holding, a red arrow
on the hand or the elbow while it is pushed.
usage: render_impedance4.py <npz> <out_dir>   (writes <out_dir>/<name>/frame_NNNN.png)"""
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
J = [m.joint(f"openarm_left_joint{i}").qposadr[0] for i in range(1, 8)]
BLUE = np.array([0.30, 0.55, 0.95])
m.vis.headlight.ambient[:] = 0.35
m.vis.headlight.diffuse[:] = 0.6
m.vis.quality.offsamples = 8
for g in range(m.ngeom):
    body = m.body(m.geom_bodyid[g]).name
    if m.geom_group[g] > 2:
        continue
    m.geom_matid[g] = -1
    m.geom_rgba[g] = (*BLUE, 1)
    if not body.startswith("openarm_left"):
        m.geom_group[g] = 5            # only the left arm is drawn
W, H = 640, 520
m.vis.global_.offwidth, m.vis.global_.offheight = W, H
r = mujoco.Renderer(m, H, W)
cam = mujoco.MjvCamera()
cam.type = mujoco.mjtCamera.mjCAMERA_FREE
cam.lookat[:] = [float(v) for v in os.environ.get("LOOKAT", "0.24 0.12 0.50").split()]
cam.distance = float(os.environ.get("DIST", 1.0))
cam.azimuth = float(os.environ.get("AZ", 215))
cam.elevation = float(os.environ.get("EL", -32))
opt = mujoco.MjvOption()
opt.geomgroup[5] = 0
opt.sitegroup[:] = 0
BG = np.array([15, 17, 20], float)


def shot(qpos, arrow=None):
    d.qpos[:] = qpos
    mujoco.mj_forward(m, d)
    r.update_scene(d, cam, opt)
    if arrow is not None:
        body, f = arrow
        tip = d.xpos[body]
        tail = tip - f / np.linalg.norm(f) * 0.18
        s = r.scene
        g = s.geoms[s.ngeom]
        mujoco.mjv_initGeom(g, mujoco.mjtGeom.mjGEOM_ARROW, np.zeros(3), np.zeros(3), np.zeros(9),
                            np.array([0.9, 0.25, 0.25, 1], np.float32))
        mujoco.mjv_connector(g, mujoco.mjtGeom.mjGEOM_ARROW, 0.012, tail, tip)
        s.ngeom += 1
    rgb = r.render().astype(float)
    r.enable_segmentation_rendering()
    seg = r.render()[..., 0] >= 0
    r.disable_segmentation_rendering()
    return rgb, seg


names = ("pure", "mixed", "null", "passthru")
ghost_q = z["pure"][0]
ghost, gmask = shot(ghost_q)
back = BG + (ghost - BG) * 0.4 * gmask[..., None]       # faint ghost of the held pose
for name in names:
    os.makedirs(f"{out}/{name}", exist_ok=True)
    for k, t in enumerate(z["t"]):
        arrow = None
        for (t0, t1, body), f in zip(z["pushes"], z["force"]):
            if t0 <= t < t1:
                arrow = (int(body), f)
        rgb, seg = shot(z[name][k], arrow)
        img = np.where(seg[..., None], BG + rgb * (1 - BG / 255), back).astype(np.uint8)
        Image.fromarray(img).save(f"{out}/{name}/frame_{k:04d}.png")
print("frames", len(z["t"]), "per panel")
