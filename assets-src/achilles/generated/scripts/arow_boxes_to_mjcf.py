"""Free-box .arow scenes (Y-up, gravity -y) -> Z-up MJCF with the same boxes, masses, contacts and start state.
Achilles (x, y, z) maps to MuJoCo (x, -z, y), a +90 deg rotation about x."""
import math, sys, yaml
import numpy as np

QR = np.array([math.cos(math.pi / 4), math.sin(math.pi / 4), 0, 0])
def qmul(a, b):
    w1, x1, y1, z1 = a; w2, x2, y2, z2 = b
    return np.array([w1*w2 - x1*x2 - y1*y2 - z1*z2, w1*x2 + x1*w2 + y1*z2 - z1*y2,
                     w1*y2 - x1*z2 + y1*w2 + z1*x2, w1*z2 + x1*y2 - y1*x2 + z1*w2])
R = lambda p: np.array([p[0], -p[2], p[1]])
v = lambda a: " ".join(f"{x:.9g}" for x in a)

def to_mjcf(arow, dt=0.002, integrator="Euler", visual=False):
    doc = yaml.safe_load(open(arow))
    bodies, q0, qd0 = [], [], []
    ground = ""
    for j in doc["joints"]:
        f = j["fields"]
        if j["name"] == "ground":
            c = np.array(f["fixed_joint_transform"]["translation"]) + np.array(f["collision_pose"]["translation"])
            e = f["collision_extents"]
            ground = (f'<geom name="ground" type="box" pos="{v(R(c))}" quat="{v(QR)}" size="{v(e)}" '
                      f'margin="{f["collision_margin"][0]}" rgba="0.35 0.38 0.35 1"/>')
            continue
        if f["joint_activation_mask"] != [63]:
            continue
        e = np.array(f["collision_extents"]) + f["collision_radius"][0]
        m = f["rigid_body_inertia"][0]
        pos = R(f["joint_position"]["translation"]); quat = qmul(QR, np.array(f["joint_position"]["rotation"]))
        col = f.get("visual_color", [0.6, 0.6, 0.6])
        bodies.append(f'''<body name="{j["name"]}" pos="{v(pos)}" quat="{v(quat)}">
  <freejoint/>
  <geom type="box" pos="{v(f["collision_pose"]["translation"])}" size="{v(e)}" mass="{m}" margin="{f["collision_margin"][0]}" rgba="{v(col)} 1"/>
</body>''')
        q0 += [*pos, *quat]
        jv = f["joint_velocity"]  # (rx, ry, rz, x, y, z), body frame
        lin_world = R(np.zeros(3)) if not any(jv[3:]) else None
        assert lin_world is not None, "only pure angular starting velocities are handled"
        qd0 += [0, 0, 0, *jv[:3]]
    vis = '<visual><global fovy="60" offwidth="1280" offheight="800"/><headlight ambient="0.35 0.35 0.35" diffuse="0.6 0.6 0.6"/></visual>' if visual else ""
    xml = f"""<mujoco>
<option timestep="{float(np.float32(dt))!r}" gravity="0 0 -9.81" integrator="{integrator}" cone="pyramidal"/>
{vis}
<worldbody>
{ground}
{chr(10).join(bodies)}
</worldbody>
</mujoco>"""
    return xml, np.array(q0), np.array(qd0)

if __name__ == "__main__":
    print(to_mjcf(sys.argv[1])[0])
