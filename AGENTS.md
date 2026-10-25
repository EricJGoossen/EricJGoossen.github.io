# Working on ericjgoossen.com (agent protocol)

Eric J. Goossen's portfolio: Markdown + Eleventy, built into plain static HTML in `_site/` and served by Cloudflare (static files only). Eric adds information over time, and agents turn it into pages. This file covers how to do that without breaking anything. `README.md` is the short human guide and `PLAN.md` is the design and roadmap. Read both once.

## Rules

1. **Branch.** Work on `phase-1`, or whatever branch Eric names. `main` is the live site. Eric's standing instruction (Oct 25, 2026): publish every change right away. Once `npm run check` passes and the change is committed and pushed to `phase-1`, push it to `main` too (a fast-forward), then confirm it on the live site.
2. **Keep it static.** No server code, frameworks, databases, logins, analytics, trackers, third-party scripts or web fonts. The only JavaScript is `src/assets/js/search.js` (the search results page, `/search/`, which reads `search-index.json`, built with the site; the box in the header is a plain form). If Eric approves something that loads from another domain, also add that domain to `src/_headers` (the Content-Security-Policy), or browsers will block it.
3. **Eric's machine.** Node runs only in Docker (`compose.yaml`, preview on port 8090). Don't change that setup. Don't install anything without asking. If something does get installed (including a Docker image), add it to `INSTALLED.md` with an uninstall command.
4. **Never invent facts about Eric.** Use only what Eric provides. Anything not provided yet stays as text starting with `Placeholder` (or a `"#"` link), so `npm run todo` can find it. That includes dates, numbers, results, co-authors, venues and awards.
5. **Nothing unfinished is visible.** A project, log entry or publication that isn't ready gets `draft: true` in its front matter (or its object in `publications.json`), which leaves it out of the built site entirely. The build fails if any visible page still has `Placeholder` text, a gray placeholder box or a `#` link.
6. **Pronouns.** Use they/them for anyone whose pronouns aren't stated.
7. **Commits.** Make small, focused commits with a message that says what and why. Push to the working branch as you go. `npm run check` must pass before every commit.
8. **Finish with a handoff.** Say what changed, what you checked, and what still needs Eric's content (summarize `npm run todo`).

## Commands

Run these in the repo root. In a cloud/CI environment with Node 22, run them directly. On Eric's machine, run them in Docker: `docker compose run --rm site <command>`, or `docker compose exec site <command>` while the preview is running.

| Command | What it does |
|---|---|
| `npm install` | Once, to get Eleventy (into `node_modules/`, gitignored) |
| `npm start` | Live preview on port 8080 (8090 on Eric's machine via Docker). Content problems show in a red banner at the top of every page. |
| `npm run check` | Builds the site and checks every link and #anchor. **Must pass before you commit.** |
| `npm run todo` | Lists every placeholder, `#` link and missing file still to fill in |
| `npm run new:project -- <folder> "Title" ["Org"]` | Creates a project page (as a draft) with a first log entry |
| `npm run new:entry -- <folder> "Entry title" [YYYY-MM-DD]` | Adds a dated log entry and prints its anchor |

## How the content fits together

```
src/_data/site.json          name, headline, bio, photo, links, authorNames, ogImage
src/_data/skills.json        skill list (order = chip order) + each skill's best example
src/_data/resume.json        paths to the resume PDF and the image of its first page
src/_data/publications.json  papers; `project` ties one to a project page
src/projects/<folder>/
  index.md                   project front matter + one-paragraph overview
  log/YYYY-MM-DD-<id>.md     progress log entries, shown newest first; <id> is the anchor
  images/                    that project's images and videos
src/assets/resume.pdf        resume (the Resume links stay hidden until this file exists)
assets-src/resume/resume.tex the resume's LaTeX source (not published); resume.pdf is compiled from it
```

- **The folder name is the URL**: `src/projects/fleet-rl/` becomes `/projects/fleet-rl/`.
- **Entry anchors**: the filename after the date is the entry's anchor. `log/2026-03-20-sim-comparison.md` is `/projects/<folder>/#sim-comparison`.
- **Highlights** live in a project's `index.md`. Each one names a log entry and the skills it shows. From those, the site builds:
  - the highlight chips on the project page
  - the skill tags on that log entry
  - a page per skill (`/skills/<name>/`, from `src/skill.njk`) showing every entry tagged with it in full, best example first; the home page skill chips link there

  Add a highlight in one place and it shows up everywhere it should.
- **Entries that aren't highlights** can still be tagged: add `skillTags: [C++, SIMD]` to the entry's front matter. (Not `skills:`, which is taken by `skills.json`.) An entry's tags are its highlight's skills plus its `skillTags`.
- **Skills** in `skills.json` set the chip order and each skill's `rank`: every entry tagged with it (`"<folder>/<entry id>"`), in the fixed order its skill page shows them. The first is its best example. The search card for a skill opens that first entry. A skill no entry is tagged with yet has no page and is hidden (the build prints a warning).
- **Search**: the box in the header of every page (`src/_includes/search-form.njk`, included by `base.njk`) opens the results page (`/search/?q=...`, `src/search.njk`), which lists a card for every match with the matching text highlighted, updating as you type. A click anywhere on a card opens it in place (a log entry in full, a skill's best example, a project's overview beside its hero, a paper's card; built as `html` in `searchIndex`); after that, its title goes to its page. It covers the intro, projects, log entries, skill pages and publications, from `search-index.json` (`src/search-index.njk`, `searchIndex` in `lib/skills.js`). Only published things are in it, and it updates itself with every build.

### Project front matter (`src/projects/<folder>/index.md`)

| Field | Required | Notes |
|---|---|---|
| `layout` | yes | Always `project.njk` |
| `draft` | no | `true` keeps the whole project (page, tile, skill links) off the site. New projects start as drafts. |
| `title`, `summary` | yes | `summary` is the one-liner on the home page tile |
| `org`, `timeline`, `tools` | no | Shown as the metadata line. `tools` is a list. |
| `order` | no | Number. Lower comes first on the home page. Leave gaps (10, 20, 30) if you like. |
| `cover` | no | Tile image or video, relative to the project folder: `images/cover.jpg` or `images/cover.mp4` |
| `coverPoster` | no | Still image for a video cover. Shown with reduced motion and used for link previews. |
| `hero`, `heroAlt`, `heroPoster` | no | Image or video behind the project intro: title, metadata, links, overview and highlight chips sit over it on a dark gradient (the poster replaces a video for reduced motion). Pick footage with its subject on the right and a dark background. Without a hero the intro is plain. |
| `highlights` | no | List of `{ label, entry, skills: [...] }`. `entry` must match a log entry anchor, and every skill must be in `skills.json`. |
| `links` | no | List of `{ label, url }`, shown as `[GitHub] [Paper] ...` |
| `heroFade` | no | `strong` fades the hero into an oval vignette, for footage whose edges would otherwise show. |
| `heroSide` | no | `right` keeps the hero footage in the right half, so the intro text sits on plain background. |
| `heroSize` | no | `large`, with `heroFade: strong`: the footage stays fully visible much further out before it fades, so more of the scene shows. |

## Recipes

**Add a project**
1. Run `npm run new:project -- <folder> "Title" "Org"`. Use a short lowercase folder name with dashes (it becomes the URL).
2. Fill in `index.md`: summary, org, timeline, tools, the overview paragraph, and `cover` once there's an image.
3. Add log entries (next recipe), then highlights.
4. When nothing on it is placeholder any more, delete the `draft: true` line to publish it.
5. Run `npm run check`, commit, push.

**Add a progress log entry**
1. Run `npm run new:entry -- <folder> "What happened" [date]`. Use the date the work happened, not today, if Eric gives one.
2. Replace the `Placeholder:` text with the real write-up, and delete the template comment. (Add `draft: true` to its front matter to keep a half-written entry off the site.) Give each paragraph its own image or video with `{% row %}` (next recipe): the paragraph sits on the left, the media on the right (below it on phones), with a thin line between rows.
3. Give it links, shown as `[Code] [Paper]` under its title: `links:` in its front matter, a list of `{ label, url }`. Link the specific code the entry is about (a commit, a pull request, or a folder at a commit), or the repo if nothing narrower fits. Every entry should have at least one; if there's nothing to link, say so in the handoff.
   Give it its basic facts too, shown on one line under the links (the build warns about a published entry without them). Keep each to a word or two from the lists below, so none wraps: the build stops on one over 24 characters. Leave out any field that doesn't apply (an event has no language), and any Eric hasn't confirmed or the entry doesn't already say:
   ```yaml
   info:
     language: C++              # or a list: [C++, Python]
     tools: [xsimd, Valgrind]   # the libraries and tools that matter for this entry
     hardware: Franka Panda     # what it ran on, or "Laptop CPU", "OpenArm (simulated)"
     role: Solo                 # Solo, Lead, Team, Captain, Co-author, Presenter, Speaker or Teacher
     status: On the robot       # how far it got: In simulation, In main, On a branch, Used at competition, In the paper, Done
   ```
4. Entries show newest first. Two entries on the same day are ordered by a time in the front matter, e.g. `date: 2026-09-19 11:02:53` (the time is only used for ordering; the page shows the date).
5. To feature it, add a highlight to the project's `index.md`:
   ```yaml
   highlights:
     - label: SIMD optimization     # 1 to 3 words
       entry: simd-optimization     # the anchor the script printed
       skills: [C++, SIMD]          # each must be in skills.json
   ```

**Add or change a skill**
- New skill: add `{ "name": "SIMD", "rank": ["opendubs/simd-optimization"] }` to `skills.json`, at the position where its chip should appear. Then tag highlights with exactly the same spelling.
- Renaming a skill means renaming it in `skills.json` **and** in every highlight that uses it. The build lists any you miss.
- `rank` lists exactly the published entries tagged with this skill (by a highlight or `skillTags`), best first. When you tag a new entry with a skill, add it to that skill's `rank` where it belongs; the build stops until you do.

**Add images and videos** (put the files in the project's `images/` folder)
- A paragraph with its image or video beside it (the usual way to write a log entry). Until the file exists, `{% row "placeholder", "Video: what it will show" %}` holds its place with a gray box. The blank-line rules of Markdown apply inside, so keep the paragraph unindented:
  ```
  {% row "images/chart.svg", "What the image shows", { caption: "..." } %}
  The paragraph, in Markdown.
  {% endrow %}
  ```
  Videos work the same way (`{ poster: "images/still.jpg" }` for the still). To stack more media under the first (say a clip and the chart that backs it up), add `more: [{ src: "images/chart.svg", alt: "...", caption: "..." }]`. Portrait media sit at half width (two side by side); add `wide: true` to show one at full width. Add `half: true` to put landscape media at half width too, so two sit side by side (stacked again on phones), or `narrow: true` to show one at three quarters of the column (a square clip that would otherwise tower). The build stops if any of them has no media or no alt text.
- Image in a log entry: `![What the image shows](images/photo.jpg)`. Always write real alt text.
- Short clip that loops like a GIF (muted, with pause controls): `{% video "images/clip.mp4", "What it shows" %}`
- Longer video with sound (click to play): `{% video "images/talk.mp4", "What it shows", { play: true, poster: "images/talk.jpg" } %}`
- Optional caption on either: add `caption: "..."` to the options. A photo credit goes in `credit: "Photo: ..."` (on `{% row %}` and `{% video %}`, and in each `more` item), a small line right under the media, so the caption stays about the picture.
- YouTube: `{% youtube "VIDEO_ID or full link", "Title", { poster: "images/still.jpg" } %}`. This shows a thumbnail that opens the video on YouTube in a new tab; no YouTube code runs on the site. Give it a `poster` (a still from the video, in the project's `images/`) so the thumbnail is local: otherwise it loads from YouTube's image server, which the artifact preview blocks. In a `{% row %}`, a YouTube link in place of the file does the same, with the alt text as its title (and `poster` in its options).
- Covers, heroes and publication teasers can be `.mp4` too. Give a video cover a `coverPoster`.
- Sizes: aim for images under about 1 MB (2000px on the long side) and clips under 5 MB. Cloudflare rejects any file over 25 MB, and the build stops on it.
- Use MP4 (H.264) for video so every browser plays it. To shrink a clip, ffmpeg in Docker works:
  `docker run --rm -v "$PWD":/w -w /w linuxserver/ffmpeg -i in.mov -vf "scale=1280:-2" -c:v libx264 -crf 28 -preset slow -an -movflags +faststart out.mp4`
  (`-an` drops audio; leave it off for clips with sound.) That pulls a Docker image, so ask Eric first and log it in `INSTALLED.md`.

**Add a publication**
Add an object to `publications.json`:
```json
{
  "title": "...", "authors": ["...", "Eric J. Goossen"], "venue": "CoRL", "year": 2026,
  "status": "", "award": "", "lab": "Human Centered Robotics Lab", "project": "hil-cap",
  "image": "/projects/hil-cap/images/teaser.jpg", "tldr": "One or two sentences.",
  "links": [{ "label": "Paper", "url": "https://..." }, { "label": "arXiv", "url": "https://..." }]
}
```
- `image` (and the optional `poster`) start at `src/`. Put paper images in `src/assets/pubs/`: a draft project's `images/` folder isn't published at all, so an image there would break while the project is hidden. Give it real alt text with `imageAlt` (otherwise it reads "Teaser for <title>"). The card crops it to 4:3.
- Names listed in `site.json` `authorNames` are shown in bold.
- Empty badge fields are hidden.
- `project` must be an existing project folder. The card then also appears on that project page, and gets a `[Project page]` link once that project is published.
- Without an `image` the card is text-only. `"draft": true` keeps a paper off the site.

**Bio, photo, links, resume**
- Bio, headline, photo and links go in `site.json`. `photo` and `ogImage` paths start at `src/`, e.g. `/assets/photo.jpg`.
- The resume PDF goes at `src/assets/resume.pdf`. The Resume links appear automatically once it exists.
- The home page Resume section shows the PDF itself: an image of its first page (`src/assets/resume.png`) that opens the PDF, and a Download PDF button. Nothing from the resume is copied onto the page.
- To update the resume, replace `src/assets/resume.pdf` with Eric's new PDF (or edit `assets-src/resume/resume.tex` and recompile it with `pdflatex` in a cloud session; Eric's machine has no TeX), then regenerate the page image: `pdftoppm -png -r 160 -singlefile src/assets/resume.pdf page && convert page.png -colors 16 PNG8:src/assets/resume.png` (poppler and ImageMagick, in a cloud session).

**Reorder, rename or remove**
- Reorder projects by changing their `order` numbers.
- Renaming a project folder or a log entry changes its URL or anchor. Update every highlight `entry`, every skill `rank`, and every publication `project` that points at it. The build lists any you miss. Avoid renames once the site is live, because people may have links to them; when one is needed, add the old path to `src/_redirects` (renaming a skill moves its page, `/skills/<name>/`, too).
- To remove a project, delete its folder and fix whatever the build reports.

## Checks (what keeps the site from breaking)

`lib/checks.js` runs on every build. A real build (`npm run build`, `npm run check`, Cloudflare) **stops** on any of these. The live preview shows them in a red banner instead.
- A highlight points at a log entry that doesn't exist.
- A highlight uses a skill that's not in `skills.json`.
- A skill's `rank` lists an entry that isn't tagged with it, or misses one that is.
- A skill name is listed twice, or two skills would share a page URL (e.g. "C++" and "Cpp").
- An entry's `skillTags` isn't a list, or names a skill that's not in `skills.json`.
- A log file doesn't start with a date, or two entries in one project share an anchor.
- A project is missing `title` or `summary`, or its `order` isn't a number.
- A `cover`, `hero`, poster, publication `image`, `photo` or `ogImage` file doesn't exist.
- A publication's `project` doesn't exist, or it has no `title` or `authors`.
- A file is over 25 MB (files over 5 MB get a warning).

`scripts/check-links.js` (part of `npm run build` and `npm run check`) then checks every internal link, image/video source and #anchor in `_site/`, and fails if a visible page has `Placeholder` text, a gray placeholder box or a `#` link. Fix the content or mark the item `draft: true`.

The checks can't judge content quality. Read what you wrote, and keep `Placeholder` markers on anything not confirmed by Eric.

## Changing templates, CSS or code

- **Where things live:**
  - Templates: `src/index.njk` (home), `src/_includes/base.njk` (page shell), `project.njk` (project page), `pub.njk` (publication card)
  - Styles: `src/assets/css/style.css` (color tokens at the top, with a dark-mode block)
  - Code: `eleventy.config.js` (collections, filters, shortcodes), `lib/checks.js`, `lib/media.js`
- **Design rules** (from mateoguaman.com, timothypan.com and the mnats bio page):
  - one clean centered column with generous white space
  - images and video do the visual work
  - restrained color
  - compact `[bracketed]` links
- Home sections render only when their data has entries, in this order: Intro, Skills, Projects, Publications, Resume. The nav follows the same order.
- After a visual change, check:
  - light mode, dark mode, and a ~375px-wide phone
  - hover and keyboard focus on project tiles
  - a skill page, and a search from the header box (it opens `/search/`; `src/_headers` must keep `form-action 'self'` or browsers block the form)
  - no horizontal scrolling
- Keep it accessible: real alt text, visible focus outlines, 4.5:1 text contrast, and nothing that only works on hover.
- If you add a new kind of data, add a check for it in `lib/checks.js` so mistakes fail loudly.

## Before you hand off

1. `npm run check` passes.
2. Visual check done, if templates or CSS changed.
3. Committed and pushed to the working branch, then published to `main` (rule 1).
4. Tell Eric what changed and paste the short version of `npm run todo`.
