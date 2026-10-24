"""IK success of Eric's July 13 OpenArm artifact (ssik's joint-lock 7R solver over the
Raghavan-Roth 6R solver) on poses near the straight-arm home configuration, with whichever
ssik is first on sys.path. Targets are the FK of random joint configurations, every joint
within +-r of home (and of its limits). usage: ik_deadzone.py <artifact.py> <n per r> <out.npz>"""
import importlib.util, sys, time, warnings
import numpy as np
warnings.filterwarnings("ignore")
import ssik
from ssik.kinematics.poe_fk import poe_forward_kinematics as fk
spec = importlib.util.spec_from_file_location("art", sys.argv[1]); art = importlib.util.module_from_spec(spec); spec.loader.exec_module(art)
kb = art._KB
lim = np.array(art._JOINT_LIMITS, float)
n = int(sys.argv[2])
R = np.array([0, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0])
rng = np.random.default_rng(0)
ok = np.zeros((len(R), n), bool); err = np.full((len(R), n), np.inf); ms = np.zeros((len(R), n))
for i, r in enumerate(R):
    for j in range(n):
        q = np.clip(rng.uniform(-r, r, 7), lim[:, 0], lim[:, 1])
        T = fk(kb, q)
        t0 = time.perf_counter()
        try:
            sols = art.solve(T)
        except Exception:
            sols = []
        ms[i, j] = (time.perf_counter() - t0) * 1e3
        e = min((np.abs(fk(kb, np.asarray(s.q)) - T).max() for s in sols), default=np.inf)
        err[i, j] = e
        ok[i, j] = e < 1e-4
    print(f"r={r:<6g} solved {ok[i].sum()}/{n}  median {np.median(ms[i]):.0f} ms", flush=True)
print(ssik.__file__)
np.savez(sys.argv[3], r=R, ok=ok, err=err, ms=ms)
