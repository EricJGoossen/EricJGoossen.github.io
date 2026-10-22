"""ABA vs closed form: worst relative joint-acceleration error per 0.1 s, Achilles only, with the float32 precision line.
usage: make_accel_chart.py dp_results.json out.svg"""
import json, sys
from svgchart import Chart, pow10
r = json.load(open(sys.argv[1]))
n = sum(1 for v in r["t_win"] if v <= 10 + 1e-6)
t, e = r["t_win"][:n], r["qdd_rel_vs_closed"][:n]
c = Chart("Joint-acceleration error against the closed-form solution",
          "Worst relative error of Achilles' joint accelerations in each tenth of a second over a 10 second double-pendulum run, "
          "compared with the closed-form Lagrangian equations of motion. It stays between about 2e-7 and 3e-6, just above float32 precision, "
          "with no growth over time.", h=340, mt=48)
c.xscale(0, 10); c.yscale(1e-9, 1e-4, log=True)
c.axes([0, 2, 4, 6, 8, 10], [1e-9, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4], "simulated time (s)", "worst relative error per 0.1 s (log scale)",
       xfmt=lambda v: f"{v:g}", yfmt=pow10)
c.hguide(1.19e-7, "float32 precision", below=True)
c.line(t, e, "--s1", width=2)
open(sys.argv[2], "w").write(c.svg())
