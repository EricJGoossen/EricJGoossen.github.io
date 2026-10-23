"""Eric's four arm control laws, compiled unmodified from his repos (see
build_armlaws.sh), each holding the left OpenArm in MuJoCo physics while it is
pushed the same way: at the hand, then at the elbow.

  pure      openarm_cartesian_control @3bf55b0  tau = J^T (K dx + D dxdot) + g
  mixed     openarm_impedance_control @871d1e3  tau = (J^T K J + eps I)(q* - q) + J^T D J (qd* - qd) + g
  null      openarm_impedance_control @eb8e13a  the Cartesian term plus a joint posture term
                                                projected into the null space, + g
  passthru  openarm_impedance_control @b517999  gravity torque sent as the feedforward of the
                                                motors' own PD loop (kp, kd from control_gains.yaml)

The laws are Eric's; the demo gains below are mine, picked so the four are
comparable (the same Cartesian gains for the first three).

  sim_impedance4.py <libarmlaws.so> <bimanual.urdf> <out.npz>
Records every arm's joints at 30 fps.
"""
import ctypes as C
import sys

import mujoco
import numpy as np
from openarm.config import OpenarmConfig

lib = C.CDLL(sys.argv[1])
urdf = open(sys.argv[2]).read().encode()
out = sys.argv[3]

n = 7
D = C.POINTER(C.c_double)
names = (C.c_char_p * n)(*[f"openarm_left_joint{i}".encode() for i in range(1, 8)])
ee = b"openarm_left_hand_tcp"
for f in ("v1_new", "v2_new", "v3_new", "v4_new"):
    getattr(lib, f).restype = C.c_void_p


def arr(x):
    return (C.c_double * len(x))(*x)


def np_out(k=n):
    return (C.c_double * k)()


tau_lim = arr([45, 45, 25, 20, 15, 15, 15])
wrench = arr([40, 40, 40, 10, 10, 10])
K_cart = [200, 200, 200, 4, 4, 4]
D_cart = [20, 20, 20, 0.2, 0.2, 0.2]
K_null = [10, 10, 10, 10, 2, 2, 2]
D_null = [1, 1, 1, 1, 0.1, 0.1, 0.1]
kp = np.array([70, 70, 70, 60, 10, 10, 10.0])        # control_gains.yaml
kd = np.array([2.75, 2.5, 2.0, 2.0, 0.7, 0.6, 0.5])

v1 = C.c_void_p(lib.v1_new(urdf, names, n, ee, arr([-0.8, -0.8, 0]), arr([0.8, 0.8, 1.2]), wrench, tau_lim, 1, 1, 1))
lib.v1_gains(v1, arr(K_cart), arr(D_cart))
v2 = C.c_void_p(lib.v2_new(urdf, names, n, ee, tau_lim, 1, 1, 1))
lib.v2_gains(v2, arr(K_cart), arr(D_cart))
v3 = C.c_void_p(lib.v3_new(urdf, names, n, ee, tau_lim, wrench, 1))
lib.v3_gains(v3, arr(K_cart), arr(D_cart), arr(K_null), arr(D_null), n)
v4 = C.c_void_p(lib.v4_new(urdf, names, n, ee))

m = mujoco.MjModel.from_xml_path(str(OpenarmConfig.default().model_path))
m.body_gravcomp[:] = 0           # the model compensates gravity for free; turn that off
m.actuator_gainprm[:] = 0        # and drive the joints with torques instead of its servos
m.actuator_biasprm[:] = 0
m.opt.timestep = 0.002           # 500 Hz
J = [m.joint(f"openarm_left_joint{i}").qposadr[0] for i in range(1, 8)]
V = [m.joint(f"openarm_left_joint{i}").dofadr[0] for i in range(1, 8)]
VR = [m.joint(f"openarm_right_joint{i}").dofadr[0] for i in range(1, 8)]
QR = [m.joint(f"openarm_right_joint{i}").qposadr[0] for i in range(1, 8)]
hand, elbow = m.body("openarm_left_hand").id, m.body("openarm_left_link4").id
q_star = np.array([-0.6, 0.15, 0.0, 1.2, 0.0, 0.0, 0.0])   # reach forward, elbow bent

# Sanity: Eric's gravity model against MuJoCo's at the hold pose.
d = mujoco.MjData(m)
d.qpos[J] = q_star
mujoco.mj_forward(m, d)
g = np_out()
lib.v4_gravity(v4, arr(q_star), n, g)
print("gravity, pinocchio vs mujoco:", np.round(list(g), 2), np.round(d.qfrc_bias[V], 2))

# The hand pushed sideways, then the elbow pushed across the shoulder-wrist line: the
# arm's "swivel", a motion the hand does not feel, so only joint-space terms resist it.
sh, el, wr = (d.xpos[m.body(f"openarm_left_link{i}").id].copy() for i in (2, 4, 7))
axis = (wr - sh) / np.linalg.norm(wr - sh)
swivel = np.cross(axis, el - sh)
swivel /= np.linalg.norm(swivel)
T = 9.0
pushes = [(1.0, 1.6, hand, np.array([0, 20.0, 0])), (4.0, 4.6, elbow, 20.0 * swivel)]
pos, quat = np_out(3), np_out(4)
lib.v1_fk(v1, arr(q_star), n, pos, quat)


def law(name, q, qd):
    t = np_out()
    if name == "pure":
        lib.v1_control(v1, arr(q), arr(qd), n, pos, quat, t)
    elif name == "mixed":
        lib.v2_control(v2, arr(q), arr(qd), arr(q_star), n, t)
    elif name == "null":
        lib.v3_control(v3, arr(q), arr(qd), arr(q_star), n, t)
    else:
        lib.v4_gravity(v4, arr(q), n, t)
        return kp * (q_star - q) - kd * qd + np.array(list(t))
    return np.array(list(t))


rec = {}
for name in ("pure", "mixed", "null", "passthru"):
    d = mujoco.MjData(m)
    d.qpos[J] = q_star
    mujoco.mj_forward(m, d)
    qs, ts = [], []
    for k in range(int(T / m.opt.timestep)):
        t = k * m.opt.timestep
        d.qfrc_applied[:] = 0
        d.qfrc_applied[V] = law(name, d.qpos[J].copy(), d.qvel[V].copy())
        d.qfrc_applied[VR] = d.qfrc_bias[VR] - 50 * d.qpos[QR] - 5 * d.qvel[VR]  # park the right arm
        d.xfrc_applied[:] = 0
        for t0, t1, body, f in pushes:
            if t0 <= t < t1:
                d.xfrc_applied[body, :3] = f
        mujoco.mj_step(m, d)
        if k % int(round(1 / 30 / m.opt.timestep)) == 0:
            qs.append(d.qpos.copy())
            ts.append(t)
    rec[name] = np.array(qs)
    print(name, "final joint error", np.round(rec[name][-1][J] - q_star, 3))
np.savez(out, t=np.array(ts), pushes=np.array([[p[0], p[1], p[2]] for p in pushes]),
         force=np.array([p[3] for p in pushes]), **rec)
