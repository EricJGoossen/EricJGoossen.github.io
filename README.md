# ericjgoossen.com

Personal portfolio site. Plain static HTML/CSS, hosted on Cloudflare Workers (static assets only, no server code).

## How it works

- Everything that gets published lives in `site/`. Files outside it (like this README) are not served.
- Pushing to `main` on GitHub automatically redeploys the live site.
- To preview locally, open `site/index.html` in a browser.

## Cloudflare settings

Config lives in `wrangler.jsonc`, which points Cloudflare at `site/`.

- Build command: (empty)
- Deploy command: `npx wrangler deploy`
