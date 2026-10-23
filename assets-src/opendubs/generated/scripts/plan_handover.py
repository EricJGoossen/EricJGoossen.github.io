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
from scipy.spatial.transform import Rotation, Slerp

from openarm.config import OpenarmConfig
from openarm.robot import Openarm
import handover_scene

out = sys.argv[1]
TABLE_Z = 0.40       # table top
CAN_HALF = 0.0615    # the can's half height (prl_assets "can")
SPOTS = {"right": np.array([0.36, -0.17]), "left": np.array([0.36, 0.17])}
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


frames = []  # (qL, qR, fL, fR, can_pos)
state = {"mirror": False, "fL": 0.044, "fR": 0.044, "held": None, "can": np.r_[SPOTS["right"], TABLE_Z + CAN_HALF], "offset": None}


def ee(side):
    return robot._arm_group[side].get_ee_pose()


def record(qL, qR):
    d.qpos[joint["left"]], d.qpos[joint["right"]] = qL, qR
    mujoco.mj_forward(m, d)
    if state["held"]:
        state["can"] = (ee(state["held"]) @ state["offset"])[:3, 3]
    frames.append((np.array(qL), np.array(qR), state["fL"], state["fR"], state["can"].copy()))


def can_path(S):
    """Where the held can would be along joint path S (it follows the gripper)."""
    keep = d.qpos.copy()
    side, out = state["held"], []
    for q in S:
        d.qpos[joint["left"]], d.qpos[joint["right"]] = q[:7], q[7:]
        mujoco.mj_kinematics(m, d)
        out.append((ee(side) @ state["offset"])[:3, 3])
    d.qpos[:] = keep
    mujoco.mj_forward(m, d)
    return np.array(out)


def keeps_can_up(S):
    """The collision checker can't see the can (a prop), so a path that carries it must
    not dip or swing wide: the can stays within 6 cm of the lower of its start and end
    heights (or well clear of the tabletop) and no more than a little past the table's
    edge (the table is 0.30 m either side of the middle)."""
    if state["held"] is None:
        return True
    c = can_path(np.asarray(S))
    low = min(min(c[0, 2], c[-1, 2]) - 0.06, TABLE_Z + CAN_HALF + 0.04)
    return c[:, 2].min() >= low and np.abs(c[:, 1]).max() <= 0.42


lo = np.r_[[m.jnt_range[m.joint(n).id] for sd in ("left", "right") for n in robot._arm_group[sd].config.joint_names]]


def within_limits(P, margin=0.02):
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
    if segment_free(a, b, chk) and keeps_can_up(np.linspace(a, b, 40)):
        return np.array([a, b])
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
            if S is not None and keeps_can_up(S):
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
    if S is not None and keeps_can_up(S):
        options.append(S)
    elif keeps_can_up(dense(W)) and all(collision_free(q, chk) for q in dense(W)):
        options.append(W)
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
    state["offset"] = np.linalg.inv(ee(side)) @ pose(np.eye(3), state["can"])


def release():
    state["held"] = None


def settle():
    """Let a released can drop the last bit onto the table (eased, a few frames)."""
    z0, z1 = state["can"][2], TABLE_Z + CAN_HALF
    n = max(1, int(np.ceil(abs(z0 - z1) / 0.008)))
    for k in range(1, n + 1):
        state["can"] = np.r_[state["can"][:2], z0 + (z1 - z0) * (k / n) ** 2]
        record(frames[-1][0], frames[-1][1])


CLOSED = 0.012  # finger travel that just meets the can (set by eye in the render)
OPEN = 0.044


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
    hold(0.6, **{fg: CLOSED})
    grasp(giver)
    move({giver: (Rp, grip + [0, 0, 0.10])})
    # The handover: both arms planned together into the shared space.
    give = HANDOVER + [0, 0, 0.025]
    take = HANDOVER - [0, 0, 0.02]
    move({giver: (Rg, give), taker: (Rt, back(Rt, take))})
    move({taker: (Rt, take)})
    hold(0.6, **{ft: CLOSED})
    grasp(taker)
    hold(0.5, **{fg: OPEN})
    move({giver: (Rg, back(Rg, give))})
    place = np.r_[to_spot, TABLE_Z + CAN_HALF] - [0, 0, 0.02]
    # The can is round, so the taker turns its grip back to straight ahead on the way
    # over, the same approach it would pick with (the inward grip ends at a joint limit).
    move({taker: (Rp, place + [0, 0, 0.08])})
    # Lower until the can itself rests on the table (where it sits in this grip
    # depends on how it was taken), keeping the grip's orientation.
    T = ee(taker)
    Rh, low = T[:3, :3], T[:3, 3] - [0, 0, state["can"][2] - (TABLE_Z + CAN_HALF)]
    try:
        move({taker: (Rh, low)}, exact=True)
    except RuntimeError:  # can't reach that exactly: set it down from just above instead
        low = T[:3, 3] - [0, 0, max(0.0, state["can"][2] - (TABLE_Z + CAN_HALF) - 0.05)]
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
         can=np.array(F[4]), fps=FPS, table_z=TABLE_Z, can_half=CAN_HALF)
print("frames", len(frames), "seconds", len(frames) / FPS)
