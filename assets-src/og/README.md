# Link preview image

`src/assets/og-image.jpg` (1200×630, `ogImage` in `src/_data/site.json`) is the picture shown when the
home page is shared. It is `og.html` rendered by a browser at 1200×630: the headshot, name and headline,
and four project tiles (OpenDubs, HCRL, Fleet RL, ARUW, the home page's first four). To remake it, open
`og.html` from this folder in Chromium at 1200×630 (Playwright: `page.screenshot`), and save as JPEG.
