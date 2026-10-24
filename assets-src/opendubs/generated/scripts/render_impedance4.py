"""Render impedance4.npz (sim_impedance4.py) as four panels, one per controller:
the left arm in blue over a faint ghost of where the plan has it at that moment,
a red arrow on the elbow while it is pushed. Each panel is labelled with its
controller and how far the arm is from the plan right now (the larger of the hand's
and the elbow's distance), colored by size; the motors' panel, the one that runs on
the robot, is framed.
usage: render_impedance4.py <npz> <out_dir> [font.otf]   (writes <out_dir>/<name>/frame_NNNN.png)"""
import os
import sys

os.environ.setdefault("MUJOCO_GL", "egl")
import mujoco  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from openarm.config import OpenarmConfig  # noqa: E402

src, out = sys.argv[1], sys.argv[2]
FONT = sys.argv[3] if len(sys.argv) > 3 else "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
TOP = int(os.environ.get("TOP", 105))   # the panel is cropped to 640x390 from this row down
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
LABEL = {"pure": "Cartesian", "mixed": "Cartesian, in joint space", "null": "Cartesian + null space",
         "passthru": "Motor PD + gravity (runs now)"}
hand_id, elbow_id = m.body("openarm_left_hand").id, m.body("openarm_left_link4").id
big, small = ImageFont.truetype(FONT, 26), ImageFont.truetype(FONT, 22)
GREEN, AMBER, RED, TEXT, MUTED = (111, 207, 151), (230, 180, 80), (240, 120, 80), (230, 232, 235), (163, 157, 151)


def points(q):
    d.qpos[:] = q
    mujoco.mj_kinematics(m, d)
    return d.xpos[hand_id].copy(), d.xpos[elbow_id].copy()


def off_plan(q, qref):
    (h, e), (hr, er) = points(q), points(qref)
    return max(np.linalg.norm(h - hr), np.linalg.norm(e - er))


def annotate(img, name, off):
    im = Image.fromarray(img)
    dr = ImageDraw.Draw(im)
    x, y = 22, TOP + 16
    dr.text((x, y), LABEL[name], font=big, fill=GREEN if name == "passthru" else TEXT)
    cm = off * 100
    color = GREEN if cm < 1 else AMBER if cm < 3 else RED
    dr.text((x, y + 36), "off plan", font=small, fill=MUTED)
    dr.text((x + dr.textlength("off plan  ", font=small), y + 36), f"{cm:4.1f} cm", font=small, fill=color)
    if name == "passthru":
        dr.rounded_rectangle((3, TOP + 3, W - 4, TOP + 386), radius=10, outline=GREEN, width=3)
    return np.asarray(im)


backs = []
for k in range(len(z["t"])):
    ghost, gmask = shot(z["ref"][k])
    backs.append(BG + (ghost - BG) * 0.4 * gmask[..., None])    # faint ghost of the plan
for name in names:
    os.makedirs(f"{out}/{name}", exist_ok=True)
    for k, t in enumerate(z["t"]):
        back = backs[k]
        arrow = None
        for (t0, t1, body), f in zip(z["pushes"], z["force"]):
            if t0 <= t < t1:
                arrow = (int(body), f)
        rgb, seg = shot(z[name][k], arrow)
        img = np.where(seg[..., None], BG + rgb * (1 - BG / 255), back).astype(np.uint8)
        img = annotate(img, name, off_plan(z[name][k], z["ref"][k]))
        Image.fromarray(img).save(f"{out}/{name}/frame_{k:04d}.png")
print("frames", len(z["t"]), "per panel")
