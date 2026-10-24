"""Run Eric's automatic reset (fleet_so101_infra, branch EricG/automatic-reset) on a mock arm,
exactly as its end-to-end unit test does -- the real IK, planner and ScriptedReset, the peg seen
through a calibrated sim camera -- for a few scrambled peg poses, and record every joint
command with its time.

  capture_reset.py <fleet_so101_infra checkout> <out.npz>

Writes, per command: time (s), the six joints in USD degrees (the sim's convention, which the
SO-101 MJCF shares), and per reset the peg's pose before (base_from_peg, its bottom-face frame)
and the start pose it was put back to.
"""
import math
import sys
from pathlib import Path

repo = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(repo / "src"), str(repo)]

import numpy as np  # noqa: E402

from fleet_so101.arm.backend import MockBackend  # noqa: E402
from fleet_so101.arm.calibration import synthetic_calibration  # noqa: E402
from fleet_so101.arm.joints import JOINT_NAMES  # noqa: E402
from fleet_so101.arm.safety import ManualClock, SafetyConfig  # noqa: E402
from fleet_so101.arm.so101_arm import ArmConfig, SO101Arm  # noqa: E402
from fleet_so101.sim.kinematics import usd_joint_angles_deg  # noqa: E402
from tests.unit.tasks import test_prop_reset as T  # noqa: E402


class Recording(MockBackend):
    """The test's mock backend, keeping every joint command and when it was sent."""

    def __init__(self, clock, **kw):
        super().__init__(**kw)
        self.clock, self.log = clock, []

    def write_joints(self, command):
        super().write_joints(command)
        self.log.append((self.clock.monotonic(), {n: float(command[n]) for n in JOINT_NAMES}))


def setup():
    clock = ManualClock()
    backend = Recording(clock, calibration=synthetic_calibration(), max_rate=10_000.0)
    arm = SO101Arm(backend, calibration=backend.calibration,
                   config=ArmConfig(arm_id="arm01", ramp_seconds=0.2, ramp_fps=10.0),
                   safety_config=SafetyConfig(max_step=500.0, limit_margin=2.0),
                   clock=clock, sleep=clock.advance)
    arm.connect()
    return clock, backend, arm, T.reset_for(clock, T.HOME)


# Candidate scrambles (centre, yaw, lying); the ones the planner can reach are kept, the first
# four in this order. Lying pegs rest with their centre 15 mm over the table, as in the test.
candidates = [((0.18, -0.06, 0.015), 30.0, True), ((0.17, 0.10, 0.015), 15.0, True),
              ((0.20, -0.01, 0.015), -50.0, True), ((0.15, -0.12, 0.015), 70.0, True),
              ((0.23, 0.02, 0.015), -20.0, True), ((0.16, 0.02, 0.015), 120.0, True),
              ((0.21, -0.10, 0.015), 45.0, True), ((0.19, 0.14, 0.015), -30.0, True)]
scrambles = []
for c in candidates:
    clock, backend, arm, reset = setup()
    if reset.reset(T.context(T.World(arm, T.peg_pose(c[0], c[1], lying=c[2]), T.PUT_BACK)), None):
        scrambles.append(c)
    if len(scrambles) == 4:
        break

clock, backend, arm, reset = setup()
befores, results = [], []
for centre, yaw, lying in scrambles:
    found = T.peg_pose(centre, yaw, lying=lying)
    befores.append((len(backend.log), found))
    ok = reset.reset(T.context(T.World(arm, found, T.PUT_BACK)), None)
    outcome = T.last(reset)
    results.append(ok)
    print(f"peg at {centre} yaw {yaw}: {'reset' if ok else 'FAILED'} {outcome.reason or ''} "
          f"offset {float(outcome.detail.get('offset_m', float('nan'))) * 1000:.1f} mm")
geometry = reset.solver.geometry
t = np.array([c[0] for c in backend.log])
q = np.array([[usd_joint_angles_deg(c[1], geometry=geometry)[n] for n in JOINT_NAMES] for c in backend.log])
np.savez(sys.argv[2], t=t, q=q, names=np.array(JOINT_NAMES),
         start_index=np.array([b[0] for b in befores]), before=np.array([b[1] for b in befores]),
         put_back=T.PUT_BACK, ok=np.array(results))
print(len(t), "commands over", t[-1] - t[0], "s")
