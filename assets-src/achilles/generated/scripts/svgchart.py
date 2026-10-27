"""Tiny theme-aware SVG line/bar charts in the site's style (CSS variables + dark block)."""
import math
from html import escape

STYLE = """  <style>
    svg { --text:#1c1917; --muted:#6b6560; --grid:#e7e5e4; --axis:#a8a29e;
          --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a; --s4:#eda100; --s5:#6250d6; --ref:#78716c; }
    @media screen {
      svg { --text:#f2f1ef; --muted:#a39d97; --grid:#33312e; --axis:#57534e;
            --s1:#3987e5; --s2:#d95926; --s3:#199e70; --s4:#c98500; --s5:#9085e9; --ref:#a8a29e; }
    }
    text { font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; fill: var(--text); font-size: 13px; }
    .m { fill: var(--muted); } .s { font-size: 12px; } .b { font-weight: 650; }
    .e { text-anchor: end; } .c { text-anchor: middle; }
    .grid { stroke: var(--grid); stroke-width: 1; }
    .axis { stroke: var(--axis); stroke-width: 1; }
    .ln { fill: none; stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
    .dash { stroke-dasharray: 6 4; }
    .guide { stroke: var(--muted); stroke-width: 1; stroke-dasharray: 3 3; }
  </style>
"""

def pow10(v, suffix=""):
    """10 with a raised exponent, as SVG text content."""
    e = int(round(math.log10(v)))
    exp = str(e).replace("-", "\u2212")
    return f'10<tspan dy="-6" font-size="9.5">{exp}</tspan>' + (f'<tspan dy="6">{suffix}</tspan>' if suffix else "")

class Chart:
    def __init__(self, title, desc, w=680, h=400, ml=64, mr=24, mt=64, mb=52):
        self.title, self.desc = title, desc
        self.w, self.h, self.ml, self.mr, self.mt, self.mb = w, h, ml, mr, mt, mb
        self.body = []
    # scales
    def xscale(self, lo, hi, log=False):
        self.xlo, self.xhi, self.xlog = lo, hi, log
    def yscale(self, lo, hi, log=False):
        self.ylo, self.yhi, self.ylog = lo, hi, log
    def X(self, v):
        f = (math.log10(v) - math.log10(self.xlo)) / (math.log10(self.xhi) - math.log10(self.xlo)) if self.xlog else (v - self.xlo) / (self.xhi - self.xlo)
        return self.ml + f * (self.w - self.ml - self.mr)
    def Y(self, v):
        if self.ylog:
            v = max(v, self.ylo)
            f = (math.log10(v) - math.log10(self.ylo)) / (math.log10(self.yhi) - math.log10(self.ylo))
        else:
            f = (v - self.ylo) / (self.yhi - self.ylo)
        f = min(max(f, -0.02), 1.02)
        return self.h - self.mb - f * (self.h - self.mt - self.mb)
    def axes(self, xticks, yticks, xlabel, ylabel, xfmt=str, yfmt=str):
        b = self.body
        for v in yticks:
            y = self.Y(v)
            b.append(f'<line class="grid" x1="{self.ml}" x2="{self.w-self.mr}" y1="{y:.1f}" y2="{y:.1f}"/>')
            b.append(f'<text class="s m e" x="{self.ml-8}" y="{y+4:.1f}">{yfmt(v)}</text>')
        y0 = self.h - self.mb
        b.append(f'<line class="axis" x1="{self.ml}" x2="{self.w-self.mr}" y1="{y0}" y2="{y0}"/>')
        for v in xticks:
            x = self.X(v)
            b.append(f'<text class="s m c" x="{x:.1f}" y="{y0+18}">{xfmt(v)}</text>')
        b.append(f'<text class="s m c" x="{(self.ml+self.w-self.mr)/2:.0f}" y="{self.h-12}">{escape(xlabel)}</text>')
        b.append(f'<text class="s m" x="{self.ml-8}" y="{self.mt-14}" text-anchor="start">{escape(ylabel)}</text>')
    def line(self, xs, ys, var, dash=False, width=2, opacity=1):
        pts = " ".join(f"{self.X(x):.1f},{self.Y(y):.1f}" for x, y in zip(xs, ys))
        cls = "ln dash" if dash else "ln"
        op = f' stroke-opacity="{opacity}"' if opacity != 1 else ""
        self.body.append(f'<polyline class="{cls}" style="stroke:var({var})" stroke-width="{width}"{op} points="{pts}"/>')
    def hguide(self, v, label, below=False, x=None):
        y = self.Y(v)
        self.body.append(f'<line class="guide" x1="{self.ml}" x2="{self.w-self.mr}" y1="{y:.1f}" y2="{y:.1f}"/>')
        ty = y + 16 if below else y - 6
        self.body.append(f'<text class="s m e" x="{x or self.w-self.mr-4}" y="{ty:.1f}">{escape(label)}</text>')
    def label(self, x, y, text, var=None, anchor="start", cls="s"):
        fill = ' class="%s"' % cls
        self.body.append(f'<text{fill} x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}">{text}</text>')
    def legend(self, items, y=None):
        """items: (label, var, dash). Laid out in rows across the top."""
        x, y = self.ml, y or 22
        for text, var, dash in items:
            wtxt = 7.2 * len(text) + 34
            if x + wtxt > self.w - self.mr:
                x, y = self.ml, y + 22
            d = ' stroke-dasharray="6 4"' if dash else ''
            self.body.append(f'<line x1="{x}" x2="{x+20}" y1="{y-4}" y2="{y-4}" style="stroke:var({var})" stroke-width="2.5" stroke-linecap="round"{d}/>')
            self.body.append(f'<text class="s" x="{x+26}" y="{y}">{escape(text)}</text>')
            x += wtxt
    def svg(self):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="t d">\n'
                f'  <title id="t">{escape(self.title)}</title>\n  <desc id="d">{escape(self.desc)}</desc>\n'
                + STYLE + "  " + "\n  ".join(self.body) + "\n</svg>\n")
