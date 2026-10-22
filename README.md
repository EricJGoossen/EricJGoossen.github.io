# ericjgoossen.com

Personal portfolio site. Markdown + [Eleventy](https://www.11ty.dev/) build to plain static HTML, hosted on Cloudflare Workers (static assets only, no server code). See `PLAN.md` for the design.

## Preview locally

Node runs only in Docker.

```bash
docker compose up -d      # preview at http://localhost:8090, reloads on save
docker compose down       # stop it
```

## Where things live

| To change... | Edit |
|---|---|
| Name, headline, bio, top links | `src/_data/site.json` |
| Link preview image (LinkedIn/Slack) | `ogImage` in `site.json` for the home page, e.g. `"/assets/og.jpg"`. Project pages use their `cover` automatically. |
| Resume section | `src/_data/resume.json`, PDF at `src/assets/resume.pdf` |
| Skills and each one's best example | `src/_data/skills.json` |
| Publications | `src/_data/publications.json` (see below) |
| A project's overview, highlights, links | `src/projects/<name>/index.md` |
| A project's progress log | `src/projects/<name>/log/*.md` |
| Project images | `src/projects/<name>/images/` |
| Look and feel | `src/assets/css/style.css` |

## Adding a progress log entry

Create `src/projects/<name>/log/YYYY-MM-DD-short-name.md`:

```markdown
---
title: What happened
---
Text in Markdown. Images go in the project's images/ folder:

![What the image shows](images/my-photo.jpg)
```

The part of the filename after the date (`short-name`) is the entry's anchor. To make it a highlight, add it to `highlights` in the project's `index.md` with `entry: short-name` and the skills it shows.

## Adding a publication

Add an entry to `src/_data/publications.json`. It shows at the bottom of the home page, and on the project page whose folder name matches `project` (e.g. `"project": "hil-cap"`).

- `authors`: any name listed in `authorNames` in `site.json` is shown in bold.
- `image`: teaser figure, e.g. `/projects/hil-cap/images/teaser.jpg`. Leave empty for a gray placeholder.
- `venue`, `year`, `status`, `award`: shown as badges. Leave any of them empty to hide it.
- `links`: shown as `[Paper] [arXiv] [Video] [Code]`. The first one is also the title link. A `[Project page]` link is added automatically.

## Deploying

Pushing to `main` deploys. Cloudflare runs `npx wrangler deploy`, which first runs `npm run build` (the `build.command` in `wrangler.jsonc`) and then uploads `_site/`.

Checked against Wrangler 4.151's source: for a static-assets-only Worker, `wrangler deploy` runs the custom build before it checks that `_site/` exists, so a fresh clone works. Still to confirm in the Cloudflare dashboard (any `phase-1` preview build log shows it): that Workers Builds installs npm dependencies before the deploy command. If the log shows `eleventy: not found`, set the build command to `npm ci` (or `npm run build`) in the dashboard.

The build stops on content problems (see `lib/checks.js`), so a broken change can't replace the live site; the previous version stays up.

Security headers (Content-Security-Policy and friends) live in `src/_headers`, which Cloudflare reads at deploy time.
