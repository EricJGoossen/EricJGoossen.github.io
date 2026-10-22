// Build-time checks on the site's content and data files.
//
// Anything that would silently break a link or a page is an error and stops
// the build with a list of what to fix. Things that are fine for now but need
// attention later (a skill nothing uses yet, a large video) are warnings.
import fs from "node:fs";
import path from "node:path";

const INPUT = "src";
const MAX_FILE_BYTES = 25 * 1024 * 1024; // Cloudflare rejects larger static files
const WARN_FILE_BYTES = 5 * 1024 * 1024;
const DATED_FILE = /^\d{4}-\d{2}-\d{2}-/;

const exists = (file) => fs.existsSync(file);
const isBlank = (value) => typeof value !== "string" || value.trim() === "";
const rel = (file) => path.relative(".", file);

// A media path from front matter: "images/x.jpg" is relative to the project
// folder, "/projects/x/images/y.jpg" is relative to src/.
function mediaFile(projectDir, src) {
  return src.startsWith("/") ? path.join(INPUT, src) : path.join(projectDir, src);
}

function walk(dir, files = []) {
  if (!exists(dir)) return files;
  for (const name of fs.readdirSync(dir)) {
    const file = path.join(dir, name);
    if (fs.statSync(file).isDirectory()) walk(file, files);
    else files.push(file);
  }
  return files;
}

export function checkSite(api) {
  const errors = [];
  const warnings = [];
  const all = api.getAll();
  const globals = all[0]?.data ?? {};
  const skills = globals.skills ?? [];
  const publications = globals.publications ?? [];
  const site = globals.site ?? {};

  const projects = api.getFilteredByGlob(`${INPUT}/projects/*/index.md`);
  const entries = api.getFilteredByGlob(`${INPUT}/projects/*/log/*.md`);
  const projectSlugs = new Set(projects.map((p) => p.fileSlug));
  const skillNames = new Set(skills.map((s) => s.name));

  // Log entries: dated filenames and unique anchors within each project.
  const entryIds = new Map(); // slug -> Set of entry ids
  const draftEntries = new Set(); // "slug/id" of entries marked draft
  for (const entry of entries) {
    const file = rel(entry.inputPath);
    const slug = entry.inputPath.split("/projects/")[1].split("/")[0];
    const id = entry.data.id ?? entry.fileSlug;
    if (!DATED_FILE.test(path.basename(entry.inputPath))) {
      errors.push(`${file}: log file names must start with a date, e.g. 2026-10-21-${id}.md`);
    }
    if (isBlank(entry.data.title)) errors.push(`${file}: missing "title" in the front matter`);
    if (!entryIds.has(slug)) entryIds.set(slug, new Set());
    if (entryIds.get(slug).has(id)) {
      errors.push(`${file}: another log entry in ${slug} already uses the anchor "${id}". Rename one of them.`);
    }
    entryIds.get(slug).add(id);
    if (entry.data.draft) draftEntries.add(`${slug}/${id}`);
  }

  // Projects: required fields, media files, highlights pointing at real entries and known skills.
  const highlightSkills = new Map(); // "slug/entry" -> skills on that highlight
  for (const project of projects) {
    const file = rel(project.inputPath);
    const slug = project.fileSlug;
    const dir = path.dirname(project.inputPath);
    const data = project.data;

    for (const field of ["title", "summary"]) {
      if (isBlank(data[field])) errors.push(`${file}: missing "${field}" in the front matter`);
    }
    if (data.order !== undefined && typeof data.order !== "number") {
      errors.push(`${file}: "order" must be a number`);
    }
    for (const field of ["cover", "hero", "coverPoster", "heroPoster"]) {
      if (data[field] && !exists(mediaFile(dir, data[field]))) {
        errors.push(`${file}: ${field} "${data[field]}" not found (looked for ${rel(mediaFile(dir, data[field]))})`);
      }
    }
    for (const link of data.links ?? []) {
      if (isBlank(link.label) || isBlank(link.url)) errors.push(`${file}: every link needs a "label" and a "url"`);
    }

    const ids = entryIds.get(slug) ?? new Set();
    for (const h of data.highlights ?? []) {
      if (isBlank(h.label) || isBlank(h.entry)) {
        errors.push(`${file}: every highlight needs a "label" and an "entry"`);
        continue;
      }
      if (!ids.has(h.entry)) {
        errors.push(
          `${file}: highlight "${h.label}" points at entry "${h.entry}", but there's no log/YYYY-MM-DD-${h.entry}.md in ${slug}`
        );
      } else if (!data.draft && draftEntries.has(`${slug}/${h.entry}`)) {
        errors.push(`${file}: highlight "${h.label}" points at entry "${h.entry}", which is a draft. Publish the entry or mark the project draft.`);
      }
      for (const skill of h.skills ?? []) {
        if (!skillNames.has(skill)) {
          errors.push(`${file}: highlight "${h.label}" uses skill "${skill}", which isn't in src/_data/skills.json. Add it there (same spelling).`);
        }
      }
      highlightSkills.set(`${slug}/${h.entry}`, h.skills ?? []);
    }
  }

  // Skills: unique names, and `best` must be a highlight that actually lists the skill.
  const seen = new Set();
  for (const skill of skills) {
    if (isBlank(skill.name)) {
      errors.push(`src/_data/skills.json: every skill needs a "name"`);
      continue;
    }
    const key = skill.name.toLowerCase();
    if (seen.has(key)) errors.push(`src/_data/skills.json: "${skill.name}" is listed twice`);
    seen.add(key);

    const usedBy = [...highlightSkills].filter(([, list]) => list.includes(skill.name)).map(([k]) => k);
    if (skill.best) {
      if (!highlightSkills.has(skill.best)) {
        errors.push(`src/_data/skills.json: "${skill.name}" best "${skill.best}" isn't a highlight (use "<project folder>/<entry>")`);
      } else if (!highlightSkills.get(skill.best).includes(skill.name)) {
        errors.push(`src/_data/skills.json: "${skill.name}" best "${skill.best}" doesn't list "${skill.name}" in its skills`);
      }
    }
    if (!usedBy.length) warnings.push(`skills.json: "${skill.name}" isn't used by any highlight yet, so it's hidden on the home page`);
  }

  // Publications: required fields, real project, teaser file present.
  publications.forEach((pub, i) => {
    const where = `src/_data/publications.json (entry ${i + 1}${pub.title ? `, "${pub.title}"` : ""})`;
    if (isBlank(pub.title)) errors.push(`${where}: missing "title"`);
    if (!Array.isArray(pub.authors) || !pub.authors.length) errors.push(`${where}: "authors" must be a non-empty list`);
    else if (!pub.authors.some((a) => (site.authorNames ?? []).includes(a))) {
      warnings.push(`${where}: no author matches site.json "authorNames", so Eric won't be bolded`);
    }
    if (pub.project && !projectSlugs.has(pub.project)) {
      errors.push(`${where}: "project" is "${pub.project}", but there's no src/projects/${pub.project}/`);
    }
    for (const field of ["image", "poster"]) {
      if (pub[field] && !exists(path.join(INPUT, pub[field]))) {
        errors.push(`${where}: ${field} "${pub[field]}" not found (paths start at src/, e.g. /projects/hil-cap/images/teaser.jpg)`);
      }
    }
    for (const link of pub.links ?? []) {
      if (isBlank(link.label) || isBlank(link.url)) errors.push(`${where}: every link needs a "label" and a "url"`);
    }
  });

  // Site-wide images.
  for (const field of ["photo", "ogImage"]) {
    if (site[field] && !exists(path.join(INPUT, site[field]))) {
      errors.push(`src/_data/site.json: ${field} "${site[field]}" not found (paths start at src/)`);
    }
  }

  // File sizes: Cloudflare won't deploy files over 25 MiB.
  for (const file of [...walk(`${INPUT}/projects`), ...walk(`${INPUT}/assets`)]) {
    const size = fs.statSync(file).size;
    const mb = (size / 1024 / 1024).toFixed(1);
    if (size > MAX_FILE_BYTES) errors.push(`${rel(file)}: ${mb} MB is over Cloudflare's 25 MB per-file limit. Compress it (see AGENTS.md).`);
    else if (size > WARN_FILE_BYTES) warnings.push(`${rel(file)}: ${mb} MB, consider compressing it (see AGENTS.md)`);
  }

  return { errors, warnings };
}
