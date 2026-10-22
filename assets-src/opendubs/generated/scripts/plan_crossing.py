"""Plan the adversarial bimanual crossing from openarm's own test suite with the
unmodified ArmGroup planner, and record the naive straight-line path next to it.

Writes crossing.npz: planned left/right joint trajectories (synchronized), the
naive straight-line paths, and per-sample left-vs-right contact flags for both.
"""
import sys
import time

import numpy as np

sys.path.insert(0, "/home/user/prl/openarm/tests")
from test_openarm_bimanual_planning import (  # noqa: E402
    _cross_arm_contacts,
    _reach_into_other_workspace,
    _straight_line,
)

from openarm.config import OpenarmConfig  # noqa: E402
from openarm.robot import Openarm  # noqa: E402

out = sys.argv[1]
robot = Openarm(config=OpenarmConfig.default())
# The test's goal pair predates ArmGroup's 5 mm standoff; check overlap only,
# as the test does (README: "Set it to 0 to check overlap only").
robot._arm_group.config.planning_defaults.collision_margin_mm = 0.0
qL0 = np.asarray(robot.left.get_joint_positions(), float)
qR0 = np.asarray(robot.right.get_joint_positions(), float)
qL, qR = _reach_into_other_workspace(robot)

t = time.time()
res = robot.plan_to_configuration({"left": qL, "right": qR}, seed=0)
plan_s = time.time() - t
print("plan success", res is not None and res.success, f"{plan_s:.2f}s")
L, R = res.left, res.right
print("waypoints", L.num_waypoints, R.num_waypoints, "duration", getattr(L, "duration", None))

planned_hits = [bool(_cross_arm_contacts(robot, L.positions[i], R.positions[i])) for i in range(L.num_waypoints)]
n = L.num_waypoints
naive_L = _straight_line(qL0, qL, n)
naive_R = _straight_line(qR0, qR, n)
naive_hits = [bool(_cross_arm_contacts(robot, a, b)) for a, b in zip(naive_L, naive_R)]
print("planned colliding samples", sum(planned_hits), "/", n)
print("naive colliding samples", sum(naive_hits), "/", n)

np.savez(
    out,
    left=np.asarray(L.positions), right=np.asarray(R.positions),
    times=np.asarray(getattr(L, "timestamps", np.linspace(0, getattr(L, "duration", 1.0), n))),
    naive_left=np.asarray(naive_L), naive_right=np.asarray(naive_R),
    planned_hits=np.asarray(planned_hits), naive_hits=np.asarray(naive_hits),
    plan_s=plan_s,
)
