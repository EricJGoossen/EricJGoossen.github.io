import sys, os
from playwright.sync_api import sync_playwright
url, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(color_scheme="light", viewport={"width": 1000, "height": 1100})
    pg.goto(url, timeout=120000)
    pg.add_style_tag(content=".controls{display:none!important} #ticker{min-height:150px}")
    pg.evaluate("layout()")
    F = pg.evaluate("F")
    for f in range(F):
        pg.evaluate(f"seek({f})")
        pg.screenshot(path=f"{outdir}/f{f:05d}.png", clip={"x": 0, "y": 0, "width": 1000, "height": 1000})
    print("frames", F)
    b.close()
