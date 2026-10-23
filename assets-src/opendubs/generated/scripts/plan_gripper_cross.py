"""Send both grippers through the middle and plan it two ways, with the unmodified
ArmGroup planner (openarm's Openarm wrapper around mj_manipulator):

  individually: each arm planned on its own, with the other arm standing at its
                start pose (so each plan is collision-free by itself), then both
                run at the same time, as two single-arm planners would
  together:     one ArmGroup plan for both goals

Both are checked for left-vs-right contact at every sample with the bimanual
planning tests' own oracle. Writes per-frame joints, contact flags and the contacts'
bodies.  usage: plan_gripper_cross.py <out.npz>
"""
import sys

import numpy as np

sys.path.insert(0, "/home/user/prl/openarm/tests")
from test_openarm_bimanual_planning import _cross_arm_contacts  # noqa: E402

from openarm.config import OpenarmConfig  # noqa: E402
from openarm.robot import Openarm  # noqa: E402

out = sys.argv[1]
FPS = 30
robot = Openarm(config=OpenarmConfig.default())
robot._arm_group.config.planning_defaults.collision_margin_mm = 5.0
m, d = robot.model, robot.data
J = {s: [m.joint(n).qposadr[0] for n in robot._arm_group[s].config.joint_names] for s in ("left", "right")}
FLIP = np.diag([-1.0, -1.0, 1.0])


def approach(z):
    z = np.asarray(z, float) / np.linalg.norm(z)
    y = np.cross(z, [0, 0, 1.0])
    y /= np.linalg.norm(y)
    return np.c_[np.cross(y, z), y, z]


def pose(R, p):
    T = np.eye(4)
    T[:3, :3], T[:3, 3] = R, p
    return T


def ik(side, T):
    for R in (T[:3, :3], T[:3, :3] @ FLIP):
        sols = robot._arm_group[side].ik_solver.solve(pose(R, T[:3, 3]))
        if sols:
            return sols[0]
    raise RuntimeError(f"no IK for {side} at {T[:3, 3]}")


def set_q(qL, qR):
    import mujoco
    d.qpos[J["left"]], d.qpos[J["right"]] = qL, qR
    mujoco.mj_forward(m, d)


# Start: each gripper forward on its own side.
starts = {"left": pose(approach([1, 0, 0]), [0.30, 0.20, 0.48]), "right": pose(approach([1, 0, 0]), [0.30, -0.20, 0.48])}
q0 = {s: ik(s, starts[s]) for s in starts}
# Goal pairs are drawn at random in front of the robot (seeded) and kept only if
# they are clear of each other and every other part of the robot, their solo plans
# collide at the grippers when run together, and ArmGroup can plan them jointly.
rng = np.random.default_rng(3)
GRIP = ("hand", "finger")


def random_goals():
    g = {}
    for s, sgn in (("left", 1), ("right", -1)):
        p = [rng.uniform(0.26, 0.40), -sgn * rng.uniform(-0.02, 0.18), rng.uniform(0.42, 0.58)]
        z = [1.0, -sgn * rng.uniform(0.0, 1.0), 0.0]
        g[s] = pose(approach(z), p)
    return g


def plan(goal_sides):
    set_q(q0["left"], q0["right"])
    for fl in (False, True):
        for fr in (False, True):
            flips = {"left": fl, "right": fr}
            g = {s: pose(goals[s][:3, :3] @ FLIP if flips[s] else goals[s][:3, :3], goals[s][:3, 3]) for s in goal_sides}
            res = robot.plan_ee_to_pose(g)
            if res is not None and res.success:
                return res
    return None


def resample(traj, n):
    t = np.asarray(traj.timestamps)
    P = np.asarray(traj.positions)
    tt = np.linspace(0, t[-1], n)
    return np.stack([np.interp(tt, t, P[:, j]) for j in range(P.shape[1])], axis=1), t[-1]


# Individually planned: left alone (right held at its start), right alone (left held).
# Take the first candidate whose solo plans collide when run together and that
# ArmGroup can plan jointly.
site = {sd: m.site(f"openarm_{sd}_ee_site").id for sd in ("left", "right")}


def ee_path(L, R):
    P = {"left": [], "right": []}
    for l, r in zip(L, R):
        set_q(l, r)
        for sd in P:
            P[sd].append(d.site_xpos[site[sd]].copy())
    return {sd: np.array(v) for sd, v in P.items()}


def detour(a, b):
    """How far path b strays from path a: the largest distance from a point of b to path a."""
    return max(np.min(np.linalg.norm(a - p, axis=1)) for p in b)


best, tried, found = None, 0, 0
while tried < 900 and found < 4:
    tried += 1
    goals = random_goals()
    try:
        qg = {sd: ik(sd, goals[sd]) for sd in goals}
    except RuntimeError:
        continue
    set_q(qg["left"], qg["right"])
    if robot.check_collisions():
        continue
    lines = [(q0["left"] + (qg["left"] - q0["left"]) * a, q0["right"] + (qg["right"] - q0["right"]) * a) for a in np.linspace(0, 1, 40)]
    if not any(any(x in "".join(c[:2]) for x in GRIP) for c in sum((_cross_arm_contacts(robot, l, r) for l, r in lines), [])):
        continue
    solo_L, solo_R = plan(["left"]), plan(["right"])
    if solo_L is None or solo_R is None:
        continue
    dur = max(solo_L.left.timestamps[-1], solo_R.right.timestamps[-1])
    n = int(dur * FPS)
    L_s, _ = resample(solo_L.left, n)
    R_s, _ = resample(solo_R.right, n)
    grip_hits = sum(any(any(x in b for x in GRIP) and any(x in a for x in GRIP) for a, b, _ in _cross_arm_contacts(robot, l, r))
                    for l, r in zip(L_s[::2], R_s[::2]))
    if grip_hits < 6:
        continue
    group = plan(["left", "right"])
    if group is None:
        continue
    ng = int(group.left.timestamps[-1] * FPS)
    L_g, _ = resample(group.left, ng)
    R_g, _ = resample(group.right, ng)
    ps, pg = ee_path(L_s, R_s), ee_path(L_g, R_g)
    dev = max(detour(ps[sd], pg[sd]) for sd in ps)
    found += 1
    print("try", tried, "gripper hits", grip_hits, f"detour {dev * 100:.1f} cm", flush=True)
    if best is None or dev > best[0]:
        best = (dev, L_s, R_s, L_g, R_g, np.r_[goals["left"][:3, 3], goals["right"][:3, 3]])
if best is None:
    raise SystemExit("no candidate worked")
_, L_solo, R_solo, L_grp, R_grp, cand = best
print(f"best detour {best[0] * 100:.1f} cm")


def contacts(L, R):
    hits, bodies = [], []
    for a, b in zip(L, R):
        c = _cross_arm_contacts(robot, a, b)
        hits.append(bool(c))
        bodies.append(";".join(sorted({x for pair in c for x in pair[:2]})))
    return np.array(hits), np.array(bodies)


h_solo, b_solo = contacts(L_solo, R_solo)
h_grp, b_grp = contacts(L_grp, R_grp)
print("solo frames", len(L_solo), "colliding", h_solo.sum(), "bodies", sorted(set(";".join(b_solo).split(";")) - {""}))
print("group frames", len(L_grp), "colliding", h_grp.sum())
np.savez(out, goal=np.array(cand), L_solo=L_solo, R_solo=R_solo, h_solo=h_solo, L_grp=L_grp, R_grp=R_grp, h_grp=h_grp,
         b_solo=b_solo, fps=FPS)
