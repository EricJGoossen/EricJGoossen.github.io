"""Draws two-robot-plan.svg: the two-robot schedule Eric set up as 417 SKID's captain (from his Oct 25 notes)."""
import sys

out = sys.argv[1]
W, H, x0, x1 = 720, 290, 130, 706
ys, ym = 86, 176                                       # software and mechanical rows
software = ["Robot A: drive train", "Robot B: + lift", "Robot A: + arm"]
mechanical = ["Robot B: builds the lift", "Robot A: builds the arm", "Robot B: next feature"]
trades = ["lift done", "arm done"]
pre = 0.17 * (x1 - x0)
step = (x1 - x0 - pre) / 3
svg = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
  <title id="t">Two robots, traded at each definition of done</title>
  <desc id="d">A timeline in two rows, software and mechanical. While the CAD is finished, the drive trains are built. Then software tests on robot A, a bare drive train, while mechanical builds the lift on robot B. When the lift passes the definition of done the teams trade robots: software takes robot B with the lift, and mechanical builds the arm on robot A. At the next definition of done they trade again, and so on through the season.</desc>
  <defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="var(--text)"/></marker></defs>
  <style>
    svg {{ --text:#1c1917; --muted:#6b6560; --sw:#1d5fae; --me:#b8461c; --pre:#e7e5e4; }}
    @media (prefers-color-scheme: dark) {{
      svg {{ --text:#f2f1ef; --muted:#a39d97; --sw:#1d5fae; --me:#a8401a; --pre:#33312e; }}
    }}
    text {{ font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; fill: var(--text); font-size: 13px; }}
    .m {{ fill: var(--muted); }} .s {{ font-size: 12px; }} .b {{ font-weight: 650; }} .c {{ text-anchor: middle; }} .e {{ text-anchor: end; }}
    .w {{ fill: #fff; }}
  </style>''']
svg.append(f'  <text x="{x0}" y="26" class="m s">through the season →</text>')
svg.append(f'  <text x="{x0 - 12}" y="{ys + 5}" class="e b">Software</text>')
svg.append(f'  <text x="{x0 - 12}" y="{ym + 5}" class="e b">Mechanical</text>')
svg.append(f'  <rect x="{x0}" y="{ys - 20}" width="{pre - 8:.1f}" height="{ym - ys + 40}" rx="6" fill="var(--pre)"/>')
for k, line in enumerate(("CAD finished,", "drive trains", "built")):
    svg.append(f'  <text x="{x0 + (pre - 8) / 2:.1f}" y="{(ys + ym) / 2 - 12 + 16 * k}" class="c s">{line}</text>')
for i in range(3):
    a = x0 + pre + i * step; b = a + step - 8
    for y, label, col in ((ys, software[i], "--sw"), (ym, mechanical[i], "--me")):
        svg.append(f'  <rect x="{a:.1f}" y="{y - 20}" width="{b - a:.1f}" height="40" rx="6" fill="var({col})"/>')
        svg.append(f'  <text x="{(a + b) / 2:.1f}" y="{y + 5}" class="c s w">{label}</text>')
    if i < 2:                                   # the two robots swap rows at each definition of done
        xm = b + 4
        svg.append(f'  <path d="M{xm - 14:.1f} {ym - 24} L{xm + 12:.1f} {ys + 24}" stroke="var(--text)" stroke-width="1.5" fill="none" marker-end="url(#ar)"/>')
        svg.append(f'  <path d="M{xm - 14:.1f} {ys + 24} L{xm + 12:.1f} {ym - 24}" stroke="var(--text)" stroke-width="1.5" fill="none" marker-end="url(#ar)"/>')
        svg.append(f'  <text x="{xm:.1f}" y="{ym + 42}" class="c s m">{trades[i]}: trade</text>')
svg.append(f'  <text x="{x0}" y="{H - 14}" class="m s">Software always tests on the more complete robot while mechanical builds on the other.</text>')
svg.append('</svg>')
open(out, "w").write("\n".join(svg) + "\n")
