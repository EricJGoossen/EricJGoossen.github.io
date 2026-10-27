// Skill pages and the search index, both built from the same published
// projects and log entries the rest of the site uses.
import { isVideo, mediaUrl } from "./media.js";

// URL-safe name for a skill page: "C++" → "cpp", "Rigid-body dynamics" → "rigid-body-dynamics".
export const skillSlug = (name = "") =>
  name
    .toLowerCase()
    .replace(/\+/g, "p")
    .replace(/#/g, "sharp")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");

export const entryId = (entry) => entry.data.id ?? entry.fileSlug;
export const projectOf = (entry, projects) =>
  projects.find((p) => entry.inputPath.includes(`/projects/${p.fileSlug}/log/`));
// An entry's skills: its `skillTags:` list. (`project` is unused, kept so
// templates can keep passing it.)
export const entrySkills = (entry, project) => [...new Set(entry.data.skillTags ?? [])];
// Its label where space is short: the `short` of a featured entry, else its title.
export const entryLabel = (entry) => entry.data.short ?? entry.data.title;

// An entry's basic facts, from `info:` in its front matter, shown under its
// links in this order. Fields that don't apply (no code, say) are left out.
export const ENTRY_INFO = [
  ["language", "Language"],
  ["tools", "Tools"],
  ["hardware", "Hardware"],
  ["role", "Role"],
  ["status", "Status"],
];
export const entryInfo = (entry) =>
  ENTRY_INFO.filter(([key]) => entry.data.info?.[key]).map(([key, label]) => {
    const value = entry.data.info[key];
    return { label, value: Array.isArray(value) ? value.join(", ") : String(value) };
  });

// Lines of code Eric wrote for an entry (`loc:` in its front matter, counted
// with git from the commits the entry links to: see assets-src/loc/README.md),
// and a project's total, the sum of its published entries.
export const entryLoc = (entry) => (Number.isInteger(entry.data.loc) && entry.data.loc > 0 ? entry.data.loc : 0);
export const projectLoc = (entries = []) => entries.reduce((n, e) => n + entryLoc(e), 0);
export const formatLoc = (n) => Number(n).toLocaleString("en-US");

// One page per skill: every published log entry tagged with it, in the order
// of the skill's `rank` in skills.json (the first is its best example). A
// skill on no entry yet gets no page (and no chip on the home page).
export function skillPages(skills, projects, entries) {
  return skills
    .map((skill) => {
      const uses = [];
      for (const entry of entries) {
        const project = projectOf(entry, projects);
        if (!project) continue; // its project is still a draft
        const tags = entrySkills(entry, project);
        const key = `${project.fileSlug}/${entryId(entry)}`;
        // A hidden skill (only reachable by URL or search) is tagged by its rank alone.
        if (skill.hidden ? !(skill.rank ?? []).includes(key) : !tags.includes(skill.name)) continue;
        const label = entryLabel(entry);
        uses.push({ key, project, entry, label, otherSkills: tags.filter((t) => t !== skill.name), best: key === skill.rank?.[0] });
      }
      // In the skill's fixed `rank`; anything not ranked yet goes last, newest first.
      const place = (u) => (skill.rank ?? []).indexOf(u.key) >>> 0;
      uses.sort((a, b) => place(a) - place(b) || b.entry.date - a.entry.date);
      const projectCount = new Set(uses.map((u) => u.project)).size;
      return { name: skill.name, slug: skillSlug(skill.name), description: skill.description ?? "", hidden: !!skill.hidden, uses, projectCount };
    })
    .filter((skill) => skill.uses.length);
}

// Media and #links inside an entry are relative to its project page. Shown on
// another page (a skill page), they need the project's URL in front.
export const rebase = (html = "", base = "/") =>
  html.replace(/\s(src|poster|href)="(?![a-z][a-z0-9+.-]*:|\/)([^"]*)"/gi, (_, attr, url) => ` ${attr}="${base}${url}"`);

const ENTITIES = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " " };
export const plainText = (html = "") =>
  html
    .replace(/<(script|style)[\s\S]*?<\/\1>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&(#x?[0-9a-f]+|[a-z]+);/gi, (m, code) =>
      code[0] === "#"
        ? String.fromCodePoint(code[1].toLowerCase() === "x" ? parseInt(code.slice(2), 16) : parseInt(code.slice(1), 10))
        : ENTITIES[code.toLowerCase()] ?? m
    )
    .replace(/\s+/g, " ")
    .trim();

// What an opened search card shows, built as HTML here: text beside its
// picture, laid out like a {% row %}. A video loops muted, like a tile.
const esc = (s = "") => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
function cardMedia(src, alt, poster = "") {
  if (!src) return "";
  return isVideo(src)
    ? `<video src="${esc(src)}"${poster ? ` poster="${esc(poster)}"` : ""} autoplay muted loop playsinline aria-label="${esc(alt)}"></video>`
    : `<img src="${esc(src)}" alt="${esc(alt)}" loading="lazy">`;
}
const cardRow = (text, media) =>
  media ? `<div class="row"><div class="row-text">${text}</div><div class="row-media"><figure>${media}</figure></div></div>` : `<div class="row-text">${text}</div>`;
const cardLinks = (links = []) =>
  links.length ? `<p class="bracket-links">${links.map((l) => `<a href="${esc(l.url)}">${esc(l.label)}</a>`).join("")}</p>` : "";

// A project's card: its hero (or cover) beside the metadata, links, overview and featured entries.
function projectCard(p, entries) {
  const d = p.data;
  const src = d.hero || d.cover;
  const poster = d.hero ? d.heroPoster : d.coverPoster;
  const meta = [d.org, d.timeline, (d.tools ?? []).join(", ")].filter(Boolean).join(" · ");
  const chips = entries
    .filter((e) => e.data.featured && projectOf(e, [p]))
    .map((e) => `<a class="chip" href="${p.url}#${esc(entryId(e))}">${esc(entryLabel(e))}</a>`)
    .join(" ");
  const text = [
    meta && `<p class="muted">${esc(meta)}</p>`,
    cardLinks(d.links),
    rebase(p.templateContent, p.url),
    chips && `<nav class="chips" aria-label="Featured entries">${chips}</nav>`,
  ].filter(Boolean).join("");
  return cardRow(text, cardMedia(src && mediaUrl(p.url, src), d.heroAlt || d.title, poster && mediaUrl(p.url, poster)));
}

// A skill's card: its description and counts, then a card per entry that shows
// it (in its rank, best example first), each opening that entry on its page.
function skillCard(s) {
  const counts = [`${s.uses.length} log ${s.uses.length === 1 ? "entry" : "entries"}`, `${s.projectCount} ${s.projectCount === 1 ? "project" : "projects"}`];
  const cards = s.uses
    .map((u) => {
      const loc = entryLoc(u.entry);
      const meta = [u.project.data.short || u.project.data.title, u.entry.date.getUTCFullYear(), loc && `${formatLoc(loc)} lines of code`].filter(Boolean);
      return (
        `<li><a class="skill-entry-card" href="${u.project.url}#${esc(entryId(u.entry))}">` +
        `<span class="skill-entry-meta">${meta.map(esc).join(" · ")}${u.best ? ` <span class="badge">Best example</span>` : ""}</span>` +
        `<strong>${esc(u.entry.data.title)}</strong>` +
        (u.entry.data.summary ? `<span class="skill-entry-summary">${esc(u.entry.data.summary)}</span>` : "") +
        `</a></li>`
      );
    })
    .join("");
  return (
    (s.description ? `<p class="skill-description">${esc(s.description)}</p>` : "") +
    `<p class="meta">${counts.map((c) => `<span>${c}</span>`).join("")}</p>` +
    `<ul class="skill-entry-cards">${cards}</ul>` +
    `<p class="bracket-links"><a href="/skills/${s.slug}/">Every entry in full</a></p>`
  );
}

// Everything search.js can find: the intro, projects, log entries, skill
// pages and publications. Only published things, since it's built from the
// same collections as the pages. Each result's `html` is what its card opens to.
export function searchIndex({ site, projects, entries, skills, publications }) {
  const items = [];
  items.push({
    type: "About",
    title: site.name,
    url: "/",
    text: [site.headline, ...(site.bio ?? [])].join(" "),
    html: cardRow(
      [site.headline, ...(site.bio ?? [])].map((t) => `<p>${esc(t)}</p>`).join("") + cardLinks(site.links),
      site.photo ? `<img src="${esc(site.photo)}" alt="Photo of ${esc(site.name)}" loading="lazy">` : ""
    ),
  });
  for (const p of projects) {
    items.push({
      type: "Project",
      title: p.data.title,
      context: p.data.org ?? "",
      url: p.url,
      text: [p.data.summary, plainText(p.templateContent), (p.data.tools ?? []).join(", ")].join(" "),
      html: projectCard(p, entries),
    });
  }
  for (const e of entries) {
    const project = projectOf(e, projects);
    if (!project) continue; // its project is still a draft
    items.push({
      type: "Log entry",
      title: e.data.title,
      context: project.data.title,
      url: `${project.url}#${entryId(e)}`,
      text: [plainText(e.templateContent), entrySkills(e, project).join(", "), ...entryInfo(e).map((f) => f.value)].join(" "),
      html: rebase(e.templateContent, project.url), // shown in full when its result is opened
    });
  }
  for (const s of skills) {
    items.push({
      type: "Skill",
      title: s.name,
      context: `${s.uses.length} ${s.uses.length === 1 ? "entry" : "entries"}`,
      url: `/skills/${s.slug}/`,
      text: [s.description, `Every log entry that shows ${s.name}.`].filter(Boolean).join(" "),
      html: skillCard(s),
    });
  }
  for (const pub of publications.filter((p) => !p.draft)) {
    const project = projects.find((p) => p.fileSlug === pub.project);
    const text = [
      `<p class="muted">${esc((pub.authors ?? []).join(", "))}</p>`,
      `<p>${esc([pub.venue, pub.status, pub.year].filter(Boolean).join(" · "))}${pub.award ? ` · ${esc(pub.award)}` : ""}</p>`,
      pub.tldr && `<p>${esc(pub.tldr)}</p>`,
      cardLinks(pub.links),
    ].filter(Boolean).join("");
    items.push({
      type: "Publication",
      title: pub.title,
      context: [pub.venue, pub.status, pub.year].filter(Boolean).join(" · "),
      url: project ? `${project.url}#pubs-title` : "/#publications",
      text: [(pub.authors ?? []).join(", "), pub.lab, pub.tldr].filter(Boolean).join(". "),
      html: cardRow(text, cardMedia(pub.image, pub.imageAlt || `Teaser for ${pub.title}`, pub.poster)),
    });
  }
  return items;
}
