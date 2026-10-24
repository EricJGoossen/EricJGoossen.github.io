"""Plan a two-arm handover of a can on the OpenArm model with the unmodified
ArmGroup planner (openarm's Openarm wrapper around mj_manipulator), for the
OpenDubs page hero.

The right arm picks the can off a table, both arms meet in the middle (one
two-arm plan), the left arm takes it and sets it down on the other side; then
the same in mirror, so the clip loops. The can is carried kinematically (it
follows the gripper that holds it). Each move is planned by ArmGroup, then made
direct: a straight joint-space move if that is collision-free, otherwise the
plan shortcut and splined, every sample re-checked with the robot's own collision
checker (table included); moves start and stop smoothly (quintic timing).

  plan_handover.py <out.npz>
Writes per-frame joint positions for both arms and fingers, and the can's pose.
"""
import contextlib
import io
import os
import re
import sys

import mujoco
import numpy as np
from scipy.interpolate import CubicSpline
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation, Slerp

from openarm.config import OpenarmConfig
from openarm.robot import Openarm
import handover_scene

out = sys.argv[1]
TABLE_Z = 0.40       # table top
CAN_HALF = 0.0615    # the can's half height (prl_assets "can")
SPOTS = {"right": np.array([0.36, -0.17]), "left": np.array([0.38, 0.12])}  # the left arm runs into a joint limit placing further out
HANDOVER = np.array([0.33, 0.0, 0.58])
FPS = 30

# The OpenArm scene plus a table and the can (written next to the generated model
# so its relative mesh paths still resolve; removed at the end).
cfg = OpenarmConfig.default()
src = cfg.model_path.read_text()
scene = cfg.model_path.with_name("openarm_bimanual_handover_tmp.xml")
scene.write_text(handover_scene.scene_xml(src, TABLE_Z, CAN_HALF))
cfg.model_path = scene
try:
    robot = Openarm(config=cfg)
finally:
    scene.unlink()
m, d = robot.model, robot.data
robot._arm_group.config.planning_defaults.collision_margin_mm = 5.0

joint = {s: [m.joint(n).qposadr[0] for n in robot._arm_group[s].config.joint_names] for s in ("left", "right")}
finger = {s: [m.joint(f"openarm_{s}_finger_joint{i}").qposadr[0] for i in (1, 2)] for s in ("left", "right")}
can_mocap = m.body("can_prop").mocapid[0]

# Gripper orientations (columns: tcp x, y, z; z is the approach direction, the
# fingers close along y).
def approach(z):
    """Gripper orientation approaching horizontally along z, fingers closing horizontally."""
    z = np.asarray(z, float) / np.linalg.norm(z)
    y = np.cross(z, [0, 0, 1.0])
    y /= np.linalg.norm(y)
    return np.c_[np.cross(y, z), y, z]


# Straight ahead to pick from the table; angled 45° inward to pass and to place,
# which is where each arm's reach overlaps the other's (found by sweeping IK).
APPROACH = {"+x": approach([1, 0, 0]), "in_left": approach([1, -1, 0]), "in_right": approach([1, 1, 0])}
FLIP = np.diag([-1.0, -1.0, 1.0])  # the same approach, rolled 180°


def pose(R, p):
    T = np.eye(4)
    T[:3, :3], T[:3, 3] = R, p
    return T


frames = []  # (qL, qR, fL, fR, can position, can quaternion); fL, fR: each finger joint
state = {"mirror": False, "fL": np.full(2, 0.044), "fR": np.full(2, 0.044), "held": None, "can": np.r_[SPOTS["right"], TABLE_Z + CAN_HALF], "can_R": np.eye(3), "offset": None}


def ee(side):
    return robot._arm_group[side].get_ee_pose()


def record(qL, qR):
    d.qpos[joint["left"]], d.qpos[joint["right"]] = qL, qR
    mujoco.mj_forward(m, d)
    if state["held"]:
        T = ee(state["held"]) @ state["offset"]  # the can turns with the gripper holding it
        state["can"], state["can_R"] = T[:3, 3], T[:3, :3]
    quat = np.zeros(4)
    mujoco.mju_mat2Quat(quat, state["can_R"].flatten())
    frames.append((np.array(qL), np.array(qR), np.array(state["fL"]), np.array(state["fR"]), state["can"].copy(), quat))


def can_path(S):
    """Where the held can would be along joint path S (it follows the gripper): its
    positions, and its axis's height component (1 when upright, -1 upside down)."""
    keep = d.qpos.copy()
    side, pos, axis_z = state["held"], [], []
    for q in S:
        d.qpos[joint["left"]], d.qpos[joint["right"]] = q[:7], q[7:]
        mujoco.mj_kinematics(m, d)
        T = ee(side) @ state["offset"]
        pos.append(T[:3, 3])
        axis_z.append(T[2, 2])
    d.qpos[:] = keep
    mujoco.mj_forward(m, d)
    return np.array(pos), np.array(axis_z)


def keep_upright(S):
    """Re-solve the holding arm's three wrist joints along joint path S so the carried
    can's axis stays vertical (or upside down, if it already is). The can stays upright
    however the gripper turns about its axis, so the fit is also pulled toward the
    planned wrist (or that turn drifts and moves the gripper), and the correction fades
    to nothing at both ends, so the move still starts and ends exactly as planned.
    Returns the corrected path."""
    side = state["held"]
    if side is None:
        return S
    S = np.asarray(S)
    i0 = (0 if side == "left" else 7) + 4               # joints 5, 6, 7 of the holding arm
    keep = d.qpos.copy()
    up = np.sign((ee(side) @ state["offset"])[2, 2]) or 1.0
    out, prev = [], None
    n = len(S)

    def axis(q):
        d.qpos[joint["left"]], d.qpos[joint["right"]] = q[:7], q[7:]
        mujoco.mj_kinematics(m, d)
        return (ee(side) @ state["offset"])[:3, 2]

    for k, q0 in enumerate(S):
        q = q0.copy()
        w_plan = q0[i0:i0 + 3]
        w_start = w_plan if prev is None else prev

        def resid(w):
            q[i0:i0 + 3] = w
            a = axis(q) * up
            return np.r_[a[0], a[1], 0.03 * (w - w_plan), 0.03 * (w - w_start)]

        sol = least_squares(resid, w_start, bounds=(lo[i0:i0 + 3, 0], lo[i0:i0 + 3, 1]))
        prev = sol.x
        u = k / max(1, n - 1)
        taper = min(1.0, min(u, 1 - u) / 0.06)          # 0 at the ends, 1 in the middle
        q[i0:i0 + 3] = w_plan + (sol.x - w_plan) * taper
        out.append(q)
    d.qpos[:] = keep
    mujoco.mj_forward(m, d)
    return np.array(out)


def keeps_can_up(S):
    """The collision checker can't see the can (a prop), so a path that carries it must
    not dip or swing wide: the can stays within 6 cm of the lower of its start and end
    heights (or well clear of the tabletop) and no more than a little past the table's
    edge (the table is 0.30 m either side of the middle), and it stays within 35° of
    upright (or of upside down)."""
    if state["held"] is None:
        return True
    c, axis_z = can_path(np.asarray(S))
    low = min(min(c[0, 2], c[-1, 2]) - 0.06, TABLE_Z + CAN_HALF + 0.04)
    upright = np.abs(axis_z).min() >= np.cos(np.radians(35))  # a carried can doesn't tip over
    return c[:, 2].min() >= low and np.abs(c[:, 1]).max() <= 0.42 and upright


lo = np.r_[[m.jnt_range[m.joint(n).id] for sd in ("left", "right") for n in robot._arm_group[sd].config.joint_names]]


def within_limits(P, margin=0.01):
    return bool(np.all(P >= lo[:, 0] + margin) and np.all(P <= lo[:, 1] - margin))


def checker():
    """The group's own collision checker (table, other arm, 5 mm margin), built once per
    move: building it copies the model, so a fresh one per check is far too slow."""
    group = robot._arm_group
    fork = group.env.fork()
    return group._make_collision_checker(fork.model, fork.data)


def collision_free(q, chk):
    """q: both arms' joints, left then right."""
    return not chk.get_contacts(q)


def segment_free(a, b, chk, step=0.03):
    n = max(2, int(np.ceil(np.abs(b - a).max() / step)) + 1)
    return all(collision_free(a + (b - a) * u, chk) for u in np.linspace(0, 1, n))


def spline(W, chk, n=200):
    """A clamped cubic spline through waypoints W, or None if any sample collides."""
    W = np.asarray(W)
    W = W[np.r_[True, np.abs(np.diff(W, axis=0)).max(axis=1) > 1e-9]]  # drop repeated points
    if len(W) < 3:
        return None
    u = np.r_[0, np.cumsum(np.abs(np.diff(W, axis=0)).max(axis=1))]
    S = CubicSpline(u / u[-1], W, bc_type="clamped")(np.linspace(0, 1, n))
    return S if all(collision_free(q, chk) for q in S) else None


def length(P):
    return np.abs(np.diff(P, axis=0)).sum()


def smooth(P):
    """Make a planned path direct and smooth, every sample re-checked. In order:
    a straight joint-space move; a spline through one via point (the moving arms
    part-way or all the way to their ready pose); the planner's own path, shortcut
    and splined. Of the curved options the shortest collision-free one wins.
    Returns dense waypoints."""
    chk = checker()
    a, b = P[0], P[-1]
    if segment_free(a, b, chk):
        if state["held"] is None:
            return np.array([a, b])
        S = keep_upright(np.linspace(a, b, 60))        # carrying: keep the can level on the way
        if keeps_can_up(S) and all(collision_free(q, chk) for q in S):
            return S
    ready = np.r_[robot.named_poses["ready"]["left"], robot.named_poses["ready"]["right"]]
    moving = np.zeros(14, bool)
    for sl in (slice(0, 7), slice(7, 14)):
        moving[sl] = np.abs(b[sl] - a[sl]).max() > 1e-6
    options = []
    for w in (0.35, 0.7, 1.0):
        v = (a + b) / 2
        v[moving] = (1 - w) * v[moving] + w * ready[moving]
        if collision_free(v, chk):
            S = spline([a, v, b], chk)
            if S is not None:
                S = keep_upright(S)
                if keeps_can_up(S) and all(collision_free(q, chk) for q in S):
                    options.append(S)
    W = list(P[:: max(1, len(P) // 40)]) + [P[-1]]
    rng = np.random.default_rng(0)
    for _ in range(300):
        if len(W) < 3:
            break
        i, j = sorted(rng.choice(len(W), 2, replace=False))
        if j - i > 1 and segment_free(W[i], W[j], chk):
            W = W[: i + 1] + W[j:]
    S = spline(W, chk) if len(W) > 2 else None
    W = np.array(W)
    if S is not None:
        S = keep_upright(S)
        if keeps_can_up(S) and all(collision_free(q, chk) for q in S):
            options.append(S)
    else:
        Wd = keep_upright(dense(W))
        if keeps_can_up(Wd) and all(collision_free(q, chk) for q in Wd):
            options.append(Wd)
    if not options:
        return None
    return min(options, key=length)


def every(P, n=60):
    """About n rows of P, always including the last."""
    return np.vstack([P[:: max(1, len(P) // n)], P[-1]])


def dense(W, step=0.03):
    return np.concatenate([np.linspace(W[i], W[i + 1], max(2, int(np.abs(W[i + 1] - W[i]).max() / step) + 1))
                           for i in range(len(W) - 1)])


def play(P, vmax=0.8):
    """Record a joint-space path with a smooth start and stop (quintic timing)."""
    seg = np.abs(np.diff(P, axis=0)).max(axis=1)
    u = np.r_[0, np.cumsum(seg)]
    T = max(1.0, u[-1] / vmax * 1.875)  # quintic peak speed is 1.875x its average
    for k in range(int(T * FPS) + 1):
        tau = min(k / (T * FPS), 1.0)
        s_ = (10 * tau ** 3 - 15 * tau ** 4 + 6 * tau ** 5) * u[-1]
        q = np.array([np.interp(s_, u, P[:, j]) for j in range(P.shape[1])])
        record(q[:7], q[7:])


def rolls(exact):
    """Which rolls of a grasp to try: as given, or also turned 180° about the approach."""
    return (False,) if exact else ((True, False) if state["mirror"] else (False, True))


def plan(goals, exact=False):
    """One ArmGroup plan to {side: tcp pose}, trying both rolls of each grasp."""
    for flip in rolls(exact):
        g = {s: pose(R @ FLIP if flip else R, p) for s, (R, p) in goals.items()}
        res = robot.plan_ee_to_pose(g)
        if res is not None and res.success:
            P = np.c_[np.asarray(res.left.positions), np.asarray(res.right.positions)]
            Pfix = P.copy()
            for sd, sl in (("left", slice(0, 7)), ("right", slice(7, 14))):
                if sd not in goals:
                    Pfix[:, sl] = P[0, sl]  # an arm with no goal stays put
            if all(collision_free(q, checker_now) for q in dense(every(Pfix))):
                P = Pfix
            return P
    return None


def straight(goals, steps=30, exact=False):
    """A straight-line gripper path to {side: pose} (positions interpolated, rotations
    slerped), through ArmGroup's Cartesian planner, or None if it can't follow it
    cleanly. Carries, lifts and places look natural this way."""
    group = robot._arm_group
    for flip in rolls(exact):
        wps = {}
        for sd, (R, p) in goals.items():
            T0, T1 = ee(sd), pose(R @ FLIP if flip else R, p)
            rots = Slerp([0, 1], Rotation.from_matrix([T0[:3, :3], T1[:3, :3]]))(np.linspace(0, 1, steps))
            wps[sd] = [pose(r.as_matrix(), (1 - u) * T0[:3, 3] + u * T1[:3, 3])
                       for u, r in zip(np.linspace(0, 1, steps), rots)]
        keep = d.qpos.copy()
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                traj = group.plan_cartesian_path(wps, max_branch_jump=0.6, redundancy_window_rad=0.4,
                                                 redundancy_samples=17)
        except (ValueError, RuntimeError):
            continue
        finally:
            d.qpos[:] = keep  # leave the live state as it was for the next planner
            mujoco.mj_forward(m, d)
        P = np.asarray(traj.positions)
        chk = checker()
        if within_limits(P) and all(collision_free(q, chk) for q in dense(every(P))) and keeps_can_up(P):
            return P
    return None


def framed(side, R, p, n=6, exact=False):
    """A carry that stays close to a straight gripper line where the Cartesian planner
    can't follow one exactly: ArmGroup plans through n poses along the line (positions
    interpolated, rotations slerped), so each step is short and the can stays nearly
    level; smoothing then keeps it level between them. Returns a path, or None."""
    for flip in rolls(exact):
        T0, T1 = ee(side), pose(R @ FLIP if flip else R, p)
        u = np.linspace(0, 1, n + 1)[1:]
        rots = Slerp([0, 1], Rotation.from_matrix([T0[:3, :3], T1[:3, :3]]))(u)
        poses = [pose(r.as_matrix(), (1 - s_) * T0[:3, 3] + s_ * T1[:3, 3]) for s_, r in zip(u, rots)]
        for attempt in range(3):
            res = robot.plan_ee_to_pose({side: poses})
            if res is not None and res.success:
                S = smooth(np.c_[np.asarray(res.left.positions), np.asarray(res.right.positions)])
                if S is not None:
                    return S
    return None


def reachable_clear(side, R, p):
    """Whether `side` has an IK solution at exactly (R, p) that is clear of the table
    and the other arm."""
    i0 = 0 if side == "left" else 7
    now, chk = np.r_[frames[-1][0], frames[-1][1]], checker()
    for q in robot._arm_group[side].ik_solver.solve_valid(pose(R, p)):
        full = now.copy()
        full[i0:i0 + 7] = q
        if collision_free(full, chk):
            return True
    return False


def pick_ik(side, R, p, prefer, roll=None):
    """One IK solution for `side` at pose (R, p), trying both rolls of the grasp (or
    only `roll`, False for R as given, True for it turned 180°): "near" picks the one
    closest to the arm's current joints, "margin" the one furthest from any joint
    limit (so the arm isn't left at a limit, unable to go on to its next move). Only
    solutions clear of the table and the other arm count."""
    arm = robot._arm_group[side]
    lo_s, hi_s = arm.get_joint_limits()
    i0 = 0 if side == "left" else 7
    now = np.r_[frames[-1][0], frames[-1][1]]
    chk = checker()
    best, best_cost = None, np.inf
    for flip in (rolls(False) if roll is None else (roll,)):
        for q in arm.ik_solver.solve_valid(pose(R @ FLIP if flip else R, p)):
            full = now.copy()
            full[i0:i0 + 7] = q
            if not collision_free(full, chk):
                continue
            if prefer == "near":
                cost = float(np.linalg.norm(q - now[i0:i0 + 7]))
            else:
                cost = -float(np.min(np.minimum(q - lo_s, hi_s - q) / (hi_s - lo_s)))
            if cost < best_cost:
                best, best_cost = q, cost
    if best is None:
        raise RuntimeError(f"no IK for {side} at {np.round(p, 3)}")
    return best


def move_to(goal_q, label):
    """Plan both arms to joint goals {side: q} with ArmGroup, smooth it, record it."""
    for attempt in range(8):
        res = robot.plan_to_configuration(goal_q)
        if res is not None and res.success:
            S = smooth(np.c_[np.asarray(res.left.positions), np.asarray(res.right.positions)])
            if S is not None:
                print("planned", label, len(S), "waypoints", flush=True)
                return play(S)
        print("retrying", label, flush=True)
    raise RuntimeError(f"no smooth plan for {label}")


def move(goals, exact=False):
    """Move to {side: tcp pose}: a straight gripper line if ArmGroup's Cartesian planner
    can follow one, otherwise an ArmGroup plan (others hold still), smoothed. The
    planner is randomized, so a goal that gives no plan, or a plan that can't be
    smoothed, is planned again."""
    global checker_now
    S = straight(goals, exact=exact) if len(goals) == 1 else None  # two-arm moves stay ArmGroup plans
    how = "straight line"
    for attempt in range(8):
        if S is not None:
            break
        checker_now = checker()
        P = plan(goals, exact)
        S = smooth(P) if P is not None else None
        how = f"{len(S)} waypoints" if S is not None else ""
        if S is None:
            print("retrying", list(goals), flush=True)
    else:
        raise RuntimeError(f"no smooth plan to {goals}")
    print("planned", {s: np.round(p, 3).tolist() for s, (R, p) in goals.items()}, how, flush=True)
    play(S)


def hold(seconds, **fingers):
    """Hold the arms still while the named fingers open or close."""
    qL, qR = frames[-1][0], frames[-1][1]
    start = {k: state[k] for k in fingers}
    n = int(seconds * FPS)
    for k in range(1, n + 1):
        e = 0.5 - 0.5 * np.cos(np.pi * k / n)  # ease in and out
        for f, target in fingers.items():
            state[f] = start[f] + (target - start[f]) * e
        record(qL, qR)


def grasp(side):
    state["held"] = side
    state["offset"] = np.linalg.inv(ee(side)) @ pose(state["can_R"], state["can"])


def release():
    state["held"] = None


def settle():
    """Let a released can drop the last bit onto the table and stand up straight (it
    may have been set down tilted, or upside down after a rolled grasp), eased."""
    z0, z1 = state["can"][2], TABLE_Z + CAN_HALF
    R0 = state["can_R"]
    up = np.sign(R0[2, 2]) or 1.0          # keep it the way up it is
    axis = np.cross(R0[:, 2], [0, 0, up])
    ang = np.arcsin(min(1.0, np.linalg.norm(axis)))
    n = max(6, int(np.ceil(abs(z0 - z1) / 0.008)), int(np.ceil(ang / 0.05)))
    for k in range(1, n + 1):
        u = (k / n) ** 2
        Rk = R0
        if ang > 1e-6:
            Rk = Rotation.from_rotvec(axis / np.linalg.norm(axis) * ang * u).as_matrix() @ R0
        state["can"], state["can_R"] = np.r_[state["can"][:2], z0 + (z1 - z0) * u], Rk
        record(frames[-1][0], frames[-1][1])


OPEN = 0.044


def closed_on_can(side):
    """Each finger's travel at which it just touches the can, measured on the visible
    meshes. The two finger joints are independent and the can rarely sits exactly
    between them, so each finger closes by its own gap and both stop on the can's
    surface instead of one passing into it."""
    keep_q, keep_p, keep_r = d.qpos.copy(), d.mocap_pos[can_mocap].copy(), d.mocap_quat[can_mocap].copy()
    d.mocap_pos[can_mocap] = state["can"]
    mujoco.mju_mat2Quat(d.mocap_quat[can_mocap], state["can_R"].flatten())
    d.qpos[finger[side]] = OPEN
    mujoco.mj_kinematics(m, d)
    can_g, fromto, travel = m.geom("can_prop_visual").id, np.zeros(6), []
    for body in (f"openarm_{side}_right_finger", f"openarm_{side}_left_finger"):  # finger_joint1, finger_joint2
        bid = m.body(body).id
        gap = min(mujoco.mj_geomDistance(m, d, g, can_g, 0.1, fromto)
                  for g in range(m.ngeom) if m.geom_bodyid[g] == bid and m.geom_group[g] == 2)
        travel.append(float(np.clip(OPEN - (gap - 0.0005), 0.0, OPEN)))  # finger travel is 1:1 with the gap
    d.qpos[:], d.mocap_pos[can_mocap], d.mocap_quat[can_mocap] = keep_q, keep_p, keep_r
    mujoco.mj_forward(m, d)
    print(f"  {side} fingers close to {travel[0]:.4f} / {travel[1]:.4f} on the can", flush=True)
    return np.array(travel)


def back(R, p, dist=0.10):
    """dist back along the gripper's approach direction from p."""
    return p - dist * R[:, 2]


def go_ready(side):
    ready = np.array(robot.named_poses["ready"][side])
    for attempt in range(8):
        res = robot.plan_to_configuration({side: ready})
        S = smooth(np.c_[np.asarray(res.left.positions), np.asarray(res.right.positions)])
        if S is not None:
            return play(S)
    raise RuntimeError(f"no smooth plan to ready for {side}")


def pass_can(giver, taker, from_spot, to_spot):
    """giver picks the can at from_spot, hands it to taker, who sets it at to_spot."""
    fg, ft = ("fL" if giver == "left" else "fR"), ("fL" if taker == "left" else "fR")
    Rp = APPROACH["+x"]
    Rg = APPROACH["in_right" if giver == "right" else "in_left"]
    Rt = APPROACH["in_right" if taker == "right" else "in_left"]
    grip = np.r_[from_spot, TABLE_Z + CAN_HALF] + [0, 0, 0.015]
    move({giver: (Rp, back(Rp, grip))})
    move({giver: (Rp, grip)})
    hold(0.6, **{fg: closed_on_can(giver)})
    grasp(giver)
    move({giver: (Rp, grip + [0, 0, 0.10])})
    # The handover: both arms planned together into the shared space.
    give = HANDOVER + [0, 0, 0.025]
    take = HANDOVER - [0, 0, 0.035]  # low enough that the two grippers keep their 5 mm apart
    # Both arms planned together, to joint goals chosen here: the giver's nearest IK
    # solution, and for the taker the one furthest from its joint limits, so it can
    # carry the can on to the table without reconfiguring (and tipping it).
    # The taker grasps unrolled (the gripper's x axis up, as every pick is): the gripper
    # isn't symmetric top to bottom, and rolled over its hand would meet the table before
    # the can does when it sets it down. Rolling it over later would tip the can.
    move_to({giver: pick_ik(giver, Rg, give, "near"),
             taker: pick_ik(taker, Rt, back(Rt, take), "margin", roll=False)},
            f"{giver} to give, {taker} to take")
    move({taker: (Rt, take)}, exact=True)
    hold(0.6, **{ft: closed_on_can(taker)})
    grasp(taker)
    hold(0.5, **{fg: OPEN})
    move({giver: (Rg, back(Rg, give))})
    place = np.r_[to_spot, TABLE_Z + CAN_HALF] - [0, 0, 0.02]
    # Any heading works for a round can: take the first the taker can carry over the spot
    # in a straight, upright line (or close to one, through a few upright poses) and then
    # lower to just above the table (how far depends on where the can sits in the grip).
    # Otherwise plan over the spot and lower from there.
    sign = 1 if taker == "right" else -1
    rest = TABLE_Z + CAN_HALF
    # Unrolled headings only, the way the taker holds the can (see the take above).
    headings = [approach(v) for v in ([1, 0, 0], [1, 0.4 * sign, 0], [1, -0.4 * sign, 0],
                                      [1, 1.0 * sign, 0], [1, 0.8 * sign, 0])]
    for v in headings:
        over = straight({taker: (v, place + [0, 0, 0.08])}, exact=True)
        if over is None:
            over = framed(taker, v, place + [0, 0, 0.08], exact=True)
        if over is None:
            continue
        snap = (len(frames), {k: (v_.copy() if isinstance(v_, np.ndarray) else v_) for k, v_ in state.items()}, d.qpos.copy())
        play(over)
        T = ee(taker)
        # Down to the lowest height (1.5 to 4.5 cm above the table) where the hand clears
        # the tabletop: the taker holds the can low, so its hand meets the table before
        # the can does. The released can settles the rest of the way.
        Rh = T[:3, :3]
        lows = [T[:3, 3] - [0, 0, state["can"][2] - rest - clear] for clear in (0.015, 0.025, 0.035, 0.045)]
        lows = [p_ for p_ in lows if reachable_clear(taker, Rh, p_)][:1]
        if lows:
            low = lows[0]
            try:
                move({taker: (Rh, low)}, exact=True)
                print("planned", taker, "over the spot and down, heading", np.round(Rh[:, 2], 2), flush=True)
                break
            except RuntimeError:
                down = framed(taker, Rh, low, n=3, exact=True)
                if down is not None:
                    play(down)
                    print("planned", taker, "over the spot and down through poses, heading", np.round(Rh[:, 2], 2), flush=True)
                    break
        # this heading can't set it down: undo and try the next
        del frames[snap[0]:]
        state.update(snap[1])
        d.qpos[:] = snap[2]
        mujoco.mj_forward(m, d)
    else:
        move({taker: (Rp, place + [0, 0, 0.08])})
        T = ee(taker)
        Rh, low = T[:3, :3], T[:3, 3] - [0, 0, state["can"][2] - rest]
        try:
            move({taker: (Rh, low)}, exact=True)
        except RuntimeError:  # can't reach that exactly: set it down from just above instead
            low = T[:3, 3] - [0, 0, max(0.0, state["can"][2] - rest - 0.05)]
            move({taker: (Rh, low)}, exact=True)
    release()
    settle()
    hold(0.5, **{ft: OPEN})
    move({taker: (Rh, back(Rh, low))}, exact=True)
    go_ready(giver)
    go_ready(taker)


mujoco.mj_forward(m, d)
record(d.qpos[joint["left"]].copy(), d.qpos[joint["right"]].copy())
pass_can("right", "left", SPOTS["right"], SPOTS["left"])
state["mirror"] = True  # the mirror image of a grasp is the same grasp rolled 180°
pass_can("left", "right", SPOTS["left"], SPOTS["right"])

F = list(zip(*frames))
np.savez(out, left=np.array(F[0]), right=np.array(F[1]), fL=np.array(F[2]), fR=np.array(F[3]),
         can=np.array(F[4]), can_quat=np.array(F[5]), fps=FPS, table_z=TABLE_Z, can_half=CAN_HALF)
print("frames", len(frames), "seconds", len(frames) / FPS)
