"""An illustration, not the robot's controller: the two OpenArms in MuJoCo physics
hold the same reach-out pose with the same joint stiffness and damping (the shape
of the motors' MIT-mode loop: tau = kp*(q* - q) - kd*qd + tau_ff). The left arm
gets no feedforward; the right arm adds gravity compensation as tau_ff, the way
the forwarding controller does. Halfway through, both are pushed down at the wrist.

  sim_gravcomp.py <out.npz>
Records both arms' joints and the wrist heights at 30 fps.
"""
import sys

import mujoco
import numpy as np
from openarm.config import OpenarmConfig

out = sys.argv[1]
m = mujoco.MjModel.from_xml_path(str(OpenarmConfig.default().model_path))
m.body_gravcomp[:] = 0           # the model compensates gravity for free; turn that off
m.actuator_gainprm[:] = 0        # and drive the joints with torques instead of its servos
m.actuator_biasprm[:] = 0
m.opt.timestep = 0.002           # 500 Hz
d = mujoco.MjData(m)
J = {s: [m.joint(f"openarm_{s}_joint{i}").qposadr[0] for i in range(1, 8)] for s in ("left", "right")}
V = {s: [m.joint(f"openarm_{s}_joint{i}").dofadr[0] for i in range(1, 8)] for s in ("left", "right")}
hand = {s: m.body(f"openarm_{s}_hand").id for s in ("left", "right")}
# Reach forward: shoulder pitched forward, elbow bent (joint 1 turns the other way on the right arm).
q_star = {"left": np.array([-0.9, 0.0, 0.0, 0.9, 0.0, 0.0, 0.0]), "right": np.array([0.9, 0.0, 0.0, 0.9, 0.0, 0.0, 0.0])}
for s in J:
    d.qpos[J[s]] = q_star[s]
mujoco.mj_forward(m, d)
kp = np.array([30, 30, 20, 20, 5, 5, 5.0])
kd = np.array([2, 2, 1.5, 1.5, 0.3, 0.3, 0.3])
T, push = 6.0, (3.0, 3.6)
rec = {"left": [], "right": [], "zl": [], "zr": [], "t": []}
steps = int(T / m.opt.timestep)
for k in range(steps):
    t = k * m.opt.timestep
    # gravity torques at the current state: inverse dynamics with zero velocity and acceleration
    g = d.qfrc_bias.copy()  # gravity plus Coriolis; the arm barely moves, so this is gravity
    d.qfrc_applied[:] = 0
    for s in J:
        q, qd = d.qpos[J[s]], d.qvel[V[s]]
        tau = kp * (q_star[s] - q) - kd * qd
        if s == "right":
            tau = tau + g[V[s]]
        d.qfrc_applied[V[s]] = tau
    d.xfrc_applied[:] = 0
    if push[0] <= t < push[1]:
        for s in J:
            d.xfrc_applied[hand[s], 2] = -15.0
    mujoco.mj_step(m, d)
    if k % int(round(1 / 30 / m.opt.timestep)) == 0:
        rec["left"].append(d.qpos[J["left"]].copy())
        rec["right"].append(d.qpos[J["right"]].copy())
        rec["zl"].append(d.xpos[hand["left"]][2])
        rec["zr"].append(d.xpos[hand["right"]][2])
        rec["t"].append(t)
np.savez(out, **{k: np.array(v) for k, v in rec.items()}, push=np.array(push), q_star_l=q_star["left"], q_star_r=q_star["right"])
z = np.load(out)
print("wrist height start", z["zl"][0].round(3), z["zr"][0].round(3), "settled", z["zl"][80].round(3), z["zr"][80].round(3),
      "pushed", z["zl"][105].round(3), z["zr"][105].round(3), "end", z["zl"][-1].round(3), z["zr"][-1].round(3))
