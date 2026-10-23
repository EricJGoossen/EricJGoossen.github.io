"""Render handover.npz (plan_handover.py) on the OpenArm model, offscreen with
MuJoCo: blue left arm, orange right arm, on the site's dark hero background.

  render_handover.py <handover.npz> <out_dir> [speedup] [first last]
Writes out_dir/frame_%05d.png at 30 fps (speedup x real time, default 4), or
only stills for frame indices first..last with STILLS=1.
"""
import os
import sys

os.environ.setdefault("MUJOCO_GL", "egl")
import mujoco  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from openarm.config import OpenarmConfig  # noqa: E402
import handover_scene  # noqa: E402

src, out = sys.argv[1], sys.argv[2]
speed = float(sys.argv[3]) if len(sys.argv) > 3 else 4.0
z = np.load(src)
path = OpenarmConfig.default().model_path
tmp = path.with_name("openarm_bimanual_handover_render_tmp.xml")
tmp.write_text(handover_scene.scene_xml(path.read_text(), float(z["table_z"]), float(z["can_half"]), floor=True))
try:
    m = mujoco.MjModel.from_xml_path(str(tmp))
finally:
    tmp.unlink()
d = mujoco.MjData(m)
names = lambda s: [f"openarm_{s}_joint{i}" for i in range(1, 8)]  # noqa: E731
adr = {s: [m.joint(n).qposadr[0] for n in names(s)] for s in ("left", "right")}
fin = {s: [m.joint(f"openarm_{s}_finger_joint{i}").qposadr[0] for i in (1, 2)] for s in ("left", "right")}
can = m.body("can_prop").mocapid[0]

m.vis.headlight.ambient[:] = 0.3
m.vis.headlight.diffuse[:] = 0.65
m.vis.headlight.specular[:] = 0.2
m.vis.quality.offsamples = 8
for g in range(m.ngeom):
    body = m.body(m.geom_bodyid[g]).name
    if m.geom_group[g] > 2:
        continue
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
cam.lookat[:] = [float(v) for v in os.environ.get("LOOKAT", "0.3 -0.42 0.45").split()]
cam.distance = float(os.environ.get("DIST", "1.9"))
cam.azimuth = float(os.environ.get("AZ", "205"))
cam.elevation = float(os.environ.get("EL", "-20"))
opt = mujoco.MjvOption()
BG = np.array([10, 11, 13])  # the floor's far color, so there is no horizon line

n = len(z["left"])
if os.environ.get("STILLS"):
    idx = range(int(sys.argv[4]), int(sys.argv[5]))
else:
    idx = np.arange(0, n, speed).round().astype(int)
os.makedirs(out, exist_ok=True)
for k, i in enumerate(idx):
    d.qpos[adr["left"]], d.qpos[adr["right"]] = z["left"][i], z["right"][i]
    d.qpos[fin["left"]] = z["fL"][i]
    d.qpos[fin["right"]] = z["fR"][i]
    d.mocap_pos[can] = z["can"][i]
    mujoco.mj_forward(m, d)
    renderer.update_scene(d, cam, opt)
    img = renderer.render().astype(float)
    sky = (img.sum(axis=2) == 0)[..., None]  # nothing drawn there
    img = np.where(sky, BG, img)
    Image.fromarray(img.astype(np.uint8)).save(f"{out}/frame_{k:05d}.png")
print("frames", len(idx), "of", n)
