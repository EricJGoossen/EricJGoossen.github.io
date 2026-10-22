"""Achilles narrow phase vs MuJoCo on random pose pairs. Writes coll/results.json."""
import json, subprocess, sys
import numpy as np, mujoco
SP, PROBE = sys.argv[1], sys.argv[2]
rng = np.random.default_rng(7)
M = 0.3  # contact margin, both engines
SHAPES = {  # name -> (achilles h, r, mujoco geom attrs)
    "sphere":  (lambda: (np.zeros(3), 0.25), lambda h, r: f'type="sphere" size="{r}"'),
    "capsule": (lambda: (np.array([0, 0, 0.35]), 0.12), lambda h, r: f'type="capsule" size="{r} {h[2]}"'),
    "box":     (lambda: (np.array([0.3, 0.18, 0.1]), 0.0), lambda h, r: f'type="box" size="{h[0]} {h[1]} {h[2]}"'),
}
TYPES = [("sphere", "sphere"), ("sphere", "capsule"), ("capsule", "capsule"),
         ("sphere", "box"), ("capsule", "box"), ("box", "box")]

def rand_quat():
    q = rng.normal(size=4); q /= np.linalg.norm(q)
    return q if q[0] >= 0 else -q

def mj_model(a, b):
    (ha, ra), (hb, rb) = SHAPES[a][0](), SHAPES[b][0]()
    xml = f"""<mujoco><option gravity="0 0 0"/><worldbody>
<body name="A"><freejoint/><geom name="A" {SHAPES[a][1](ha, ra)} margin="{M/2}"/></body>
<body name="B"><freejoint/><geom name="B" {SHAPES[b][1](hb, rb)} margin="{M/2}"/></body>
</worldbody></mujoco>"""
    m = mujoco.MjModel.from_xml_string(xml)
    return m, mujoco.MjData(m), (ha, ra), (hb, rb)

rows, meta = [], []
for a, b in TYPES:
    m, d, (ha, ra), (hb, rb) = mj_model(a, b)
    got, tries = 0, 0
    while got < 300 and tries < 20000:
        tries += 1
        qa, qb = rand_quat(), rand_quat()
        pa = np.zeros(3)
        pb = rng.uniform(-1, 1, 3) * 0.9
        d.qpos[:] = np.concatenate([pa, qa, pb, qb]); d.qvel[:] = 0
        mujoco.mj_forward(m, d)
        if d.ncon == 0:
            continue
        cons = []
        for i in range(d.ncon):
            c = d.contact[i]
            n = np.array(c.frame[:3])
            if c.geom1 == 1:  # MuJoCo listed B first: flip to A -> B
                n = -n
            cons.append((c.dist, n, np.array(c.pos)))
        got += 1
        rows.append(" ".join(map(str, [*ha, ra, M, *pa, *qa, *hb, rb, M, *pb, *qb])))
        meta.append({"type": f"{a}-{b}", "mj": [(float(c[0]), c[1].tolist(), c[2].tolist()) for c in cons]})
    print(a, b, got, "pairs from", tries, "tries")

open(f"{SP}/coll/pairs.txt", "w").write("\n".join(rows))
out = subprocess.run([PROBE], input="\n".join(rows) + "\n", capture_output=True, text=True, check=True).stdout.split("\n")
res = []
for line, mt in zip(out, meta):
    v = np.array(line.split(), float)
    n, dist, pts, act = v[:3], v[3:7], v[7:19].reshape(4, 3), v[19:23].astype(bool)
    if not act.any():
        res.append({**mt, "ach": None}); continue
    k = np.argmin(np.where(act, dist, np.inf))
    md = min(c[0] for c in mt["mj"])
    mk = int(np.argmin([c[0] for c in mt["mj"]]))
    mn, mp = np.array(mt["mj"][mk][1]), np.array(mt["mj"][mk][2])
    res.append({**mt, "ach": {"dist": float(dist[k]), "n": n.tolist(), "p": pts[k].tolist(), "count": int(act.sum())},
                "d_mj": md, "d_err": float(dist[k] - md),
                "n_err_deg": float(np.degrees(np.arccos(np.clip(n @ mn, -1, 1)))),
                "p_err": float(np.linalg.norm(pts[k] - mp)), "count_mj": len(mt["mj"])})
json.dump(res, open(f"{SP}/coll/results.json", "w"))
for t in [f"{a}-{b}" for a, b in TYPES]:
    R = [r for r in res if r["type"] == t]
    ok = [r for r in R if r["ach"]]
    de = np.abs([r["d_err"] for r in ok]); ne = np.array([r["n_err_deg"] for r in ok]); pe = np.array([r["p_err"] for r in ok])
    cm = np.mean([r["ach"]["count"] == r["count_mj"] for r in ok])
    print(f"{t:16s} n={len(R)} missed={len(R)-len(ok)}  |dist err| median {np.median(de):.1e} p99 {np.percentile(de,99):.1e} max {de.max():.1e}  "
          f"normal err median {np.median(ne):.1e} max {ne.max():.2f} deg  point err median {np.median(pe):.1e} max {pe.max():.1e}  same contact count {100*cm:.0f}%")
