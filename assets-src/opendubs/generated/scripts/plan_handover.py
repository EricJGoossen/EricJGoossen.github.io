"""Plan a two-arm handover of a can on the OpenArm model with the unmodified
ArmGroup planner (openarm's Openarm wrapper around mj_manipulator), for the
OpenDubs page hero.

The right arm picks the can off a table, both arms meet in the middle (one
two-arm plan), the left arm takes it and sets it down on the other side; then
the same in mirror, so the clip loops. The can is carried kinematically (it
follows the gripper that holds it); the arms' motions are ArmGroup's plans,
checked against the table and each other.

  plan_handover.py <out.npz>
Writes per-frame joint positions for both arms and fingers, and the can's pose.
"""
import os
import re
import sys

import mujoco
import numpy as np

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


def move(goals):
    """Plan to {side: tcp pose} with ArmGroup (others hold still) and record it."""
    for flip in ((True, False) if state["mirror"] else (False, True)):
        g = {s: pose(R @ FLIP if flip else R, p) for s, (R, p) in goals.items()}
        res = robot.plan_ee_to_pose(g)
        if res is not None and res.success:
            break
    else:
        raise RuntimeError(f"no plan to {goals}")
    print("planned", {s: np.round(p, 3).tolist() for s, (R, p) in goals.items()}, f"{res.left.timestamps[-1]:.1f}s", flush=True)
    L, R_ = res.left, res.right
    t = np.asarray(L.timestamps)
    for tk in np.arange(0, t[-1], 1 / FPS):
        i = min(np.searchsorted(t, tk), len(t) - 1)
        record(L.positions[i], R_.positions[i])
    record(L.positions[-1], R_.positions[-1])


def hold(seconds, **fingers):
    """Hold the arms still while the named fingers open or close."""
    qL, qR = frames[-1][0], frames[-1][1]
    start = {k: state[k] for k in fingers}
    n = int(seconds * FPS)
    for k in range(1, n + 1):
        for f, target in fingers.items():
            state[f] = start[f] + (target - start[f]) * k / n
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
    t = np.asarray(res.left.timestamps)
    for tk in np.arange(0, t[-1], 1 / FPS):
        i = min(np.searchsorted(t, tk), len(t) - 1)
        record(res.left.positions[i], res.right.positions[i])
    record(res.left.positions[-1], res.right.positions[-1])


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
