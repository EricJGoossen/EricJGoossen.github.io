import sys, math, re
sys.path.insert(0, sys.argv[1] + "/tools")
from svgchart import Chart, pow10
SP, SUM = sys.argv[1], sys.argv[2]

# parse throughput_summary.md
tables, cur = {}, None
for line in open(SUM):
    m = re.match(r"### (\S+) / (\S+)", line)
    if m: cur = tables.setdefault((m[1], m[2]), []); continue
    if cur is not None and re.match(r"\| \d", line):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        num = lambda s: None if s == "n/a" else float(s.replace(",", "").rstrip("x"))
        cur.append([num(c) for c in cells])
# columns: N, f32 AVX2, f64 AVX2, f32 SSE2, mj merged, mj rollout, speedup f32, speedup f64

# --- Chart 1: speed relative to MuJoCo, V2 vs V3 ---
v2 = {1: 0.39 / 0.35, 2: 0.50 / 0.62, 4: 0.93 / 1.31, 8: 1.26 / 2.65}
v3_single, v3_batch = {}, {}
for scene, links in (("two_joint_arm", 2), ("three_joint_arm", 3), ("seven_joint_arm", 7)):
    rows = {int(r[0]): r for r in tables[(scene, "euler")]}
    v3_single[links] = rows[1][6]
    v3_batch[links] = rows[64][6]
# 1 link: no V3 laptop run, so the cloud ratios from data/speed_vs_mujoco_cloud.json
import json, os
cloud = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "speed_vs_mujoco_cloud.json")))
for r in cloud["rows"]:
    if r["links"] == 1:
        (v3_single if r["robots"] == 1 else v3_batch)[1] = r["speedup"]
print("v2", v2, "v3 single", v3_single, "v3 N=64", v3_batch)
c = Chart("Achilles V2 and V3 speed relative to MuJoCo",
          "Simulation speed as a multiple of single-threaded MuJoCo on the same machine, by number of links in the arm. "
          "V2, one robot at a time: 1.1 times MuJoCo's speed at one link, falling to 0.8 at two links and 0.48 at eight. "
          "V3 with one robot: 2.8 times at one link, 2.1 at two, 1.6 at three, 0.97 at seven. "
          "V3 with 64 robots batched across SIMD lanes: 2.7, 2.6, 3.0 and 3.3 times at one, two, three and seven links.", h=400, mt=70)
c.xscale(1, 8, log=True); c.yscale(0, 3.5)
c.axes([1, 2, 3, 4, 7, 8], [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5], "links in the arm (log scale)", "speed relative to MuJoCo (× faster)",
       xfmt=lambda v: f"{v:g}", yfmt=lambda v: f"{v:g}×")
c.hguide(1, "")
c.label(c.X(2.15), c.Y(1) - 7, "MuJoCo (1×)", cls="s m")
def series(d, var, dash=False):
    xs = sorted(d); c.line(xs, [d[x] for x in xs], var, dash=dash)
    for x in xs:
        c.body.append(f'<circle cx="{c.X(x):.1f}" cy="{c.Y(d[x]):.1f}" r="4.5" style="fill:var({var})" stroke="var(--surface, #fff)" stroke-width="0"/>')
series(v2, "--s2"); series(v3_single, "--s3"); series(v3_batch, "--s1")
c.legend([("V2, 1 robot", "--s2", False), ("V3, 1 robot", "--s3", False), ("V3, 64 robots batched", "--s1", False)])
# direct labels at the right end of each line
c.label(c.X(8) - 6, c.Y(v2[8]) + 20, "V2", anchor="end", cls="s b")
c.label(c.X(7) + 8, c.Y(v3_single[7]) - 8, "V3 ×1", anchor="start", cls="s b")
c.label(c.X(7) + 8, c.Y(v3_batch[7]) + 4, "V3 ×64", anchor="start", cls="s b")
open(f"{SP}/charts/speed-vs-mujoco.svg", "w").write(c.svg())

# --- Chart 2: throughput vs batch size, seven-joint arm, euler ---
rows = tables[("seven_joint_arm", "euler")]
N = [r[0] for r in rows]
f32 = [r[1] for r in rows]; f64 = [r[2] for r in rows]
mj = [max(x for x in (r[4], r[5]) if x) for r in rows]
c = Chart("Seven-link arm throughput: Achilles vs MuJoCo",
          "Robot-steps per second on one laptop CPU core, by number of robots simulated at once, for a seven-link arm at a 2 ms step. "
          "Achilles in single precision (AVX2, eight lanes) rises from 0.75 million at one robot to 5.4 million at 64. "
          "Achilles in double precision peaks at 2.7 million. MuJoCo's best mode stays between 0.78 and 1.7 million.", h=400, mt=70)
c.xscale(1, 4096, log=True); c.yscale(0, 6e6)
c.axes([1, 4, 16, 64, 256, 1024, 4096], [0, 1e6, 2e6, 3e6, 4e6, 5e6, 6e6], "robots simulated at once (log scale)", "robot-steps per second",
       xfmt=lambda v: f"{int(v):,}", yfmt=lambda v: "0" if v == 0 else f"{v/1e6:g}M")
c.line(N, mj, "--ref", width=2)
c.line(N, f64, "--s3", width=2)
c.line(N, f32, "--s1", width=2.5)
for x, y, var in [(n, v, "--s1") for n, v in zip(N, f32)]:
    c.body.append(f'<circle cx="{c.X(x):.1f}" cy="{c.Y(y):.1f}" r="3.5" style="fill:var({var})"/>')
i64 = N.index(64)
c.label(c.X(64), c.Y(f32[i64]) - 12, "5.4M, 3.3× MuJoCo", anchor="middle", cls="s b")
c.legend([("Achilles, float (AVX2)", "--s1", False), ("Achilles, double (AVX2)", "--s3", False), ("MuJoCo 3.15, best mode", "--ref", False)])
open(f"{SP}/charts/throughput-seven-link.svg", "w").write(c.svg())
