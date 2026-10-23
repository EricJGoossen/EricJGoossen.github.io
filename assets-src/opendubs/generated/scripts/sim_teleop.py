"""Drive Eric's Quest teleop (openarm.webxr_teleop: HandClutch, TeleopController,
the PhysicsEventLoop tick) headless in MuJoCo, with two scripted "hands" in
place of the headset's controller poses, and record the arms.

The teleop code runs unmodified (with one alias so the headless sim context
finds each arm by name); only the pose source differs: instead of
reading the WebXR bridge, each tick passes a scripted controller pose, grip and
trigger to the same HandClutch.update() the bridge reading feeds.

  sim_teleop.py <out.npz> [seconds] [speed scale]

speed scale multiplies the arms' joint velocity and acceleration limits
(openarm.config's SAFETY_SCALE = 0.02 of the motors' rated speed in the repo; the
robot runs faster now) and, above 1, also raises the pose servo's caps (to the
teleop config's 1 m/s, and the angular cap by the same scale) and its tracking
gain from 1/s to 8/s. 1 is the repo as it is; 5 is SAFETY_SCALE 0.1.
"""
import os
import sys
import types

import mujoco
import numpy as np

# The teleop module imports the mj_viser viewer at the top; nothing here uses
# it (no viewer, no panels), so a stand-in keeps that import from failing.
sys.modules.setdefault("mj_viser", types.SimpleNamespace(MujocoViewer=None, TeleopPanel=None))
from mj_manipulator.event_loop import PhysicsEventLoop
from mj_manipulator.teleop import TeleopConfig as ControllerConfig, TeleopController
from openarm.robot import Openarm
from openarm.webxr_teleop.teleop_config import TeleopConfig
from openarm.webxr_teleop.webxr_teleop import HandClutch

out = sys.argv[1]
seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 16.0
speed = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
config = TeleopConfig.default()
robot = Openarm()
for side in ("left", "right"):
    lim = robot.arms[side].config.kinematic_limits
    lim.velocity = np.asarray(lim.velocity) * speed
    lim.acceleration = np.asarray(lim.acceleration) * speed
    if speed > 1:  # the pose servo's twist caps (mj_manipulator defaults 0.2 m/s, 0.5 rad/s)
        robot.arms[side].config.max_cartesian_speed = TeleopConfig.default().control.max_cartesian_speed
        robot.arms[side].config.max_cartesian_angular *= speed
        robot.arms[side].config.reactive_gain = float(os.environ.get("GAIN", 4.0))  # pose error -> twist, 1/s (default 1)
loop = PhysicsEventLoop()
m, d = robot.model, robot.data
joints = {s: [m.joint(n).qposadr[0] for n in robot.arms[s].config.joint_names] for s in ("left", "right")}
fingers = {s: [m.joint(f"openarm_{s}_finger_joint{i}").qposadr[0] for i in (1, 2)] for s in ("left", "right")}
dt = config.timing.period
rec_every = max(1, int(round(1 / 30 / dt)))


def hand(side, t):
    """The scripted controller: lift the hand forward, trace loops. Returns (world pose, grip, trigger)."""
    sgn = 1 if side == "left" else -1
    T = np.eye(4)
    w = 2 * np.pi / 3.0
    phase = 0 if side == "left" else np.pi
    on = 0.5 - 0.5 * np.cos(np.pi * min(t / 1.5, 1.0))
    T[:3, 3] = on * np.array([0.05 * np.sin(w * t + phase),
                              sgn * 0.06 * np.sin(w * t / 2),
                              0.07 * np.sin(2 * w * t + phase)])
    a = 0.0  # hands keep their orientation
    T[:3, :3] = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
    grip = 1.0 if t > 0.3 else 0.0
    trigger = 0.0  # the headless sim context has no gripper to toggle
    return T, grip, trigger


# Start from a working pose (arms forward, grippers level) rather than
# hanging straight down, where the arm is singular.
for s in ("left", "right"):
    sgn = 1 if s == "left" else -1
    T = np.eye(4)
    z_ax = np.array([1.0, 0, 0])
    y_ax = np.cross(z_ax, [0, 0, 1.0])
    T[:3, :3] = np.c_[np.cross(y_ax, z_ax), y_ax, z_ax]
    T[:3, 3] = [0.30, sgn * 0.20, 0.42]
    sols = robot.arms[s].ik_solver.solve(T) or robot.arms[s].ik_solver.solve(T @ np.diag([-1.0, -1, 1, 1]))
    d.qpos[joints[s]] = sols[0]
mujoco.mj_forward(m, d)

frames = {"left": [], "right": [], "fL": [], "fR": [], "tL": [], "tR": [], "engaged": []}
with robot.sim(physics=False, headless=True, event_loop=loop) as ctx:
    arms = {s: robot.arms[s] for s in ("left", "right")}
    # The sim controller keys its arms "left"/"right", while TeleopController
    # addresses them by arm name ("openarm_left"); alias the two.
    for s in arms:
        ctx._controller._arms[arms[s].config.name] = ctx._controller._arms[s]
    arm_by_side = ctx.arm
    ctx.arm = lambda name: arm_by_side(name.removeprefix("openarm_"))
    # The repo's teleop speed override (webxr_teleop.ControlConfig, 1 m/s), handed to
    # the controller; with speed scale 1, the controller's own default (0.2 m/s
    # from the arm config) applies, as it does without the override.
    cart = config.control.max_cartesian_speed if speed > 1 else None
    ctrl = {s: TeleopController(arms[s], ctx, ControllerConfig(max_cartesian_speed=cart)) for s in arms}
    for c in ctrl.values():
        c.activate()
        loop.register_teleop(c, None)
    cfgs = {"left": config.left_clutch, "right": config.right_clutch}
    clutch = {s: HandClutch(arms[s], ctrl[s], s.upper(), cfgs[s]) for s in arms}
    origin = {s: None for s in arms}
    for k in range(int(seconds / dt)):
        t = k * dt
        for s in arms:
            T, grip, trigger = hand(s, t)
            clutch[s].update(T, grip, trigger)
        loop.tick()
        if k % rec_every == 0:
            frames["left"].append(d.qpos[joints["left"]].copy())
            frames["right"].append(d.qpos[joints["right"]].copy())
            frames["fL"].append(d.qpos[fingers["left"]].copy())
            frames["fR"].append(d.qpos[fingers["right"]].copy())
            for s, key in (("left", "tL"), ("right", "tR")):
                lt = clutch[s]._last_target
                frames[key].append(lt[:3, 3].copy() if lt is not None else np.full(3, np.nan))
np.savez(out, **{k: np.array(v) for k, v in frames.items()}, fps=30)
print("frames", len(frames["left"]))
