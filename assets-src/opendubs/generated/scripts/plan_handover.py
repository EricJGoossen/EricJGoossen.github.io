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


def collision_free(q):
    """q: both arms' joints, left then right. The robot's own checker (table included)."""
    d.qpos[joint["left"]], d.qpos[joint["right"]] = q[:7], q[7:]
    mujoco.mj_forward(m, d)
    with contextlib.redirect_stdout(io.StringIO()):
        return not robot.check_collisions()


def segment_free(a, b, step=0.03):
    n = max(2, int(np.ceil(np.abs(b - a).max() / step)) + 1)
    return all(collision_free(a + (b - a) * u) for u in np.linspace(0, 1, n))


def smooth(P):
    """Make a planned path direct and smooth: a straight joint-space move when that
    is collision-free, otherwise the planner's path shortcut and splined, with every
    sample re-checked. Returns dense waypoints."""
    a, b = P[0], P[-1]
    if segment_free(a, b):
        return np.array([a, b])
    W = list(P[:: max(1, len(P) // 40)]) + [P[-1]]
    rng = np.random.default_rng(0)
    for _ in range(300):
        if len(W) < 3:
            break
        i, j = sorted(rng.choice(len(W), 2, replace=False))
        if j - i > 1 and segment_free(W[i], W[j]):
            W = W[: i + 1] + W[j:]
    W = np.array(W)
    if len(W) > 2:
        u = np.r_[0, np.cumsum(np.abs(np.diff(W, axis=0)).max(axis=1))]
        cs = CubicSpline(u / u[-1], W, bc_type="clamped")
        S = cs(np.linspace(0, 1, 200))
        if all(collision_free(q) for q in S):
            return S
    return W


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


def move(goals):
    """Plan to {side: tcp pose} with ArmGroup (others hold still), smooth it, record it."""
    for flip in ((True, False) if state["mirror"] else (False, True)):
        g = {s: pose(R @ FLIP if flip else R, p) for s, (R, p) in goals.items()}
        res = robot.plan_ee_to_pose(g)
        if res is not None and res.success:
            break
    else:
        raise RuntimeError(f"no plan to {goals}")
    P = np.c_[np.asarray(res.left.positions), np.asarray(res.right.positions)]
    S = smooth(P)
    print("planned", {s: np.round(p, 3).tolist() for s, (R, p) in goals.items()}, len(S), "waypoints", flush=True)
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


CLOSED = 0.012  # finger travel that just meets the can (set by eye in the render)
OPEN = 0.044


def back(R, p, dist=0.10):
    """dist back along the gripper's approach direction from p."""
    return p - dist * R[:, 2]


def go_ready(side):
    ready = np.array(robot.named_poses["ready"][side])
    res = robot.plan_to_configuration({side: ready})
    play(smooth(np.c_[np.asarray(res.left.positions), np.asarray(res.right.positions)]))


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
    move({taker: (Rt, place + [0, 0, 0.08])})
    move({taker: (Rt, place)})
    release()
    state["can"] = np.r_[to_spot, TABLE_Z + CAN_HALF]
    hold(0.5, **{ft: OPEN})
    move({taker: (Rt, back(Rt, place))})
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
