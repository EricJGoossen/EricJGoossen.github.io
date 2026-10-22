"""The collision-free bimanual plan from plan_crossing.py, executed the way
mj_manipulator_ros ran a multi-arm plan before the bimanual refactor
(c7bedb6^: one trajectory after the other), checked with the same
left-vs-right oracle openarm's tests use.

usage (from a checkout of EricJGoossen/openarm): check_sequential.py crossing.npz out.npz
"""
import sys

import numpy as np

sys.path.insert(0, "tests")
from test_openarm_bimanual_planning import _cross_arm_contacts  # noqa: E402

from openarm.config import OpenarmConfig  # noqa: E402
from openarm.robot import Openarm  # noqa: E402

robot = Openarm(config=OpenarmConfig.default())
z = np.load(sys.argv[1])
L, R = z["left"], z["right"]
step = 4  # every 4th sample of the 125 Hz trajectory

left_first = [(L[i], R[0]) for i in range(0, len(L), step)] + [(L[-1], R[i]) for i in range(0, len(R), step)]
right_first = [(L[0], R[i]) for i in range(0, len(R), step)] + [(L[i], R[-1]) for i in range(0, len(L), step)]
hitsA = [bool(_cross_arm_contacts(robot, a, b)) for a, b in left_first]
hitsB = [bool(_cross_arm_contacts(robot, a, b)) for a, b in right_first]
print("left then right: colliding", sum(hitsA), "/", len(hitsA))
print("right then left: colliding", sum(hitsB), "/", len(hitsB))
np.savez(sys.argv[2], hitsA=hitsA, hitsB=hitsB, step=step)
