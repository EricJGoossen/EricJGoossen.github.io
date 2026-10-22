import sys, numpy as np
def load(path):
    t, rows = [], []
    for line in open(path):
        v = line.strip().split(",")
        t.append(float(v[0])); rows.append(np.array(v[1:], float).reshape(-1, 8))
    return np.array(t), np.stack(rows)   # (frames, bodies, [row, x,y,z, w,qx,qy,qz])
def tilt(q):  # angle of body +y from world +y
    w, x, y, z = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    up_y = 1 - 2 * (x * x + z * z)
    return np.degrees(np.arccos(np.clip(up_y, -1, 1)))
if __name__ == "__main__":
    t, P = load(sys.argv[1])
    ang = tilt(P[:, 1:, 4:8])       # skip the ground
    for i in range(ang.shape[1]):
        k = np.nonzero(ang[:, i] > 45)[0]
        print(i, f"falls past 45 deg at t={t[k[0]]:.3f}" if k.size else "never", f"final {ang[-1, i]:.1f} deg")
