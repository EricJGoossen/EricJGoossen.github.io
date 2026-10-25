// Skill pages and the search index, both built from the same published
// projects, log entries and highlights the rest of the site uses.

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
export const highlightOf = (entry, project) => (project?.data.highlights ?? []).find((h) => h.entry === entryId(entry));

// An entry's skills: those on its highlight (if it has one) plus its own
// `skillTags:` list, for entries worth tagging that aren't highlights.
export const entrySkills = (entry, project) => [
  ...new Set([...(highlightOf(entry, project)?.skills ?? []), ...(entry.data.skillTags ?? [])]),
];

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

// One page per skill: every published log entry tagged with it, its `best`
// example first and the rest newest first. A skill on no entry yet gets no
// page (and no chip on the home page).
export function skillPages(skills, projects, entries) {
  return skills
    .map((skill) => {
      const uses = [];
      for (const entry of entries) {
        const project = projectOf(entry, projects);
        if (!project) continue; // its project is still a draft
        const tags = entrySkills(entry, project);
        if (!tags.includes(skill.name)) continue;
        const key = `${project.fileSlug}/${entryId(entry)}`;
        const label = highlightOf(entry, project)?.label ?? entry.data.title;
        uses.push({ key, project, entry, label, otherSkills: tags.filter((t) => t !== skill.name), best: key === skill.best });
      }
      uses.sort((a, b) => b.best - a.best || b.entry.date - a.entry.date);
      const projectCount = new Set(uses.map((u) => u.project)).size;
      return { name: skill.name, slug: skillSlug(skill.name), uses, projectCount };
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

// Everything search.js can find: the intro, projects, log entries, skill
// pages and publications. Only published things, since it's built from the
// same collections as the pages.
export function searchIndex({ site, projects, entries, skills, publications }) {
  const items = [];
  items.push({ type: "About", title: site.name, url: "/", text: [site.headline, ...(site.bio ?? [])].join(" ") });
  for (const p of projects) {
    items.push({
      type: "Project",
      title: p.data.title,
      context: p.data.org ?? "",
      url: p.url,
      text: [p.data.summary, plainText(p.templateContent), (p.data.tools ?? []).join(", ")].join(" "),
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
      text: `Every log entry that shows ${s.name}.`,
    });
  }
  for (const pub of publications.filter((p) => !p.draft)) {
    const project = projects.find((p) => p.fileSlug === pub.project);
    items.push({
      type: "Publication",
      title: pub.title,
      context: [pub.venue, pub.status, pub.year].filter(Boolean).join(" · "),
      url: project ? `${project.url}#pubs-title` : "/#publications",
      text: [(pub.authors ?? []).join(", "), pub.lab, pub.tldr].filter(Boolean).join(". "),
    });
  }
  return items;
}
