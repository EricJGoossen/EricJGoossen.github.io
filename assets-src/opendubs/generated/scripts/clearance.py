"""Clearance between the two OpenArm arms over time for the crossing plan
(data/bimanual-crossing.npz), run three ways: left arm then right (how multi-arm
plans used to run on hardware), right then left, and both together from one start
stamp. Clearance is MuJoCo's signed distance between the closest left-arm and
right-arm collision geoms (negative = overlapping).

usage: clearance.py <bimanual-crossing.npz> <out.npz>
"""
import sys

import mujoco
import numpy as np
from openarm.config import OpenarmConfig

src, out = sys.argv[1], sys.argv[2]
z = np.load(src)
m = mujoco.MjModel.from_xml_path(str(OpenarmConfig.default().model_path))
d = mujoco.MjData(m)
J = {s: [m.joint(f"openarm_{s}_joint{i}").qposadr[0] for i in range(1, 8)] for s in ("left", "right")}
col = {s: [g for g in range(m.ngeom) if m.geom_group[g] == 3 and m.body(m.geom_bodyid[g]).name.startswith(f"openarm_{s}_")]
       for s in ("left", "right")}
L, R = z["left"], z["right"]
dur = float(z["times"][-1])
n = len(L)
step = 7


def clearance(ql, qr):
    d.qpos[J["left"]], d.qpos[J["right"]] = ql, qr
    mujoco.mj_forward(m, d)
    best = 1.0
    for a in col["left"]:
        for b in col["right"]:
            best = min(best, mujoco.mj_geomDistance(m, d, a, b, 0.3, None))
    return best


runs = {
    "left_then_right": [(L[i], R[0]) for i in range(0, n, step)] + [(L[-1], R[i]) for i in range(0, n, step)],
    "right_then_left": [(L[0], R[i]) for i in range(0, n, step)] + [(L[i], R[-1]) for i in range(0, n, step)],
    "together": [(L[i], R[i]) for i in range(0, n, step)],
}
res = {}
for k, pairs in runs.items():
    c = np.array([clearance(a, b) for a, b in pairs])
    t = np.linspace(0, dur * (2 if k != "together" else 1), len(c))
    res[k], res[k + "_t"] = c, t
    print(k, f"min {c.min() * 1000:.0f} mm", "overlapping samples", int((c < 0).sum()), "of", len(c))
np.savez(out, **res, dur=dur)
