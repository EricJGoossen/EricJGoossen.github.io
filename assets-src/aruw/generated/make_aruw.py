"""Graphics for the ARUW log from EricJGoossen/odin-characterization: the campaign's
course (from config/campaign.yaml, drawn with the repo's own path functions), the
day-1 schedule (scripts/estimate_time.py's numbers), and the system diagram (README).

usage: make_aruw.py <odin-characterization checkout> <images dir>
"""
import os
import sys
from html import escape

import numpy as np
import yaml

repo, out = sys.argv[1], sys.argv[2]
sys.path.insert(0, repo)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../achilles/generated/scripts"))
from odin_char.robot import motion  # noqa: E402
from svgchart import STYLE, Chart  # noqa: E402

cfg = yaml.safe_load(open(f"{repo}/config/campaign.yaml"))
room, ph = cfg["room"], cfg["phases"]


def svg(w, h, title, desc, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">\n'
            f'  <title id="t">{escape(title)}</title>\n  <desc id="d">{escape(desc)}</desc>\n'
            + STYLE + "  " + "\n  ".join(body) + "\n</svg>\n")


# --- The course --------------------------------------------------------------------
lo, hi, margin = np.array(room["fence_min"]), np.array(room["fence_max"]), room["margin"]
p2 = ph["phase2"]
f8 = motion.figure8_path(p2["center"], p2["half_length"], p2["half_width"], np.deg2rad(p2["rotation_deg"]), 1)
lanes = motion.lawnmower_path(lo + margin, hi - margin, ph["mapping"]["lane_spacing"], ph["mapping"]["loops"])
c = Chart("The characterization course",
          "Top-down plan of the campaign in the mocap frame: an 8 by 6 meter geofence with a 0.4 meter margin, "
          "the mapping drive's lanes 1 meter apart, the 6 by 3.6 meter figure-8 the sentry laps at 0.8 m/s, "
          "and four 10-minute hold spots, each facing a different way.",
          w=680, h=560, ml=48, mr=24, mt=56, mb=48)
c.xscale(-4.3, 4.3)
c.yscale(-3.3, 3.3)
c.axes([-4, -2, 0, 2, 4], [-3, -2, -1, 0, 1, 2, 3], "x (m)", "y (m)", xfmt=lambda v: f"{v:g}", yfmt=lambda v: f"{v:g}")
for v in [-4, -2, 0, 2, 4]:
    c.body.insert(0, f'<line class="grid" x1="{c.X(v):.1f}" x2="{c.X(v):.1f}" y1="{c.mt}" y2="{c.h - c.mb}"/>')


def rect(a, b, style):
    c.body.append(f'<rect x="{c.X(a[0]):.1f}" y="{c.Y(b[1]):.1f}" width="{c.X(b[0]) - c.X(a[0]):.1f}" '
                  f'height="{c.Y(a[1]) - c.Y(b[1]):.1f}" style="{style}"/>')


rect(lo, hi, "fill:none;stroke:#dc2626;stroke-width:1.6")
rect(lo + margin, hi - margin, "fill:none;stroke:#dc2626;stroke-width:1;stroke-dasharray:4 4;stroke-opacity:0.6")
c.line(lanes[:, 0], lanes[:, 1], "--ref", width=1.2, opacity=0.55)
c.line(f8[:, 0], f8[:, 1], "--s1", width=3)
for x, y, yaw in ph["phase3"]["locations"]:
    c.body.append(f'<circle cx="{c.X(x):.1f}" cy="{c.Y(y):.1f}" r="7" style="fill:var(--s2)"/>')
    c.body.append(f'<line x1="{c.X(x):.1f}" y1="{c.Y(y):.1f}" x2="{c.X(x + 0.5 * np.cos(yaw)):.1f}" '
                  f'y2="{c.Y(y + 0.5 * np.sin(yaw)):.1f}" style="stroke:var(--s2)" stroke-width="2.5"/>')
hx, hy, _ = room["home"]
c.body.append(f'<rect x="{c.X(hx) - 6:.1f}" y="{c.Y(hy) - 6:.1f}" width="12" height="12" style="fill:var(--text)"/>')
c.legend([("figure-8 laps", "--s1", False), ("mapping lanes", "--ref", False)])
c.body.append(f'<circle cx="{c.ml + 330}" cy="{18}" r="6" style="fill:var(--s2)"/><text class="s" x="{c.ml + 342}" y="22">hold spots</text>')
c.body.append(f'<line x1="{c.ml + 440}" x2="{c.ml + 460}" y1="18" y2="18" stroke="#dc2626" stroke-width="2"/><text class="s" x="{c.ml + 466}" y="22">geofence</text>')
open(f"{out}/odin-course.svg", "w").write(c.svg())

# --- Day 1, step by step (scripts/estimate_time.py) ----------------------------------
STEPS = [("check", 0.7, "identify command gains"), ("preflight", 8.4, "mocap and Odin power-cycled"),
         ("calib", 2.6, "spins and swerves"), ("map", 4.6, "77 m of lanes and loops"),
         ("session", 5.9, "figure-8 laps"), ("holds", 41.0, "4 spots, 10 min each"),
         ("latency", 2.7, "back-and-forth, then rotation"), ("init", 16.0, "24 cold starts"),
         ("outage", 10.8, "15 covered trials")]
total = sum(m for _, m, _ in STEPS)
ml, mt, rh, w = 96, 40, 30, 680
pw = w - ml - 150
h = mt + rh * len(STEPS) + 46
b, t0 = [], 0.0
for i, (name, mins, note) in enumerate(STEPS):
    y = mt + rh * i
    x = ml + pw * t0 / total
    bw = max(pw * mins / total, 3)
    b.append(f'<text class="s e" x="{ml - 10}" y="{y + rh / 2 + 4:.0f}">{escape(name)}</text>')
    b.append(f'<rect x="{x:.1f}" y="{y + 5}" width="{bw:.1f}" height="{rh - 10}" rx="3" style="fill:var(--s1)" fill-opacity="0.8"/>')
    b.append(f'<text class="s m" x="{x + bw + 8:.1f}" y="{y + rh / 2 + 4:.0f}">{mins:g} min · {escape(note)}</text>')
    t0 += mins
b.append(f'<line class="axis" x1="{ml}" x2="{ml + pw}" y1="{h - 34}" y2="{h - 34}"/>')
for v in range(0, 100, 15):
    if v <= total:
        b.append(f'<text class="s m c" x="{ml + pw * v / total:.0f}" y="{h - 16}">{v}</text>')
b.append(f'<text class="s m" x="{ml + pw + 10}" y="{h - 16}">minutes (day 1: {total:.0f})</text>')
open(f"{out}/odin-day1.svg", "w").write(svg(w, h, "Day 1 of the campaign",
    f"The nine steps of the first collection day as the campaign's own time estimate gives them, {total:.0f} minutes in "
    "all. Holding still at four spots for 10 minutes each is the longest step at 41 minutes, then 24 cold starts at "
    "16 minutes and 15 covered-sensor outages at 11.", b))

# --- The system ---------------------------------------------------------------------
b = ['<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
     '<path d="M0,0 L10,5 L0,10 z" style="fill:var(--axis)"/></marker></defs>']


def box(x, y, bw, bh, title, lines, var):
    b.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="8" style="fill:var({var});stroke:var({var})" '
             f'fill-opacity="0.1" stroke-opacity="0.7" stroke-width="1.3"/>')
    b.append(f'<text class="b" x="{x + 12}" y="{y + 21}">{escape(title)}</text>')
    for i, line in enumerate(lines):
        b.append(f'<text class="s m" x="{x + 12}" y="{y + 40 + 16 * i}">{escape(line)}</text>')


def arrow(x1, y1, x2, y2, label="", lx=0, ly=0, anchor="middle"):
    b.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke:var(--axis)" stroke-width="1.6" marker-end="url(#a)"/>')
    if label:
        b.append(f'<text class="s m" x="{lx}" y="{ly}" text-anchor="{anchor}">{escape(label)}</text>')


box(16, 16, 200, 70, "Motion capture", ["the room's cameras: ground", "truth, about 360 Hz"], "--ref")
box(250, 16, 220, 102, "odin-characterization", ["guides the driver or drives itself,", "starts and stops Odin, records", "every run, then fits the", "error model"], "--s1")
box(504, 16, 200, 70, "Odin1", ["the lidar-inertial sensor", "under test, on the turret"], "--s4")
arrow(216, 51, 248, 51)
arrow(504, 51, 472, 51)
box(250, 168, 220, 70, "project-otto (Jetson)", ["UDP → UART bridge, 100 Hz,", "zeros if the script goes quiet"], "--s5")
arrow(360, 118, 360, 166, "chassis velocity, UDP", 368, 146, "start")
box(250, 290, 220, 86, "aruw-mcb (sentry MCB)", ["velocity command with a 150 ms", "watchdog and speed caps; holds", "the turret at a fixed yaw"], "--s3")
arrow(360, 238, 360, 288, "UART message 0x14", 368, 268, "start")
box(504, 168, 200, 86, "results/report.md", ["static field, Gauss-Markov", "drift, latency, start-up and", "dropout events"], "--s2")
arrow(470, 100, 560, 166)
box(16, 168, 200, 86, "Human mode (default)", ["a person drives with the", "remote; the script shows", "live mocap feedback"], "--ref")
b.append('<text class="s m" x="16" y="404">Autonomous mode drives through otto and the MCB; human mode sends nothing to the robot.</text>')
open(f"{out}/odin-system.svg", "w").write(svg(720, 416, "The characterization system",
    "Motion capture and the Odin1 sensor feed the odin-characterization scripts, which record every run and fit the "
    "error model into a report. In autonomous mode the scripts send chassis velocities over UDP to project-otto on "
    "the Jetson, which forwards them over UART to the sentry's MCB; in the default human mode a person drives with "
    "the remote and the script only guides.", b))
print("wrote", total)
