"""Render cross.npz (plan_gripper_cross.py) as two panels side by side: each arm
planned on its own and run together (left; red while the arms intersect) and the
same goals planned together by ArmGroup (right), with each gripper's path drawn
as it goes. usage: render_gripper_cross.py <cross.npz> <out_dir>"""
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
site = {s: m.site(f"openarm_{s}_ee_site").id for s in ("left", "right")}
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
W, H = 640, 560
m.vis.global_.offwidth, m.vis.global_.offheight = W, H
r = mujoco.Renderer(m, H, W)
cam = mujoco.MjvCamera()
cam.type = mujoco.mjtCamera.mjCAMERA_FREE
cam.lookat[:] = [0.25, 0, 0.42]
cam.distance, cam.azimuth, cam.elevation = float(os.environ.get("DIST", 1.2)), float(os.environ.get("AZ", 200)), float(os.environ.get("EL", -40))
opt = mujoco.MjvOption()
BG = np.array([15, 17, 20], float)


def panel(L, R, k, trail):
    d.qpos[J["left"]], d.qpos[J["right"]] = L[k], R[k]
    mujoco.mj_forward(m, d)
    for s in trail:
        trail[s].append(d.site_xpos[site[s]].copy())
    r.update_scene(d, cam, opt)
    for s, rgb in (("left", BLUE), ("right", ORANGE)):
        pts = trail[s]
        for a, b in zip(pts[:-1], pts[1:]):
            if r.scene.ngeom >= r.scene.maxgeom:
                break
            g = r.scene.geoms[r.scene.ngeom]
            mujoco.mjv_initGeom(g, mujoco.mjtGeom.mjGEOM_CAPSULE, np.zeros(3), np.zeros(3), np.zeros(9),
                                np.array([*(0.5 + 0.5 * rgb), 1], np.float32))
            mujoco.mjv_connector(g, mujoco.mjtGeom.mjGEOM_CAPSULE, 0.004, a, b)
            r.scene.ngeom += 1
    return (BG + r.render().astype(float) * (1 - BG / 255)).astype(np.uint8)


n = max(len(z["L_solo"]), len(z["L_grp"])) + 30  # hold the end a second
tr_solo, tr_grp = {"left": [], "right": []}, {"left": [], "right": []}
os.makedirs(out, exist_ok=True)
for k in range(n):
    ks, kg = min(k, len(z["L_solo"]) - 1), min(k, len(z["L_grp"]) - 1)
    a = panel(z["L_solo"], z["R_solo"], ks, tr_solo)
    if z["h_solo"][ks]:
        b = 8
        a[:b], a[-b:], a[:, :b], a[:, -b:] = (230, 60, 60), (230, 60, 60), (230, 60, 60), (230, 60, 60)
    g = panel(z["L_grp"], z["R_grp"], kg, tr_grp)
    frame = np.concatenate([a, np.full((H, 6, 3), 40, np.uint8), g], axis=1)
    Image.fromarray(frame).save(f"{out}/frame_{k:04d}.png")
print("frames", n)
