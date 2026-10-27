"""Draws skidaddle-hairpin.svg: SKIDADDLE, Road Runner and Pedro Pathing on one simulated robot around a hairpin.

Reads the traces in data/ (written by harness/Compare.java, every third 10 ms step kept).
Usage: python3 make_hairpin_compare.py data ../../../src/projects/ftc/images/skidaddle-hairpin.svg
"""
import csv, math, sys

data, out = sys.argv[1], sys.argv[2]
CP = [(-48, -36), (72, -36), (72, 36), (-48, 36)]           # the hairpin, a cubic Bezier


def bez(t):
    a, b, c, d = CP
    u = 1 - t
    return tuple(u**3 * a[i] + 3 * u * u * t * b[i] + 3 * u * t * t * c[i] + t**3 * d[i] for i in (0, 1))


path = [bez(i / 999) for i in range(1000)]


def load(name):
    rows = [[float(v) for v in r.values()] for r in csv.DictReader(open(f"{data}/hairpin-{name}.csv"))]
    stop = max((r[0] for r in rows if math.hypot(r[3], r[4]) >= 2), default=0)
    dev = max(min(math.hypot(r[1] - p[0], r[2] - p[1]) for p in path[::2]) for r in rows)
    end = math.hypot(rows[-1][1] - CP[3][0], rows[-1][2] - CP[3][1])
    return rows, stop, dev, end


# (file, label, colour, dashed): Road Runner twice, at the shared limit and with the margin it needs
series = [("road-runner", "Road Runner, 50 in/s² limit", "--s2", True),
          ("road-runner-accel30", "Road Runner, 30 in/s² limit", "--s2", False),
          ("pedro-pathing", "Pedro Pathing", "--s3", False),
          ("skidaddle", "SKIDADDLE", "--s1", False)]
runs = {f: load(f) for f, *_ in series}

W, H = 600, 486
S = 3.9                                                     # px per inch
X0, Y0 = -76, 44                                            # field point at the plot's top left
ox, oy = 28, 132
px = lambda x: ox + (x - X0) * S
py = lambda y: oy + (Y0 - y) * S

desc = ["Four runs around the same hairpin on one simulated mecanum robot, all starting from rest."]
for f, label, _, _ in series:
    _, stop, dev, end = runs[f]
    desc.append(f"{label}: stopped after {stop:.1f} s, {dev:.1f} inches off the path at worst, {end:.1f} inches from the end.")
over = CP[3][0] - min(r[1] for r in runs["road-runner"][0])
desc.append(f"Road Runner at the 50 limit falls behind in the curve and overshoots the end by about {over:.0f} inches before coming back.")

svg = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
  <title id="t">SKIDADDLE, Road Runner and Pedro Pathing around a hairpin</title>
  <desc id="d">{" ".join(desc)}</desc>
  <style>
    svg {{ --text:#1c1917; --muted:#6b6560; --grid:#e7e5e4; --axis:#a8a29e; --surface:#fcfcfb;
          --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a; --ref:#78716c; }}
    @media screen {{
      svg {{ --text:#f2f1ef; --muted:#a39d97; --grid:#33312e; --axis:#57534e; --surface:#1c1b1a;
            --s1:#3987e5; --s2:#d95926; --s3:#199e70; --ref:#a8a29e; }}
    }}
    text {{ font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; fill: var(--text); font-size: 13px; }}
    .m {{ fill: var(--muted); }} .s {{ font-size: 12px; }} .b {{ font-weight: 650; }}
    .e {{ text-anchor: end; }} .c {{ text-anchor: middle; }}
    .grid {{ stroke: var(--grid); stroke-width: 1; }}
    .ln {{ fill: none; stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }}
    .dash {{ stroke-dasharray: 6 4; }}
    .ref {{ fill: none; stroke: var(--ref); stroke-width: 1.5; stroke-dasharray: 2 4; stroke-linecap: round; }}
  </style>''']

# legend: one row per run, with its numbers in text ink
svg.append('  <text class="s m" x="250" y="18">stopped</text><text class="s m" x="318" y="18">worst off path</text><text class="s m" x="420" y="18">from the end point</text>')
for k, (f, label, col, dashed) in enumerate(series):
    y = 40 + 22 * k
    _, stop, dev, end = runs[f]
    svg.append(f'  <line class="ln{" dash" if dashed else ""}" x1="28" x2="56" y1="{y - 4}" y2="{y - 4}" style="stroke:var({col})"/>')
    svg.append(f'  <text x="64" y="{y}"{" class=\"b\"" if f == "skidaddle" else ""}>{label}</text>')
    svg.append(f'  <text x="250" y="{y}">{stop:.1f} s</text><text x="318" y="{y}">{dev:.1f} in</text><text x="420" y="{y}">{end:.1f} in</text>')

# a 24 in grid (one field tile)
for gx in range(-72, 49, 24):
    svg.append(f'  <line class="grid" x1="{px(gx):.1f}" x2="{px(gx):.1f}" y1="{py(Y0):.1f}" y2="{py(-44):.1f}"/>')
for gy in range(-36, 37, 24):
    svg.append(f'  <line class="grid" x1="{px(X0):.1f}" x2="{px(52):.1f}" y1="{py(gy):.1f}" y2="{py(gy):.1f}"/>')

pts = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in path[::10] + [path[-1]])
svg.append(f'  <polyline class="ref" points="{pts}"/>')
for f, label, col, dashed in series:                         # SKIDADDLE drawn last, on top
    rows = runs[f][0]
    pts = " ".join(f"{px(r[1]):.1f},{py(r[2]):.1f}" for r in rows[::2])
    svg.append(f'  <polyline class="ln{" dash" if dashed else ""}" points="{pts}" style="stroke:var({col})"/>')

sx, sy = px(CP[0][0]), py(CP[0][1])
ex, ey = px(CP[3][0]), py(CP[3][1])
svg.append(f'  <circle cx="{sx:.1f}" cy="{sy:.1f}" r="4.5" style="fill:var(--text);stroke:var(--surface);stroke-width:2"/>')
svg.append(f'  <text class="s" x="{sx + 10:.1f}" y="{sy + 18:.1f}">start →</text>')
svg.append(f'  <circle cx="{ex:.1f}" cy="{ey:.1f}" r="4.5" style="fill:none;stroke:var(--text);stroke-width:2"/>')
svg.append(f'  <text class="s" x="{ex + 10:.1f}" y="{ey + 18:.1f}">← end</text>')
svg.append(f'  <text class="s m e" x="{px(-51):.1f}" y="{py(CP[3][1]) - 10:.1f}">overshoots {over:.0f} in</text>')
svg.append(f'  <text class="s m" x="{px(-30):.1f}" y="{py(0) + 4:.1f}">dotted: the path · grid: 24 in tiles</text>')
svg.append('</svg>')
open(out, "w").write("\n".join(svg) + "\n")
print(out, "written")
