"""Render a free-box .arow scene in MuJoCo with the Achilles viewer's default camera (Y-up yaw 0.7, pitch 0.5, distance 4.5, fov 60).
usage: mj_render_boxes.py scene.arow out.rgb seconds fps"""
import sys, math
sys.path.insert(0, sys.argv[0].rsplit("/", 1)[0])
import numpy as np, mujoco
from arow_boxes_to_mjcf import to_mjcf
arow, out, seconds, fps = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
xml, q0, qd0 = to_mjcf(arow, visual=True)
m = mujoco.MjModel.from_xml_string(xml); d = mujoco.MjData(m)
d.qpos[:], d.qvel[:] = q0, qd0
mujoco.mj_forward(m, d)
r = mujoco.Renderer(m, 800, 1280)
cam = mujoco.MjvCamera(); cam.lookat[:] = 0; cam.distance = 4.5
yaw, pitch = 0.7, 0.5
cam.azimuth = 180 - math.degrees(yaw); cam.elevation = -math.degrees(pitch)
spf = round(1 / (fps * m.opt.timestep))
with open(out, "wb") as fh:
    for k in range(int(seconds * fps) + 1):
        r.update_scene(d, cam); fh.write(r.render().tobytes())
        mujoco.mj_step(m, d, nstep=spf)
