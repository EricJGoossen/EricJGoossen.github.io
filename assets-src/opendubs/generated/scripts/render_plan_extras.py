"""Two more renders from crossing.npz (plan_crossing.py), offscreen with MuJoCo:

  traces.png        the ArmGroup plan as a strobe: both arms at several moments,
                    faint to solid, with the paths both grippers trace
  sequential/       frames of the same plan run one arm at a time (left arm, then
                    right), outlined in red while the arms intersect

  render_plan_extras.py <crossing.npz> <out_dir>
"""
import os
import sys

os.environ.setdefault("MUJOCO_GL", "egl")
import mujoco  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from openarm.config import OpenarmConfig  # noqa: E402
from openarm.robot import Openarm  # noqa: E402

sys.path.insert(0, "/home/user/prl/openarm/tests")
from test_openarm_bimanual_planning import _cross_arm_contacts  # noqa: E402

src, out = sys.argv[1], sys.argv[2]
z = np.load(src)
robot = Openarm(config=OpenarmConfig.default())
m, d = robot.model, robot.data
adr = lambda arm: [m.joint(n).qposadr[0] for n in arm.config.joint_names]  # noqa: E731
la, ra = adr(robot.left.arm), adr(robot.right.arm)
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

W, H = 1000, 800
m.vis.global_.offwidth = max(m.vis.global_.offwidth, W)
m.vis.global_.offheight = max(m.vis.global_.offheight, H)
renderer = mujoco.Renderer(m, H, W)
cam = mujoco.MjvCamera()
cam.type = mujoco.mjtCamera.mjCAMERA_FREE
cam.lookat[:] = [0.22, 0, 0.42]
cam.distance, cam.azimuth, cam.elevation = 1.55, 200, -22
opt = mujoco.MjvOption()
BG = np.array([15, 17, 20], float)


def shade(img):
    return BG + img * (1 - BG / 255)


def pose_at(qL, qR):
    d.qpos[la], d.qpos[ra] = qL, qR
    mujoco.mj_forward(m, d)


def draw_path(points, rgb):
    for a, b in zip(points[:-1], points[1:]):
        if renderer.scene.ngeom >= renderer.scene.maxgeom:
            return
        g = renderer.scene.geoms[renderer.scene.ngeom]
        mujoco.mjv_initGeom(g, mujoco.mjtGeom.mjGEOM_CAPSULE, np.zeros(3), np.zeros(3), np.zeros(9),
                            np.array([*rgb, 1], np.float32))
        mujoco.mjv_connector(g, mujoco.mjtGeom.mjGEOM_CAPSULE, 0.004, a, b)
        renderer.scene.ngeom += 1


L, R = z["left"], z["right"]
n = len(L)
paths = {"left": [], "right": []}
for i in range(0, n, 10):
    pose_at(L[i], R[i])
    for s in paths:
        paths[s].append(d.site_xpos[site[s]].copy())

# Strobe: composite several moments, the last one solid.
moments = np.linspace(0, n - 1, 6).round().astype(int)
canvas = None
for j, i in enumerate(moments):
    pose_at(L[i], R[i])
    renderer.update_scene(d, cam, opt)
    if j == len(moments) - 1:
        for s, rgb in (("left", BLUE), ("right", ORANGE)):
            draw_path(paths[s], rgb)
    img = shade(renderer.render().astype(float))
    if canvas is None:
        canvas = img
    else:
        mask = (np.abs(img - BG).sum(axis=2, keepdims=True) > 6).astype(float)
        a = 0.35 + 0.65 * j / (len(moments) - 1)
        canvas = canvas * (1 - a * mask) + img * (a * mask)
Image.fromarray(canvas.clip(0, 255).astype(np.uint8)).save(f"{out}/traces.png")

# Sequential execution, left arm first: left runs its whole trajectory with the
# right arm at its start, then the right arm runs.
os.makedirs(f"{out}/sequential", exist_ok=True)
seq = [(L[i], R[0]) for i in range(n)] + [(L[-1], R[i]) for i in range(n)]
step = 8
hits = 0
for k, (qL, qR) in enumerate(seq[::step]):
    hit = bool(_cross_arm_contacts(robot, qL, qR))
    hits += hit
    pose_at(qL, qR)
    renderer.update_scene(d, cam, opt)
    img = shade(renderer.render().astype(float)).astype(np.uint8)
    if hit:
        b = 10
        img[:b], img[-b:], img[:, :b], img[:, -b:] = (230, 60, 60), (230, 60, 60), (230, 60, 60), (230, 60, 60)
    Image.fromarray(img).save(f"{out}/sequential/frame_{k:04d}.png")
print("strobe moments", moments.tolist(), "sequential frames", len(seq[::step]), "hit frames", hits)
