"""ArduPilot's position estimate (fusing the optical flow sensor) against mocap,
from the rosbag committed to rajitzg/opendubs-core in 391e3ec (recorded
2026-03-29, bag_20260329_002904/temp_0.mcap).

usage: flow_vs_mocap.py temp_0.mcap out.npz
Needs: pip install mcap mcap-ros2-support numpy

The EKF starts in its own frame (its origin and heading differ from the mocap
room frame), so its track is fitted to mocap with a 2D rotation + translation
(no scale) over the first 120 s, before the robot spins, then compared over the
whole run.
"""
import sys

import numpy as np
from mcap.reader import make_reader
from mcap_ros2.decoder import DecoderFactory

topics = {"/mavros/local_position/pose": [], "/mocap/opendubs/pose": []}
with open(sys.argv[1], "rb") as fh:
    reader = make_reader(fh, decoder_factories=[DecoderFactory()])
    for _, ch, msg, ros in reader.iter_decoded_messages(topics=list(topics)):
        p, q = ros.pose.position, ros.pose.orientation
        yaw = np.arctan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y**2 + q.z**2))
        topics[ch.topic].append((msg.log_time / 1e9, p.x, p.y, yaw))

e = np.array(topics["/mavros/local_position/pose"])
m = np.array(topics["/mocap/opendubs/pose"])
t0 = m[0, 0]
te, tm = e[:, 0] - t0, m[:, 0] - t0
mx, my = np.interp(te, tm, m[:, 1]), np.interp(te, tm, m[:, 2])

fit = te < 120
A, B = e[fit, 1:3], np.c_[mx[fit], my[fit]]
ca, cb = A.mean(0), B.mean(0)
U, _, Vt = np.linalg.svd((A - ca).T @ (B - cb))
R = Vt.T @ U.T
if np.linalg.det(R) < 0:
    Vt[1] *= -1
    R = Vt.T @ U.T
Ae = (e[:, 1:3] - ca) @ R.T + cb
err = np.hypot(Ae[:, 0] - mx, Ae[:, 1] - my)

yaw = np.unwrap(m[:, 3])
for a, b in [(0, 60), (60, 120), (120, 135), (135, 150), (150, 202)]:
    s, sm = (te >= a) & (te < b), (tm >= a) & (tm < b)
    path = np.sum(np.hypot(np.diff(m[sm, 1]), np.diff(m[sm, 2])))
    turn = np.degrees(yaw[sm].max() - yaw[sm].min())
    print(f"{a:3d}-{b:3d} s: error mean {err[s].mean():7.3f} m, max {err[s].max():7.3f} m; "
          f"robot drove {path:.2f} m, turned {turn:.0f} deg")

np.savez(sys.argv[2], t=te, err=err, ex=Ae[:, 0], ey=Ae[:, 1], mx=mx, my=my,
         tm=tm, mxr=m[:, 1], myr=m[:, 2], myaw=yaw)
