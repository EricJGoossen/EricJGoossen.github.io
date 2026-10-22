import json, sys, math
sys.path.insert(0, sys.argv[1] + "/tools")
from svgchart import Chart, pow10
SP = sys.argv[1]
r = json.load(open(f"{SP}/exp/dp_results.json"))
n = sum(1 for v in r["t"] if v <= 10.0 + 1e-6)
t = r["t"][:n]; S = {k: {kk: vv[:n] for kk, vv in v.items()} for k, v in r["series"].items()}
nw = sum(1 for v in r["t_win"] if v <= 10.0 + 1e-6)
tw = r["t_win"][:nw]
for k in ("qdd_rel_vs_closed", "qdd_rel_mujoco_vs_closed", "qdd_rel_vs_mujoco"):
    r[k] = r[k][:nw]
E0 = 0.0
names = [("euler", "Semi-implicit Euler", "--s2"), ("verlet", "Velocity Verlet", "--s4"),
         ("midpoint", "Implicit midpoint", "--s3"), ("rk4", "RK4", "--s1")]

# --- Energy ---
c = Chart("Total energy of the double pendulum, by integrator",
          "Change in total energy over 10 seconds of a two-link pendulum released from horizontal, simulated by Achilles at a 2 ms step. "
          "Energy should stay constant. Semi-implicit Euler wanders by up to about 0.56 joules and velocity Verlet by about 0.28 joules; "
          "implicit midpoint and RK4 stay flat at this scale (within 0.001 joules).", h=380)
lo, hi = -0.9, 0.6
c.xscale(0, 10); c.yscale(lo, hi)
c.axes([0, 2, 4, 6, 8, 10], [-0.9, -0.6, -0.3, 0, 0.3, 0.6], "simulated time (s)", "energy change from start (J)",
       xfmt=lambda v: f"{v:g}", yfmt=lambda v: f"{v:+.1f}".replace("+0.0", "0").replace("-", "−"))
for key, label, var in names:
    e = S[f"achilles_{key}"]["energy"]
    c.line(t, [v - e[0] for v in e], var, width=2 if key != "euler" else 1.75)
c.legend([(l, v, False) for _, l, v in names])
c.label(c.X(0.3), c.Y(0) + 18, "Implicit midpoint and RK4 stay on this line (within 0.001 J)", cls="s m")
open(f"{SP}/charts/dp-energy.svg", "w").write(c.svg())
for key, *_ in names:
    e = S[f"achilles_{key}"]["energy"]; d = [v - e[0] for v in e]
    print(key, "energy min %.4f max %.4f" % (min(d), max(d)))

# --- Dynamics error vs closed form ---
c = Chart("Joint-acceleration error against the closed-form solution",
          "Relative error of the joint accelerations at every state along a 10 second double-pendulum run, compared with the closed-form Lagrangian equations of motion. "
          "Achilles, in single precision, stays between about 1e-8 and 3e-6, at the level of float32 round-off. MuJoCo, in double precision, sits near 1e-15. "
          "Achilles and MuJoCo differ from each other by the same amount Achilles differs from the closed form.", h=380)
c.xscale(0, 10); c.yscale(1e-17, 1e-4, log=True)
c.axes([0, 2, 4, 6, 8, 10], [1e-16, 1e-14, 1e-12, 1e-10, 1e-8, 1e-6, 1e-4], "simulated time (s)", "worst relative error in joint acceleration per 0.1 s (log scale)",
       xfmt=lambda v: f"{v:g}", yfmt=pow10)
c.hguide(1.19e-7, "float32 precision", below=True)
c.hguide(2.2e-16, "float64 precision", below=True)
c.line(tw, r["qdd_rel_mujoco_vs_closed"], "--ref", width=1.75)
c.line(tw, r["qdd_rel_vs_closed"], "--s1", width=1.75)
c.legend([("Achilles (float32) vs closed form", "--s1", False), ("MuJoCo (float64) vs closed form", "--ref", False)])
open(f"{SP}/charts/dp-accel-error.svg", "w").write(c.svg())

# --- Trajectory error vs closed form ---
c = Chart("Trajectory error against the closed-form solution, by integrator",
          "Distance between the simulated and the exact position of the pendulum's outer link, as a percent of the arm's reach, over 10 seconds at a 2 ms step. "
          "The exact trajectory is the closed-form equations of motion integrated to 1e-13 tolerance. RK4 starts around 1e-6 percent and implicit midpoint around 1e-5; "
          "Verlet and Euler start near 1e-2 percent. Because the pendulum is chaotic, every run eventually separates from the exact path.", h=380)
c.xscale(0, 10); c.yscale(1e-8, 300, log=True)
c.axes([0, 2, 4, 6, 8, 10], [1e-8, 1e-6, 1e-4, 1e-2, 1, 100], "simulated time (s)", "outer-link position error (% of reach, log scale)",
       xfmt=lambda v: f"{v:g}", yfmt=lambda v: {1: "1%", 100: "100%"}.get(v) or pow10(v, "%"))
for key, label, var in names:
    c.line(t[1:], S[f"achilles_{key}"]["tip_err_vs_truth"][1:], var, width=1.75)
c.legend([(l, v, False) for _, l, v in names])
open(f"{SP}/charts/dp-trajectory-error.svg", "w").write(c.svg())
