"""The reworked SKIDADDLE follower (Dec 2025 – Jan 2026, EricJGoossen/SKIDADDLE @4b3fdb9) as a
diagram: what is computed once per path, and what runs every loop.

usage: make_skidaddle_diagram.py <images dir>
"""
import os
import sys
from html import escape

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../achilles/generated/scripts"))
from svgchart import STYLE  # noqa: E402

out = sys.argv[1]
b = ['<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
     '<path d="M0,0 L10,5 L0,10 z" style="fill:var(--axis)"/></marker></defs>']


def box(x, y, bw, bh, title, lines, var):
    b.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="8" style="fill:var({var});stroke:var({var})" '
             f'fill-opacity="0.1" stroke-opacity="0.7" stroke-width="1.3"/>')
    b.append(f'<text class="b" x="{x + 12}" y="{y + 21}">{escape(title)}</text>')
    for i, line in enumerate(lines):
        b.append(f'<text class="s m" x="{x + 12}" y="{y + 40 + 16 * i}">{escape(line)}</text>')


def arrow(x1, y1, x2, y2):
    b.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke:var(--axis)" stroke-width="1.6" marker-end="url(#a)"/>')


def label(x, y, text):
    b.append(f'<text class="s m b" x="{x}" y="{y}" letter-spacing="0.06em">{escape(text.upper())}</text>')


label(16, 24, "Once per path")
box(16, 36, 210, 86, "Path generator", ["Bézier or Hermite curve,", "flattened into straight arcs", "(De Casteljau subdivision)"], "--ref")
box(260, 36, 444, 86, "Speed limits, precomputed", ["one backward pass over every vertex: the fastest speed", "the robot can enter each turn at and still slow down in", "time for the rest of the path"], "--s1")
arrow(226, 79, 258, 79)
label(16, 160, "Every loop")
box(16, 172, 210, 134, "Controllers", ["each asks for an acceleration,", "with a weight and a priority:", "· along the path (convergent)", "· back onto it (transverse)", "· heading"], "--s4")
box(260, 172, 220, 134, "Scheduler", ["runs the controllers that", "are active and collects", "their requests; with none", "running, a default", "controller stops the robot"], "--s5")
box(514, 172, 190, 134, "Allocator", ["turns requests into motor", "space and hands out each", "motor's headroom, highest", "priority first, shared", "by weight"], "--s3")
arrow(226, 239, 258, 239)
arrow(480, 239, 512, 239)
arrow(370, 122, 370, 170)
b.append('<text class="s m" x="378" y="150">the current arc and its speed limit</text>')
box(514, 340, 190, 70, "Wheels", ["each motor kept within its", "speed and acceleration caps"], "--s2")
arrow(609, 306, 609, 338)
b.append('<text class="s m" x="16" y="364">Before the rework, one class did all of this, and</text>')
b.append('<text class="s m" x="16" y="380">re-ran the look-ahead at every change of segment.</text>')

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 424" role="img" aria-labelledby="t d">\n'
       f'  <title id="t">The reworked SKIDADDLE follower</title>\n'
       f'  <desc id="d">{escape("Once per path, the path generator flattens a Bézier or Hermite curve into straight arcs and one backward pass precomputes the fastest speed the robot can enter each turn at. Every loop, controllers for progress along the path, for getting back onto it and for heading each request an acceleration with a weight and a priority; the scheduler collects the requests, and the allocator converts them to motor space and hands out each motor’s headroom, highest priority first, shared by weight, before the result goes to the wheels.")}</desc>\n'
       + STYLE + "  " + "\n  ".join(b) + "\n</svg>\n")
open(f"{out}/skidaddle-pipeline.svg", "w").write(svg)
print("wrote skidaddle-pipeline.svg")
