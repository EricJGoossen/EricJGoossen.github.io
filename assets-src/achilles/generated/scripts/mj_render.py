"""Render an .arow scene in MuJoCo with the same camera as the Achilles viewer.
usage: mj_render.py scene.arow config.yaml out.rgb seconds fps "yaw pitch dist tx ty tz" [integrator] [dt]
Writes raw RGB 1280x800 frames, top-down rows. Frame k shows the state after k/fps s."""
import math, sys
sys.path.insert(0, sys.argv[0].rsplit('/', 2)[0] + '/bench')
import numpy as np, mujoco, yaml
import arow_to_mjcf as a2m

arow, cfg, out, seconds, fps, cam = sys.argv[1:7]
integ = sys.argv[7] if len(sys.argv) > 7 else "RK4"
dt = float(sys.argv[8]) if len(sys.argv) > 8 else 0.002
seconds, fps = float(seconds), float(fps)
yaw, pitch, dist, tx, ty, tz = map(float, cam.split())
scene = a2m.load_scene(arow, cfg)
doc = yaml.safe_load(open(arow))
vis = {j["name"]: j["fields"] for j in doc["joints"]}
xml = a2m.to_mjcf(scene, dt, integ)
for j in scene.joints:
    f = vis[j.name]
    e = np.array(f.get("visual_extents", [0, 0, 0]), float)
    c = f.get("visual_color", [0.7, 0.7, 0.7])
    if not e.any():
        continue
    geom = (f'<geom type="box" size="{e[0]} {e[1]} {e[2]}" pos="0 {e[1]} 0" '
            f'rgba="{c[0]} {c[1]} {c[2]} 1" contype="0" conaffinity="0" mass="0"/>')
    tag = f'<joint name="{j.name}"'
    i = xml.index(tag); k = xml.index('/>', i) + 2
    xml = xml[:k] + "\n" + geom + xml[k:]
xml = xml.replace('<worldbody>', '''<visual><global fovy="60" offwidth="1280" offheight="800"/>
<headlight ambient="0.35 0.35 0.35" diffuse="0.6 0.6 0.6"/></visual>
<asset><texture name="grid" type="2d" builtin="checker" width="512" height="512" rgb1="0.16 0.17 0.2" rgb2="0.12 0.13 0.15"/>
<material name="grid" texture="grid" texrepeat="20 20"/></asset>
<worldbody><geom type="capsule" fromto="0 0 0 0 0 2.2" size="0.006" rgba="0.8 0.8 0.8 1" contype="0" conaffinity="0"/><geom type="plane" size="10 10 0.1" material="grid" contype="0" conaffinity="0"/>''', 1)
m = mujoco.MjModel.from_xml_string(xml)
m.vis.rgba.haze[:] = [0.08, 0.09, 0.11, 1]
d = mujoco.MjData(m)
q0, qd0 = a2m.initial_state(scene)
d.qpos[:] = q0; d.qvel[:] = qd0
mujoco.mj_forward(m, d)
r = mujoco.Renderer(m, 800, 1280)
c = mujoco.MjvCamera()
c.lookat[:] = [tx, ty, tz]; c.distance = dist
c.azimuth = math.degrees(yaw) + 180; c.elevation = -math.degrees(pitch)
opt = mujoco.MjvOption()
steps = round(1 / (fps * dt))
with open(out, "wb") as fh:
    for k in range(int(seconds * fps)):
        r.update_scene(d, c, opt)
        fh.write(r.render().tobytes())
        mujoco.mj_step(m, d, nstep=steps)
