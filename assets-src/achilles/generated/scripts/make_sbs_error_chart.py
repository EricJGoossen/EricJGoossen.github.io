"""Achilles vs MuJoCo, same double pendulum (RK4, 2 ms): outer-link separation over the 8 s of the side-by-side clip, in mm.
usage: make_sbs_error_chart.py dp_results.json out.svg"""
import json, sys
from svgchart import Chart, pow10
r = json.load(open(sys.argv[1]))
reach_mm = r["reach"] * 1000
pts = [(t, e / 100 * reach_mm) for t, e in zip(r["t"], r["tip_err_achilles_rk4_vs_mujoco_rk4"]) if 0 < t <= 8.0 + 1e-9]
t, mm = zip(*pts)
at = lambda s: max(m for tt, m in pts if tt <= s + 1e-9)
print({s: round(at(s), 6) for s in (1, 2, 4, 6, 7, 8)})
c = Chart("Distance between the Achilles and MuJoCo pendulums",
          f"Distance between the outer link's position in Achilles and in MuJoCo over the 8 seconds of the side-by-side clip, on a log scale in millimetres. "
          f"It stays below {at(4):.2f} mm for the first 4 seconds and below 1 mm for 6 seconds, then grows to about {at(8):.0f} mm by 8 seconds, about 1% of the arm's reach, as the chaotic swing amplifies single-precision rounding.",
          h=320, mt=48)
c.xscale(0, 8); c.yscale(1e-5, 100, log=True)
c.axes([0, 2, 4, 6, 8], [1e-5, 1e-3, 1e-1, 10], "simulated time (s)", "distance between the two outer links (mm, log scale)",
       xfmt=lambda v: f"{v:g}", yfmt=lambda v: {10: "10"}.get(v) or pow10(v))
c.hguide(1, "")
c.label(c.X(0.15), c.Y(1) - 6, "1 mm", cls="s m")
c.line(t, mm, "--s1", width=2)
open(sys.argv[2], "w").write(c.svg())
