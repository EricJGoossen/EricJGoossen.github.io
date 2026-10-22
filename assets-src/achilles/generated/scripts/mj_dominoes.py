"""Run a free-box scene in MuJoCo and write poses in rec_driver's CSV layout (converted back to Achilles' Y-up)."""
import sys, math
import numpy as np, mujoco
sys.path.insert(0, sys.argv[0].rsplit("/", 1)[0])
from arow_boxes_to_mjcf import to_mjcf, qmul, QR
arow, out, seconds, fps = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
xml, q0, qd0 = to_mjcf(arow)
m = mujoco.MjModel.from_xml_string(xml); d = mujoco.MjData(m)
d.qpos[:], d.qvel[:] = q0, qd0
mujoco.mj_forward(m, d)
QRi = QR * np.array([1, -1, -1, -1])
spf = round(1 / (fps * m.opt.timestep))
with open(out, "w") as fh:
    for k in range(int(seconds * fps) + 1):
        row = [f"{k * spf * m.opt.timestep:.9g}", "0", "0", "-0.2", "0", "1", "0", "0", "0"]
        for b in range(1, m.nbody):
            p = d.xpos[b]; q = qmul(QRi, d.xquat[b])
            row += [str(b), f"{p[0]:.9g}", f"{p[2]:.9g}", f"{-p[1]:.9g}", *[f"{x:.9g}" for x in q]]
        fh.write(",".join(row) + "\n")
        mujoco.mj_step(m, d, nstep=spf)
