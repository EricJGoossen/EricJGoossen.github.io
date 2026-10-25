# Site plan

Not published. Only the build output goes live.

## What the site is

An overview of Eric: who he is, what he can do, and what he's built, with a page per project that doubles as a progress log. Built so a recruiter can go from "I want that skill" to seeing it in context in one or two clicks.

## Pages

### Home (`/`)

Single scrolling page, in this order (a compact intro, then skills and projects right away so they're visible on load):

1. **Intro / bio.** Name, one-line headline (role + what you're looking for), short bio paragraph, photo (optional), links: GitHub, LinkedIn, email, resume PDF.
2. **Skills.** A row of skill chips (e.g. C++, MuJoCo, RL), each with a count. Clicking one opens that skill's page (`/skills/<name>/`): every log entry tagged with the skill, across all projects, shown in full. The **best example** comes first (marked), the rest newest first, each linking back to its place in the project log.
3. **Projects.** Large image tiles, two per row (one on phones), in the style of timothypan.com. Title, lab/org and one-line summary appear over the image on hover or keyboard focus, and below the image on touch screens. The whole tile is the link to the project page.
4. **Resume.** The PDF itself, shown as an image of its first page that opens it, plus a "Download PDF" button.
5. **Publications.** One card per paper, like mateoguaman.com: teaser image, venue/status/award badges, title, authors (Eric in bold), a one-line TL;DR, and `[Paper] [arXiv] [Video] [Code] [Project page]`. The same card also appears on the related project page.

### Project page (`/projects/<name>/`)

1. **Header.** Title, lab/org · timeline · tools, then the bracketed links, one-paragraph overview, hero image.
2. **Entries.** A chip per log entry with a 1 to 2 word label, linking to it in the log (its summary on hover); the most impressive ones are featured (bold, accent edge).
3. **Publication.** The related publication card, if there is one. (Links like `[GitHub] [Paper] [Video] [Demo]` sit in the header, under the metadata line.)
4. **Progress log.** Blog-style entries, newest first, each paragraph beside its own image or video (stacked on phones) with a thin line between them; rows rise into view as you scroll, text first and media sliding in from the right (CSS only, off with reduced motion). A project with a `hero` opens with its intro (title, metadata, links, overview, highlights) laid over that footage. Each entry: date, title, text, any number of images, and an anchor the entries list links to. An entry's skill tags link to the skill pages.
5. **Back to all projects** link.

### Also

- 404 page
- Social preview image + description so links look good when shared on LinkedIn/Slack
- Works on phones, follows light/dark mode

## Projects

| Page | Project | Org |
|------|---------|-----|
| `/projects/opendubs/` | OpenDubs | Personal Robotics Lab |
| `/projects/hil-cap/` | HiL feedback on CaP | Human Centered Robotics Lab |
| `/projects/fleet-rl/` | Fleet RL | WEIRD Lab |
| `/projects/aruw/` | Advanced Robotics at UW | ARUW |
| `/projects/achilles/` | Achilles | |
| `/projects/botswana/` | Botswana | |
| `/projects/ftc/` | FTC (SKIDADDLE, Live View) | One page, one or two entries per project |

## How skills connect

Each entry lists its skills once, in its front matter, and can be featured:

```yaml
summary: "Structure-of-arrays storage so one SIMD instruction steps eight robots."
featured: true
short: SIMD batching
skillTags: [C++, Performance & SIMD]
```

`skills.json` lists each skill and its entries in a fixed order, best first:

```json
{ "name": "C++", "rank": ["achilles/collision-response", "..."] }
```

The site builds everything else from these: the skill pages, the entry chips, the entry tags and the anchor links.

## How content gets written

**Markdown + Eleventy** (a small static site generator).

- Each project is a folder. The overview is one Markdown file with a header block (title, org, summary, cover image, links). Each log entry is its own Markdown file with a date. Adding an update = drop in a new `.md` file and images, `git push`.
- Bio, resume, and skills live in small data files, so the home page builds itself from them.
- Output is still plain static HTML, so security is unchanged. No server, no database, no login. The only JavaScript is the search results page; the box in the header is a plain form that opens it.
- **Node runs in Docker**, not on the machine. `docker compose up` starts a live-reloading preview at localhost:8090. Cloudflare runs the same build itself on each push.

## Folder layout

```
src/
  index.njk                  home page template
  skill.njk                  one page per skill (/skills/<name>/)
  search-index.njk           search-index.json, what the search box searches
  _data/
    site.json                name, headline, bio, photo, links
    skills.json              skill list + best example for each
    resume.json              resume PDF and preview image paths
    publications.json        papers, each linked to a project
  _includes/                 shared layouts (page shell, project page, publication card)
  projects/
    opendubs/
      index.md               overview, cover, links
      log/
        2026-10-21-first-prototype.md
      images/                images and videos
    ...
  assets/
    css/style.css
    js/search.js             the search results page (/search/), the only JavaScript
    resume.pdf
  _headers                   security headers, read by Cloudflare
lib/
  checks.js                  build-time content checks
  media.js                   image/video/YouTube markup
  skills.js                  skill pages and the search index
scripts/                     check-links, todo, new-project, new-entry
_site/                       build output, what Cloudflare serves
compose.yaml                 Node toolchain for local preview (Docker)
wrangler.jsonc               points Cloudflare at _site/
AGENTS.md                    protocol for AI agents updating the site
```

## Design direction

From the reference sites (mateoguaman.com, mnats, timothypan.com): one clean centered column, generous white space, restrained color, images doing the visual work, and compact bracketed links. Borrow the per-project metadata line from timothypan.com (org · timeline · tools). Quick mockup of the home page and a project page to react to before building it for real.

## Build order

**Phase 1: Bones with placeholders** (no real content needed)

1. Docker + Eleventy setup; switch Cloudflare to build from `src/` into `_site/`.
2. Home page: bio, resume, skill chips with dropdowns, project grid. All placeholder text and gray image boxes.
3. Project page template: header, highlights, links, log with anchors.
4. All 7 project pages stubbed with placeholder overviews, 2 to 3 placeholder highlights, and a couple of placeholder log entries each, so every link and dropdown actually works.
5. Design pass on the real skeleton: type, spacing, colors, phone layout, dark mode.
6. Push. Live site shows the full structure with placeholders.

**Phase 2: Backfill** (one project at a time, any order)

7. Bio, headline, resume PDF + condensed resume, skills list.
8. Each project: real overview, cover image, highlights, links, log entries.
9. Polish: image compression, social preview, 404, accessibility check.

## Status and next steps

**Done (phase-1 branch):** Phase 1 bones, the design pass, publications, video support, build-time content checks, `npm run check` / `todo` / `new:project` / `new:entry`, security headers, and `AGENTS.md`.

**MVP (publishable now):** real intro, bio, resume (PDF), the "A Few Words Go a Long Way" publication, and the Achilles project. The other six projects are `draft: true` (hidden), and the build refuses to publish any visible placeholder text, so the live site only shows what's real.

**Next, in order:**

1. **Backfill the other projects** one at a time (Phase 2 above), removing `draft: true` from each when it's done. `npm run todo` is the checklist.
2. **Automatic image resizing.** `@11ty/eleventy-img` would make phone-sized WebP/AVIF copies with width/height at build time, so full-size photos don't slow the site down. One dependency, inside Docker only.
3. **Confirm the Cloudflare build** before merging to `main`: a `phase-1` preview build log should show `npm run build` succeeding (see README, Deploying).
4. **Nice to have, when wanted:**
   - a short News list on the home page (`news.json`)
   - Cloudflare Web Analytics (cookie-free, but adds one Cloudflare script and needs a CSP update)
   - print styles for a one-page resume
   - a table of contents for long project logs

**Not planned:** contact form (needs a server or a third-party service), comments, a CMS, JS frameworks. (Site search is done without a server: a JSON index built with the site and one small script.)

## Still open

- Skill list: which skills, and which highlight is each one's best example. Can be filled during backfill.
- When to replace the "coming soon" page on `main`: Eric's call, once there's enough real content.
