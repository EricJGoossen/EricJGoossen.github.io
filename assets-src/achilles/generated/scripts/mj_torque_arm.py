# MuJoCo 3.15 on the same scene: converted with the bench's arow_to_mjcf, the
# shoulder torque applied as a generalized force every step, Euler at 1 ms.
import sys, json, numpy as np, mujoco
sys.path.insert(0, sys.argv[1] + "/bench")
import arow_to_mjcf as a2m
scene = a2m.load_scene("arm_torque.arow", "no_gravity.yaml")
m = mujoco.MjModel.from_xml_string(a2m.to_mjcf(scene, 0.001, "Euler"))
d = mujoco.MjData(m)
q0, qd0 = a2m.initial_state(scene); d.qpos[:] = q0; d.qvel[:] = qd0
rows = []
for k in range(4001):
    rows.append((k * 0.001, *d.qpos))
    d.qfrc_applied[:] = [0.1, 0.0]
    mujoco.mj_step(m, d)
np.savetxt("mj.csv", np.array(rows), delimiter=",", header="t,q_shoulder,q_elbow", comments="")
print(mujoco.__version__, m.opt.timestep, m.opt.gravity)
