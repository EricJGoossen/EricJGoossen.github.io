"""Render capture_reset.py's npz on MuJoCo Menagerie's SO-101 (robotstudio_so101), whose joint
chain matches fleet_so101's own kinematics exactly (same joints and signs; the base frames differ
by a fixed offset, BASE below). The peg is a 30 x 30 x 60 mm box: it lies where it was scrambled,
follows the gripper while the jaws are closed on it, and stays where it was let go.

  render_reset.py <reset.npz> <menagerie robotstudio_so101 dir> <out dir> [speed]
"""
import os
import sys

os.environ.setdefault("MUJOCO_GL", "egl")
import mujoco  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

src, model_dir, out = sys.argv[1], sys.argv[2], sys.argv[3]
speed = float(sys.argv[4]) if len(sys.argv) > 4 else 2.0
z = np.load(src)
BASE = np.array([0.016, -0.021, -0.032])  # fleet_so101 contract base frame -> MJCF world (fitted, exact)
TABLE = BASE[2]                             # the table top is z = 0 in the contract frame

scene = f"""<mujoco model="reset">
  <include file="so101.xml"/>
  <visual><headlight diffuse="0.55 0.55 0.55" ambient="0.35 0.35 0.35" specular="0.1 0.1 0.1"/>
    <quality offsamples="8"/><global offwidth="1280" offheight="960"/></visual>
  <worldbody>
    <light pos="0.3 -0.4 1.2" dir="-0.3 0.4 -1" diffuse="0.5 0.5 0.5"/>
    <geom name="table" type="box" size="0.32 0.26 0.01" pos="0.16 0 {TABLE - 0.01}" rgba="0.17 0.18 0.2 1" contype="0" conaffinity="0"/>
    <geom name="spot" type="box" size="0.022 0.022 0.0005" pos="0 0 {TABLE + 0.0006}" rgba="0.95 0.95 0.95 0.35" contype="0" conaffinity="0"/>
    <body name="peg" mocap="true" pos="0 0 -1">
      <geom type="box" size="0.015 0.015 0.03" pos="0 0 0.03" rgba="0.91 0.44 0.23 1" contype="0" conaffinity="0"/>
      <geom type="box" size="0.0152 0.009 0.009" pos="0 0 0.045" rgba="0.08 0.08 0.08 1" contype="0" conaffinity="0"/>
      <geom type="box" size="0.009 0.0152 0.009" pos="0 0 0.015" rgba="0.08 0.08 0.08 1" contype="0" conaffinity="0"/>
    </body>
  </worldbody>
</mujoco>"""
path = os.path.join(model_dir, "reset_render_tmp.xml")
open(path, "w").write(scene)
try:
    m = mujoco.MjModel.from_xml_path(path)
finally:
    os.unlink(path)
d = mujoco.MjData(m)
names = [str(n) for n in z["names"]]
qadr = [m.joint(n).qposadr[0] for n in names]
peg = m.body("peg").mocapid[0]
site = m.site("gripperframe").id
spot = m.geom("spot").id
put_back = z["put_back"]
m.geom_pos[spot][:2] = put_back[:3, 3][:2] + BASE[:2]

t, q = z["t"] - z["t"][0], z["q"]
starts = list(z["start_index"]) + [len(t)]


def pose_at(k_float):
    i = int(np.clip(np.floor(k_float), 0, len(t) - 2))
    a = k_float - i
    return (1 - a) * q[i] + a * q[i + 1]


def world(T):
    W = T.copy()
    W[:3, 3] = T[:3, 3] + BASE
    return W


def set_peg(T):
    d.mocap_pos[peg] = T[:3, 3]
    mujoco.mju_mat2Quat(d.mocap_quat[peg], T[:3, :3].flatten())


r = mujoco.Renderer(m, 720, 960)
cam = mujoco.MjvCamera()
cam.type = mujoco.mjtCamera.mjCAMERA_FREE
cam.lookat[:] = [0.15, 0.0, TABLE + 0.13]
cam.distance, cam.azimuth, cam.elevation = 0.95, -140, -20
opt = mujoco.MjvOption()
opt.sitegroup[:] = 0
font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Medium.otf", 24)
os.makedirs(out, exist_ok=True)

fps = 30
frame = 0
for n_reset in range(len(starts) - 1):
    a_i, b_i = starts[n_reset], starts[n_reset + 1]
    peg_T = world(z["before"][n_reset])
    held = None
    t0, t1 = t[max(a_i - 1, 0)], t[b_i - 1]
    for tk in np.arange(t0, t1 + 1e-9, speed / fps):
        k = np.interp(tk, t, np.arange(len(t)))
        qk = pose_at(k)
        d.qpos[qadr] = np.radians(qk)
        mujoco.mj_kinematics(m, d)
        G = np.eye(4)
        G[:3, :3], G[:3, 3] = d.site_xmat[site].reshape(3, 3), d.site_xpos[site]
        closing = qk[5] < 30
        near = np.linalg.norm(G[:3, 3] - (peg_T[:3, 3] + peg_T[:3, :3] @ [0, 0, 0.03])) < 0.04
        if held is None and closing and near:
            held = np.linalg.inv(G) @ peg_T
        elif held is not None and not closing:
            held = None
        if held is not None:
            peg_T = G @ held
        set_peg(peg_T)
        mujoco.mj_kinematics(m, d)
        r.update_scene(d, cam, opt)
        img = Image.fromarray(r.render())
        dr = ImageDraw.Draw(img)
        dr.text((24, 20), f"reset {n_reset + 1} of {len(starts) - 1}", font=font, fill=(230, 232, 235))
        img.save(f"{out}/frame_{frame:04d}.png")
        frame += 1
    # where the peg was let go, against the start pose it was sent to
    miss = np.linalg.norm(peg_T[:2, 3] - (put_back[:2, 3] + BASE[:2]))
    print(f"reset {n_reset + 1}: peg let go {miss * 1000:.1f} mm from its start pose (horizontally)")
print(frame, "frames")
