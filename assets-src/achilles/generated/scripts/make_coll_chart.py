import json, sys
sys.path.insert(0, sys.argv[1] + "/tools")
from svgchart import Chart
SP = sys.argv[1]
R = [r for r in json.load(open(f"{SP}/coll/results.json")) if r["ach"]]
xs = [r["d_true"] for r in R]
lo, hi = min(xs), max(xs)
print(len(R), lo, hi, min(r["d_mj"] for r in R))
off = [r for r in R if abs(r["d_mj"] - r["d_true"]) > 1e-4]
c = Chart("Contact distance against the exact answer, Achilles and MuJoCo",
          f"Each dot is one random pair of shapes (sphere, capsule or box, all six combinations, {len(R)} pairs), from 0.35 overlapping to 0.3 apart. "
          "Horizontal: exact signed distance between the two surfaces, computed independently. Vertical: the distance each engine reports. "
          "Every Achilles dot lies on the diagonal (largest error 5e-5). MuJoCo matches for sphere and capsule pairs but is off the diagonal "
          f"for {len(off)} pairs involving boxes: separated box pairs and deeply overlapping capsule-box pairs.", h=440, mt=70, ml=70)
c.xscale(-0.4, 0.35); c.yscale(-0.4, 0.35)
ticks = [-0.4, -0.2, 0, 0.2]
c.axes(ticks, ticks, "exact signed distance (negative = overlapping)", "distance the engine reports",
       xfmt=lambda v: f"{v:g}".replace("-", "−"), yfmt=lambda v: f"{v:g}".replace("-", "−"))
c.body.append(f'<line class="guide" x1="{c.X(-0.4):.1f}" y1="{c.Y(-0.4):.1f}" x2="{c.X(0.35):.1f}" y2="{c.Y(0.35):.1f}"/>')
for r in R:
    c.body.append(f'<circle cx="{c.X(r["d_true"]):.1f}" cy="{c.Y(r["d_mj"]):.1f}" r="4" fill="none" style="stroke:var(--s2)" stroke-width="1.5"/>')
for r in R:
    c.body.append(f'<circle cx="{c.X(r["d_true"]):.1f}" cy="{c.Y(r["ach"]["dist"]):.1f}" r="2.2" style="fill:var(--s1)"/>')
c.label(c.X(0.08), c.Y(-0.03), "reported = exact", cls="s m")
c.label(c.X(-0.38), c.Y(0.04), f"MuJoCo off the line: {len(off)} box pairs", cls="s b")
c.legend([("Achilles", "--s1", False), ("MuJoCo 3.15 (ring)", "--s2", False)])
open(f"{SP}/charts/collision-vs-exact.svg", "w").write(c.svg())
