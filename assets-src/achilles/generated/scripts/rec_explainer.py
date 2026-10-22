"""Record the SIMD explainer (8 lanes) frame by frame on a fake clock -> PNG frames."""
import sys, os
from playwright.sync_api import sync_playwright
url, outdir = sys.argv[1], sys.argv[2]
FPS, SLOW = 30, 1.3          # play at 1/1.3 speed so captions can be read
SKIP = {10: 11}              # skip the register-spill step, go straight to "measured"
os.makedirs(outdir, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(color_scheme="light", viewport={"width": 960, "height": 760})
    pg.clock.install()
    pg.clock.pause_at(1_700_000_000_000)
    pg.goto(url)
    pg.add_style_tag(content=".controls{display:none!important} .caption{min-height:3.4em} main>h1,main>.muted,.foot{display:none}")
    pg.evaluate("setLanes(8)")
    panel = pg.locator(".panel")
    n, hold = 0, 0
    while True:
        k = pg.evaluate("k")
        if k in SKIP:
            pg.evaluate(f"go({SKIP[k]})")
        panel.screenshot(path=f"{outdir}/f{n:05d}.png")
        n += 1
        if not pg.evaluate("playing"):
            hold += 1
            if hold > FPS * 2: break
        pg.clock.run_for(round(1000 / FPS / SLOW))
    print("frames", n)
    b.close()
