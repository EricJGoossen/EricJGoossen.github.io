"""Draws the V2, V3 and MuJoCo trajectories of the torque-driven arm
(dyn_compare.json) through MuJoCo's renderer, one panel each, side view
(looking along the joint axis), orthographic, with the forearm tip's last
second drawn as a trail. usage: render_three.py <bench dir> <out prefix>"""
import sys, json, math
sys.path.insert(0, sys.argv[1] + "/bench")
import numpy as np, mujoco, yaml
import arow_to_mjcf as a2m
out = sys.argv[2]
scene = a2m.load_scene("arm_torque.arow", "no_gravity.yaml")
doc = yaml.safe_load(open("arm_torque.arow"))
vis = {j["name"]: j["fields"] for j in doc["joints"]}
xml = a2m.to_mjcf(scene, 0.001, "Euler")
for j in scene.joints:
    f = vis[j.name]; e = f["visual_extents"]; c = f["visual_color"]
    geom = (f'<geom type="box" size="{e[0]} {e[1]} {e[2]}" pos="0 {e[1]} 0" '
            f'rgba="{c[0]} {c[1]} {c[2]} 1" contype="0" conaffinity="0" mass="0"/>')
    i = xml.index(f'<joint name="{j.name}"'); k = xml.index('/>', i) + 2
    xml = xml[:k] + "\n" + geom + xml[k:]
xml = xml.replace('<worldbody>', '''<visual><global orthographic="true" fovy="4.1" offwidth="640" offheight="640"/>
<headlight ambient="0.45 0.45 0.45" diffuse="0.55 0.55 0.55"/></visual>
<asset><material name="bg" specular="0" shininess="0" reflectance="0" rgba="0.1 0.108 0.125 1"/></asset>
<worldbody><geom type="box" pos="6 0 0" size="0.01 20 20" material="bg" contype="0" conaffinity="0"/>
<geom type="sphere" size="0.045" rgba="0.85 0.86 0.88 1" contype="0" conaffinity="0"/>''', 1)
m = mujoco.MjModel.from_xml_string(xml)
d = mujoco.MjData(m)
r = mujoco.Renderer(m, 640, 640)
cam = mujoco.MjvCamera(); cam.lookat[:] = [0, 0, 0]; cam.distance = 4; cam.azimuth = 0; cam.elevation = 0
opt = mujoco.MjvOption()
data = json.load(open("dyn_compare.json"))
tip_local = np.array([0, 2 * vis["elbow"]["visual_extents"][1], 0])
fore = m.nbody - 1
fps = 30
for name in ("v2", "v3", "mujoco"):
    s, e = np.array(data[name]["shoulder"]), np.array(data[name]["elbow"])
    trail = []
    with open(f"{out}_{name}.rgb", "wb") as fh:
        for k in range(4 * fps + 1):
            i = min(round(k * 1000 / fps), len(s) - 1)
            # tip positions over the last second, at 100 Hz
            pts = []
            for jj in range(max(0, i - 1000), i + 1, 10):
                d.qpos[:] = [s[jj], e[jj]]; mujoco.mj_kinematics(m, d)
                pts.append(d.xpos[fore] + d.xmat[fore].reshape(3, 3) @ tip_local)
            d.qpos[:] = [s[i], e[i]]; mujoco.mj_forward(m, d)
            r.update_scene(d, cam, opt)
            for n, p in enumerate(pts):
                if r.scene.ngeom >= r.scene.maxgeom: break
                a = (n + 1) / len(pts)
                mujoco.mjv_initGeom(r.scene.geoms[r.scene.ngeom], mujoco.mjtGeom.mjGEOM_SPHERE,
                                    np.array([0.018, 0, 0]), p - np.array([0.2, 0, 0]), np.eye(3).flatten(),
                                    np.array([0.95, 0.75, 0.3, 0.15 + 0.85 * a], dtype=np.float32))
                r.scene.ngeom += 1
            fh.write(r.render().tobytes())
    print(name, "done")
