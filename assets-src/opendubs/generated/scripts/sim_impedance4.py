"""Eric's four arm control laws, compiled unmodified from his repos (see
build_armlaws.sh), each driving the left OpenArm in MuJoCo physics through the
same routine: a fast reach out to an almost straight arm, a push down on the
elbow there, a fast reach back, then a sideways push on the elbow.

  pure      openarm_cartesian_control @3bf55b0  tau = J^T (K dx + D dxdot) + g
  mixed     openarm_impedance_control @871d1e3  tau = (J^T K J + eps I)(q* - q) + J^T D J (qd* - qd) + g
  null      openarm_impedance_control @eb8e13a  the Cartesian term plus a joint posture term
                                                projected into the null space, + g
  passthru  openarm_impedance_control @b517999  gravity torque sent as the feedforward of the
                                                motors' own PD loop (kp, kd from control_gains.yaml)

Timing: physics runs at 2 kHz. The first three laws run on the Thor at 500 Hz and
act on the arm's state from the previous cycle (a read, compute, write loop over
CAN), their torque held until the next update. The motors close their own PD loop
every physics step on the current state; the Thor only sends them the trajectory and
the gravity feedforward at 500 Hz. The one-cycle delay is an assumption of this
demo, not a measurement.

The laws are Eric's; the demo gains below are mine (the same Cartesian gains for
the first three), and every law gets the trajectory's velocity as its reference.

  sim_impedance4.py <libarmlaws.so> <bimanual.urdf> <out.npz>
Records every arm's joints, and the reference, at 30 fps.
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
names = (C.c_char_p * n)(*[f"openarm_left_joint{i}".encode() for i in range(1, 8)])
ee = b"openarm_left_hand_tcp"
for f in ("v1_new", "v2_new", "v3_new", "v4_new"):
    getattr(lib, f).restype = C.c_void_p


def arr(x):
    return (C.c_double * len(x))(*x)


def np_out(k=n):
    return (C.c_double * k)()


TAU_MAX = np.array([45, 45, 25, 20, 15, 15, 15.0])
tau_lim = arr(TAU_MAX)
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
m.opt.timestep = 0.0005          # physics and the motors' own loop at 2 kHz
EVERY = 4                        # the Thor's loop at 500 Hz
J = [m.joint(f"openarm_left_joint{i}").qposadr[0] for i in range(1, 8)]
V = [m.joint(f"openarm_left_joint{i}").dofadr[0] for i in range(1, 8)]
VR = [m.joint(f"openarm_right_joint{i}").dofadr[0] for i in range(1, 8)]
QR = [m.joint(f"openarm_right_joint{i}").qposadr[0] for i in range(1, 8)]
hand, elbow = m.body("openarm_left_hand").id, m.body("openarm_left_link4").id

A = np.array([-0.2, 0.15, 0.0, 2.2, 0.0, 0.3, 0.0])     # elbow bent, hand drawn in
S = np.array([-1.4, 0.15, 0.0, 0.05, 0.0, 0.3, 0.0])    # reaching out 30 cm, elbow almost straight
REACH = 0.5                                              # seconds for each reach
moves = [(0.5, A, S), (4.6, S, A)]
T = 9.5


def ref(t):
    """Planned joint position and velocity: quintic reaches between the poses."""
    q, qd = A.copy(), np.zeros(n)
    for t0, a, b in moves:
        u = np.clip((t - t0) / REACH, 0, 1)
        if t >= t0:
            q = a + (b - a) * (10 * u**3 - 15 * u**4 + 6 * u**5)
            qd = (b - a) * (30 * u**2 - 60 * u**3 + 30 * u**4) / REACH if u < 1 else np.zeros(n)
    return q, qd


# Sanity: Eric's gravity model against MuJoCo's at both poses.
d = mujoco.MjData(m)
for q in (A, S):
    d.qpos[J] = q
    mujoco.mj_forward(m, d)
    g = np_out()
    lib.v4_gravity(v4, arr(q), n, g)
    print("gravity, pinocchio vs mujoco:", np.round(list(g), 2), np.round(d.qfrc_bias[V], 2))

# Pushes: at the reach, the elbow straight down (near the singularity, where a hand
# error along the arm turns into almost no elbow torque); back at the start, the elbow
# across the shoulder-wrist line (the arm's swivel, which the hand does not feel).
d.qpos[J] = A
mujoco.mj_forward(m, d)
sh, el, wr = (d.xpos[m.body(f"openarm_left_link{i}").id].copy() for i in (2, 4, 7))
axis = (wr - sh) / np.linalg.norm(wr - sh)
swivel = np.cross(axis, el - sh)
swivel /= np.linalg.norm(swivel)
pushes = [(1.9, 2.5, elbow, np.array([0, 0, -35.0])), (6.3, 6.9, elbow, 20.0 * swivel)]


def pose(q):
    p, qu = np_out(3), np_out(4)
    lib.v1_fk(v1, arr(q), n, p, qu)
    return np.array(list(p)), np.array(list(qu))


def twist(q, qd, h=1e-4):
    """Reference twist of the hand (world-aligned, as the Cartesian law measures it)."""
    p0, q0 = pose(q)
    p1, q1 = pose(q + qd * h)
    dq = np.zeros(4)
    mujoco.mju_mulQuat(dq, q1, np.array([q0[0], -q0[1], -q0[2], -q0[3]]))
    w = np.zeros(3)
    mujoco.mju_quat2Vel(w, dq, h)
    return (p1 - p0) / h, w


def law(name, q, qd, qr, qdr):
    t = np_out()
    if name == "pure":
        p, qu = pose(qr)
        lin, ang = twist(qr, qdr)
        lib.v1_control(v1, arr(q), arr(qd), n, arr(p), arr(qu), arr(lin), arr(ang), t)
    elif name == "mixed":
        lib.v2_control(v2, arr(q), arr(qd), arr(qr), arr(qdr), n, t)
    elif name == "null":
        lib.v3_control(v3, arr(q), arr(qd), arr(qr), arr(qdr), n, t)
    else:
        lib.v4_gravity(v4, arr(q), n, t)
    return np.array(list(t))


rec, refs = {}, []
for name in ("pure", "mixed", "null", "passthru"):
    d = mujoco.MjData(m)
    d.qpos[J] = A
    mujoco.mj_forward(m, d)
    qs, ts, refs = [], [], []
    held = np.zeros(n)                   # what the Thor last sent
    seen = (A.copy(), np.zeros(n))       # the state it will act on next cycle
    qr, qdr = A.copy(), np.zeros(n)
    for k in range(int(T / m.opt.timestep)):
        t = k * m.opt.timestep
        q, qd = d.qpos[J].copy(), d.qvel[V].copy()
        if k % EVERY == 0:
            qr, qdr = ref(t)
            if name == "passthru":
                held = law(name, q, qd, qr, qdr)            # gravity feedforward
            else:
                held = law(name, *seen, qr, qdr)            # last cycle's reading
            seen = (q, qd)
        tau = held + (kp * (qr - q) + kd * (qdr - qd) if name == "passthru" else 0)
        tau = np.clip(tau, -TAU_MAX, TAU_MAX)                # every law within the same torque limits
        d.qfrc_applied[:] = 0
        d.qfrc_applied[V] = tau
        d.qfrc_applied[VR] = d.qfrc_bias[VR] - 50 * d.qpos[QR] - 5 * d.qvel[VR]  # park the right arm
        d.xfrc_applied[:] = 0
        for t0, t1, body, f in pushes:
            if t0 <= t < t1:
                d.xfrc_applied[body, :3] = f
        mujoco.mj_step(m, d)
        if k % int(round(1 / 30 / m.opt.timestep)) == 0:
            qs.append(d.qpos.copy())
            ts.append(t)
            r = d.qpos.copy()
            r[J] = ref(t)[0]
            refs.append(r)
    rec[name] = np.array(qs)
np.savez(out, t=np.array(ts), ref=np.array(refs), pushes=np.array([[p[0], p[1], p[2]] for p in pushes]),
         force=np.array([p[3] for p in pushes]), **rec)

# What the video shows, measured.
dd = mujoco.MjData(m)


def where(q):
    dd.qpos[:] = q
    mujoco.mj_kinematics(m, dd)
    return dd.xpos[hand].copy(), dd.xpos[elbow].copy()


t = np.array(ts)
R = np.array(refs)
for name in rec:
    Q = rec[name]
    err = np.array([np.linalg.norm(where(Q[i])[0] - where(R[i])[0]) for i in range(len(t))])
    elb = np.array([np.linalg.norm(where(Q[i])[1] - where(R[i])[1]) for i in range(len(t))])
    w = (t > 0.5) & (t < 1.9)
    bad = t[w][err[w] > 0.01]
    arrive = bad.max() + 1 / 30 if len(bad) else 0.5
    after = (t > 1.85) & (t < 1.9)
    end_s = (t > 4.4) & (t < 4.6)
    end = t > 9.3
    print(f"{name:9s} reach: lag {err[(t > 0.5) & (t < 1.9)].max() * 100:4.1f} cm, within 1 cm by {arrive - 0.5:.2f} s"
          f" | at the reach {err[after].mean() * 100:.1f} cm | after the push down: hand {err[end_s].mean() * 100:.1f} cm,"
          f" elbow {elb[end_s].mean() * 100:.1f} cm, q4 {Q[end_s][:, J[3]].mean():.2f}"
          f" | end: hand {err[end].mean() * 100:.1f} cm, elbow {elb[end].mean() * 100:.1f} cm")
