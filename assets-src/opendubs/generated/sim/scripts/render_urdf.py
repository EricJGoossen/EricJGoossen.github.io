"""Render Eric's robot description (eric/open_dubs_description.urdf, expanded with
xacro) in MuJoCo with every link's frame drawn: the base, the frame, four wheels
and the front and back lidars. usage: render_urdf.py <expanded.urdf> <out.png>"""
import os
import sys

os.environ.setdefault("MUJOCO_GL", "egl")
import mujoco  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

src, out = sys.argv[1], sys.argv[2]
spec = mujoco.MjSpec.from_file(src)
spec.worldbody.add_light(pos=[1, -1, 2], dir=[-0.4, 0.4, -1], diffuse=[0.7, 0.7, 0.7])
m = spec.compile()
d = mujoco.MjData(m)
mujoco.mj_forward(m, d)
COL = {"frame": (0.70, 0.72, 0.76, 0.18), "base_link": (0.70, 0.72, 0.76, 0.18), "drivewhl": (0.2, 0.21, 0.23, 1), "front_lidar": (0.95, 0.55, 0.22, 1),
       "back_lidar": (0.24, 0.55, 0.99, 1)}
for g in range(m.ngeom):
    body = m.body(m.geom_bodyid[g]).name
    for key, rgba in COL.items():
        if body.startswith(key):
            m.geom_matid[g] = -1
            m.geom_rgba[g] = rgba
m.vis.global_.offwidth, m.vis.global_.offheight = 1200, 800
m.vis.quality.offsamples = 8
m.vis.scale.framelength, m.vis.scale.framewidth = 2.6, 0.12
r = mujoco.Renderer(m, 800, 1200)
cam = mujoco.MjvCamera()
cam.type = mujoco.mjtCamera.mjCAMERA_FREE
cam.lookat[:] = [0, 0, 0.05]
cam.distance, cam.azimuth, cam.elevation = 1.05, 140, -34
opt = mujoco.MjvOption()
opt.frame = mujoco.mjtFrame.mjFRAME_BODY
r.update_scene(d, cam, opt)
img = r.render().astype(float)
bg = np.array([246, 245, 243.0])
img = np.where((img.sum(axis=2) == 0)[..., None], bg, img)
Image.fromarray(img.astype(np.uint8)).save(out)
print([m.body(i).name for i in range(m.nbody)])
