"""Exact signed distance for sphere-swept boxes; adds d_true to coll/results.json."""
import json, sys
import numpy as np
from scipy.optimize import minimize
SP = sys.argv[1]

def R(q):
    w, x, y, z = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)],
                     [2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)],
                     [2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)]])

def inner_distance(ha, Ra, pa, hb, Rb, pb):
    def f(z):
        u, v = z[:3], z[3:]
        dvec = Ra @ u + pa - Rb @ v - pb
        return dvec @ dvec, np.concatenate([2 * Ra.T @ dvec, -2 * Rb.T @ dvec])
    bounds = [(-h, h) for h in ha] + [(-h, h) for h in hb]
    best = np.inf
    for z0 in (np.zeros(6), np.concatenate([ha * 0.5, -hb * 0.5]), np.concatenate([-ha * 0.5, hb * 0.5])):
        r = minimize(f, z0, jac=True, method="L-BFGS-B", bounds=bounds, options={"ftol": 1e-20, "gtol": 1e-14, "maxiter": 5000})
        best = min(best, r.fun)
    return np.sqrt(max(best, 0.0))

def sat_depth(ha, Ra, pa, hb, Rb, pb):
    axes = [Ra[:, i] for i in range(3)] + [Rb[:, i] for i in range(3)]
    for i in range(3):
        for j in range(3):
            c = np.cross(Ra[:, i], Rb[:, j])
            if np.linalg.norm(c) > 1e-9:
                axes.append(c / np.linalg.norm(c))
    t = pb - pa
    depth = np.inf
    for n in axes:
        ra = np.sum(ha * np.abs(Ra.T @ n)); rb = np.sum(hb * np.abs(Rb.T @ n))
        depth = min(depth, ra + rb - abs(t @ n))
    return depth  # >= 0 when overlapping (min overlap over the axes)

res = json.load(open(f"{SP}/coll/results.json"))
rows = open(f"{SP}/coll/pairs.txt").read().split("\n")
for r, line in zip(res, rows):
    v = np.array(line.split(), float)
    ha, ra, pa, qa = v[0:3], v[3], v[5:8], v[8:12]
    hb, rb, pb, qb = v[12:15], v[15], v[17:20], v[20:24]
    Ra, Rb = R(qa), R(qb)
    di = inner_distance(ha, Ra, pa, hb, Rb, pb)
    if di > 1e-7:
        r["d_true"] = di - ra - rb
    else:
        r["d_true"] = -(sat_depth(ha, Ra, pa, hb, Rb, pb) + ra + rb)
json.dump(res, open(f"{SP}/coll/results.json", "w"))
types = sorted({r["type"] for r in res}, key=lambda t: [x["type"] for x in res].index(t))
for t in types:
    ok = [r for r in res if r["type"] == t and r["ach"]]
    ea = np.abs([r["ach"]["dist"] - r["d_true"] for r in ok]); em = np.abs([r["d_mj"] - r["d_true"] for r in ok])
    print(f"{t:16s} achilles vs exact: median {np.median(ea):.1e} max {ea.max():.1e} (>1e-4: {np.sum(ea>1e-4)})   "
          f"mujoco vs exact: median {np.median(em):.1e} max {em.max():.1e} (>1e-4: {np.sum(em>1e-4)})")
