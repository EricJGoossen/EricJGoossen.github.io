"""Double pendulum (examples/two_joint_arm.arow): Achilles integrators vs MuJoCo vs the closed form.
Writes exp/dp_results.json with downsampled series."""
import json, math, sys
sys.path.insert(0, sys.argv[1] + '/bench')
import numpy as np, mujoco
from scipy.integrate import solve_ivp
import arow_to_mjcf as a2m

SP, A = sys.argv[1], sys.argv[2]
arow, cfg = f"{A}/examples/two_joint_arm.arow", f"{A}/examples/sim_config.yaml"
scene = a2m.load_scene(arow, cfg)
gz = scene.gravity[2]
assert abs(gz + 9.8) < 1e-6, scene.gravity  # gravity points down
m1, r1, I1 = 1.0, 0.3, 0.18083
m2, r2, I2 = 0.4, 0.375, 0.07238
L1 = 1.0
P, Q, R = I1 + m2 * L1 * L1, I2, m2 * L1 * r2

def qdd_closed(phi, psi, pd, sd):
    c, s = np.cos(psi), np.sin(psi)
    m11, m12, m22 = P + Q + 2 * R * c, Q + R * c, Q
    b1 = 2 * R * s * pd * sd + R * s * sd * sd + (m1 * r1 + m2 * L1) * gz * np.cos(phi) + m2 * r2 * gz * np.cos(phi + psi)
    b2 = -R * s * pd * pd + m2 * r2 * gz * np.cos(phi + psi)
    det = m11 * m22 - m12 * m12
    return (b1 * m22 - b2 * m12) / det, (m11 * b2 - m12 * b1) / det

def energy(phi, psi, pd, sd):
    w2 = pd + sd
    T = 0.5 * P * pd**2 + 0.5 * Q * w2**2 + R * np.cos(psi) * pd * w2
    U = -gz * (m1 * r1 * np.sin(phi) + m2 * (L1 * np.sin(phi) + r2 * np.sin(phi + psi)))
    return T + U

def tip(phi, psi):  # elbow link's centre of mass, (y, z)
    return np.stack([L1 * np.cos(phi) + r2 * np.cos(phi + psi), L1 * np.sin(phi) + r2 * np.sin(phi + psi)], -1)
reach = L1 + r2

def load(name):
    d = np.genfromtxt(f"{SP}/exp/traces/two_joint_arm_{name}.csv", delimiter=",", names=True)
    q = np.stack([2 * np.arctan2(d[f"j{j}_qx"], d[f"j{j}_qw"]) for j in (0, 1)], 1)
    return d["t"], np.unwrap(q, axis=0), np.stack([d["j0_v0"], d["j1_v0"]], 1), np.stack([d["j0_a0"], d["j1_a0"]], 1)

t, q_rk4, qd_rk4, qdd_rk4 = load("rk4")
dt = float(np.float32(0.002))
# Closed-form truth: Lagrangian EOM integrated by DOP853 at rtol 1e-13.
def rhs(_, y):
    a, b = qdd_closed(y[0], y[1], y[2], y[3])
    return [y[2], y[3], a, b]
sol = solve_ivp(rhs, (0, t[-1]), [0, 0, 0, 0], method="DOP853", rtol=1e-13, atol=1e-13, t_eval=t)
q_true = sol.y[:2].T
tip_true = tip(q_true[:, 0], q_true[:, 1])

# MuJoCo, same scene and dt, double precision.
def mj_run(integ):
    m = mujoco.MjModel.from_xml_string(a2m.to_mjcf(scene, dt, integ))
    d = mujoco.MjData(m)
    q = np.empty((t.size, 2)); qd = np.empty((t.size, 2))
    q[0], qd[0] = d.qpos, d.qvel
    for k in range(1, t.size):
        mujoco.mj_step(m, d)
        q[k], qd[k] = d.qpos, d.qvel
    return m, q, qd
mj = {k: mj_run(v) for k, v in {"euler": "Euler", "rk4": "RK4", "implicitfast": "implicitfast"}.items()}

out = {"dt": dt, "reach": reach, "pe_span": None, "series": {}}
g = 9.8
out["pe_span"] = 2 * g * (m1 * r1 + m2 * (L1 + r2))
E0 = energy(0, 0, 0, 0)
idx = np.arange(0, t.size, 10)  # every 20 ms
out["t"] = t[idx].tolist()

# 1. Instantaneous dynamics along the Achilles RK4 trajectory.
a_cf = np.stack(qdd_closed(q_rk4[:, 0], q_rk4[:, 1], qd_rk4[:, 0], qd_rk4[:, 1]), 1)
m, d = mj["rk4"][0], mujoco.MjData(mj["rk4"][0])
a_mj = np.empty_like(a_cf)
for k in range(t.size):
    d.qpos[:], d.qvel[:] = q_rk4[k], qd_rk4[k]
    mujoco.mj_forward(m, d)
    a_mj[k] = d.qacc
rel = lambda a, b: np.linalg.norm(a - b, axis=1) / np.linalg.norm(b, axis=1)
W = 50  # max over each 0.1 s window, full resolution
wmax = lambda v: v[1:1 + (v.size - 1) // W * W].reshape(-1, W).max(1).tolist()
out["t_win"] = (t[1:1 + (t.size - 1) // W * W].reshape(-1, W)[:, -1]).tolist()
out["qdd_rel_vs_closed"] = wmax(rel(qdd_rk4, a_cf))
out["qdd_rel_vs_mujoco"] = wmax(rel(qdd_rk4, a_mj))
out["qdd_rel_mujoco_vs_closed"] = wmax(rel(a_mj, a_cf))
m10 = t <= 10 + 1e-9
print("0-10 s: qdd rel achilles vs closed max %.2e, vs mujoco max %.2e, mujoco vs closed max %.2e" % (rel(qdd_rk4, a_cf)[m10].max(), rel(qdd_rk4, a_mj)[m10].max(), rel(a_mj, a_cf)[m10].max()))
print("qdd rel err  achilles vs closed: max %.2e median %.2e" % (rel(qdd_rk4, a_cf).max(), np.median(rel(qdd_rk4, a_cf))))
print("qdd rel err  achilles vs mujoco: max %.2e" % rel(qdd_rk4, a_mj).max())
print("qdd rel err  mujoco vs closed: max %.2e" % rel(a_mj, a_cf).max())

# 2. Trajectories and energy, per integrator.
for name in ["euler", "verlet", "midpoint", "rk4"]:
    tt, q, qd, _ = load(name)
    e = energy(q[:, 0], q[:, 1], qd[:, 0], qd[:, 1])
    err = 100 * np.linalg.norm(tip(q[:, 0], q[:, 1]) - tip_true, axis=1) / reach
    out["series"][f"achilles_{name}"] = {"energy": e[idx].tolist(), "tip_err_vs_truth": err[idx].tolist()}
    m10 = t <= 10 + 1e-9
    drift = 100 * np.max(np.abs(e - E0)[m10]) / out["pe_span"]
    print(f"[0-10 s] maxabs dE {np.max(np.abs(e - E0)[m10]):.2e} J")
    print(f"achilles {name:9s} energy drift max {drift:.2e} %PE  final dE {e[-1]-E0:+.3e} J  tip err @1s {err[500]:.1e} @5s {err[2500]:.1e} @10s {err[5000]:.1e}")
for name, (m, q, qd) in mj.items():
    e = energy(q[:, 0], q[:, 1], qd[:, 0], qd[:, 1])
    err = 100 * np.linalg.norm(tip(q[:, 0], q[:, 1]) - tip_true, axis=1) / reach
    out["series"][f"mujoco_{name}"] = {"energy": e[idx].tolist(), "tip_err_vs_truth": err[idx].tolist()}
    drift = 100 * np.max(np.abs(e - E0)) / out["pe_span"]
    print(f"mujoco   {name:12s} energy drift max {drift:.2e} %PE  tip err @1s {err[500]:.1e} @5s {err[2500]:.1e} @10s {err[5000]:.1e}")
# Achilles RK4 vs MuJoCo RK4 directly (for the side-by-side clip)
e_am = 100 * np.linalg.norm(tip(q_rk4[:, 0], q_rk4[:, 1]) - tip(mj["rk4"][1][:, 0], mj["rk4"][1][:, 1]), axis=1) / reach
out["tip_err_achilles_rk4_vs_mujoco_rk4"] = e_am[idx].tolist()
for thr in (0.1, 1, 5):
    k = np.nonzero(e_am > thr)[0]
    print(f"achilles rk4 vs mujoco rk4 first > {thr}% reach at t = {t[k[0]] if k.size else None}")
json.dump(out, open(f"{SP}/exp/dp_results.json", "w"))
