"""When each domino of the amplifier tipped past 45 degrees, Achilles vs MuJoCo.
usage: make_domino_chart.py achilles.csv mujoco.csv scene.arow out.svg"""
import sys, yaml
import numpy as np
from svgchart import Chart
from dom_analyze import load, tilt
def fall_times(path):
    t, P = load(path); ang = tilt(P[:, 1:, 4:8])
    return [float(t[np.nonzero(ang[:, i] > 45)[0][0]]) for i in range(ang.shape[1])]
a, m = fall_times(sys.argv[1]), fall_times(sys.argv[2])
masses = [j["fields"]["rigid_body_inertia"][0] for j in yaml.safe_load(open(sys.argv[3]))["joints"] if j["fields"]["joint_activation_mask"] == [63]]
n = len(a); idx = list(range(1, n + 1))
gap = max(abs(x - y) for x, y in zip(a, m))
print("achilles", a); print("mujoco", m); print("max gap", gap, "masses", masses[0], masses[-1])
c = Chart("Domino amplifier: when each domino tipped, Achilles and MuJoCo",
          f"Time at which each of the ten dominoes tipped past 45 degrees, simulated by Achilles and by MuJoCo 3.15 from the same scene. "
          f"Each domino is 1.2 times the size of the one before, so the last weighs {masses[-1] / masses[0]:.0f} times the first. "
          f"The two engines agree to within {gap * 1000:.0f} milliseconds on every domino; the last one falls at {a[-1]:.2f} s in Achilles and {m[-1]:.2f} s in MuJoCo.",
          h=340, mt=60, mb=66)
c.xscale(0.5, n + 0.5); c.yscale(0, 5.5)
c.axes(idx, [0, 1, 2, 3, 4, 5], "domino (each 1.2× the last)", "time it tipped past 45° (s)",
       xfmt=lambda v: str(v), yfmt=lambda v: f"{v:g}")
c.label(c.X(1), c.h - 30, f"{masses[0]:.1f} kg", anchor="middle", cls="s m")
c.label(c.X(n), c.h - 30, f"{masses[-1]:.0f} kg", anchor="middle", cls="s m")
c.line(idx, a, "--s1", width=2)
for i, (x, y) in enumerate(zip(a, m), 1):
    c.body.append(f'<circle cx="{c.X(i):.1f}" cy="{c.Y(y):.1f}" r="6.5" fill="none" style="stroke:var(--s2)" stroke-width="2"/>')
    c.body.append(f'<circle cx="{c.X(i):.1f}" cy="{c.Y(x):.1f}" r="3.5" style="fill:var(--s1)"/>')
c.legend([("Achilles", "--s1", False), ("MuJoCo 3.15 (ring)", "--s2", False)])
open(sys.argv[4], "w").write(c.svg())
