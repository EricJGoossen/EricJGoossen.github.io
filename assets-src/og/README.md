# Link preview image

`src/assets/og-image.jpg` (1200×630, `ogImage` in `src/_data/site.json`) is the picture shown when the
home page is shared. It is `og.html` rendered by a browser at 1200×630: the headshot, name, headline,
site address, GitHub and LinkedIn,
and four project tiles from `tiles/` (Eric's picks, Oct 25), each cropped to the card's shape around
its subject:

- `opendubs.jpg`: the two-arm handover render (`opendubs/images/hero-handover.jpg`), around the arms.
- `hil-cap.jpg`: the ARCHITECT hero video (`hil-cap/images/hero-architect.mp4`) at 3 s, the arm
  dropping the apple in the bowl.
- `aruw.jpg`: the 2026 robot reveal (YouTube FGh1yQdJGeM) at 1:22.5, the two lit robots.
- `botswana.jpg`: the Botswana card photo (`botswana/images/cover-tree.jpg`).

To remake it, open `og.html` from this folder in Chromium at 1200×630 (Playwright: `page.screenshot`),
and save as JPEG.
