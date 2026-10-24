"""The Odin1 error model's hold-out check (Eric's report, Table 4), in the site's chart style:
for each axis, the real RMSE on the held-out session against the model's simulated 5-95% band
(200 Monte Carlo runs along the session's real trajectory).

usage: make_holdout_chart.py <out.svg>
"""
import os
import sys
from html import escape

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../achilles/generated/scripts"))
from svgchart import STYLE, Chart  # noqa: E402

# axis, real RMSE, simulated 5%, 95%  (Odin1 Error Characterization, Table 4)
POS = [("along-track", 3.40, 0.83, 3.54), ("cross-track", 3.85, 0.86, 8.93), ("vertical", 0.59, 0.55, 4.83)]
ROT = [("roll", 0.25, 0.32, 1.27), ("pitch", 0.45, 0.26, 1.61), ("yaw", 0.33, 0.22, 0.99)]


def panel(rows, hi, ticks, unit, title):
    c = Chart("", "", w=680, h=190, ml=110, mr=24, mt=40, mb=40)
    c.xscale(0, hi)
    c.yscale(0, len(rows))
    b = c.body
    for v in ticks:
        x = c.X(v)
        b.append(f'<line class="grid" x1="{x:.1f}" x2="{x:.1f}" y1="{c.mt}" y2="{c.h - c.mb}"/>')
        b.append(f'<text class="s m c" x="{x:.1f}" y="{c.h - c.mb + 18}">{v:g}</text>')
    b.append(f'<text class="s m c" x="{(c.ml + c.w - c.mr) / 2:.0f}" y="{c.h - 6}">{escape(unit)}</text>')
    b.append(f'<text class="b" x="{c.ml - 100}" y="{c.mt - 18}">{escape(title)}</text>')
    for i, (name, real, lo, hi_) in enumerate(rows):
        y = c.Y(len(rows) - i - 0.5)
        b.append(f'<text class="s e" x="{c.ml - 10}" y="{y + 4:.1f}">{escape(name)}</text>')
        b.append(f'<rect x="{c.X(lo):.1f}" y="{y - 7:.1f}" width="{c.X(hi_) - c.X(lo):.1f}" height="14" rx="3" '
                 'style="fill:var(--s1)" fill-opacity="0.22"/>')
        b.append(f'<circle cx="{c.X(real):.1f}" cy="{y:.1f}" r="5.5" style="fill:var(--s2)"/>')
        b.append(f'<text class="s" x="{c.X(real) + 9:.1f}" y="{y - 9:.1f}">{real:g}</text>')
    return b


top = panel(POS, 10, [0, 2, 4, 6, 8, 10], "RMSE (cm)", "Position")
bot = panel(ROT, 2, [0, 0.5, 1, 1.5, 2], "RMSE (degrees)", "Rotation")
title = "The error model's hold-out check: every axis passes"
desc = ("For each axis, the Odin1's real RMSE on a held-out 40 s session (dot) against the range the error model "
        "predicts for that session (bar: 5th to 95th percentile of 200 simulated runs along the same trajectory). "
        "Position: along-track 3.40 cm (predicted 0.83-3.54), cross-track 3.85 cm (0.86-8.93), vertical 0.59 cm "
        "(0.55-4.83). Rotation: roll 0.25 degrees (0.32-1.27), pitch 0.45 (0.26-1.61), yaw 0.33 (0.22-0.99). "
        "Every axis passes the rank test (family-wise alpha 0.10); roll sits just under its band.")
legend = ('<rect x="110" y="12" width="22" height="12" rx="3" style="fill:var(--s1)" fill-opacity="0.22"/>'
          '<text class="s" x="138" y="22">predicted 5-95%</text>'
          '<circle cx="268" cy="18" r="5.5" style="fill:var(--s2)"/><text class="s" x="280" y="22">real</text>')
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 420" role="img" aria-labelledby="t d">\n'
       f'  <title id="t">{escape(title)}</title>\n  <desc id="d">{escape(desc)}</desc>\n' + STYLE +
       "  " + legend + "\n  <g transform=\"translate(0,30)\">" + "\n  ".join(top) + "</g>\n"
       "  <g transform=\"translate(0,225)\">" + "\n  ".join(bot) + "</g>\n</svg>\n")
open(sys.argv[1], "w").write(svg)
