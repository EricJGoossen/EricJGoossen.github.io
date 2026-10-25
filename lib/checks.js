// Build-time checks on the site's content and data files.
//
// Anything that would silently break a link or a page is an error and stops
// the build with a list of what to fix. Things that are fine for now but need
// attention later (a skill nothing uses yet, a large video) are warnings.
import fs from "node:fs";
import path from "node:path";
import { ENTRY_INFO, skillSlug } from "./skills.js";

const INPUT = "src";
const MAX_FILE_BYTES = 25 * 1024 * 1024; // Cloudflare rejects larger static files
const WARN_FILE_BYTES = 5 * 1024 * 1024;
const DATED_FILE = /^\d{4}-\d{2}-\d{2}-/;
const INFO_FIELDS = ENTRY_INFO.map(([key]) => key);
const INFO_MAX = 24; // characters per fact, so none wraps

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
  const resume = globals.resume ?? {};

  const projects = api.getFilteredByGlob(`${INPUT}/projects/*/index.md`);
  const entries = api.getFilteredByGlob(`${INPUT}/projects/*/log/*.md`);
  const projectSlugs = new Set(projects.map((p) => p.fileSlug));
  const draftProjects = new Set(projects.filter((p) => p.data.draft).map((p) => p.fileSlug));
  const skillNames = new Set(skills.map((s) => s.name));
  const hiddenSkills = new Set(skills.filter((s) => s.hidden).map((s) => s.name));

  // Log entries: dated filenames and unique anchors within each project.
  const entryIds = new Map(); // slug -> Set of entry ids
  const draftEntries = new Set(); // "slug/id" of entries marked draft
  const taggedSkills = new Map(); // "slug/id" -> its `skillTags`
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
    if (entry.data.skillTags !== undefined && !Array.isArray(entry.data.skillTags)) {
      errors.push(`${file}: "skillTags" must be a list, e.g. skillTags: [C++, SIMD]`);
    }
    for (const skill of Array.isArray(entry.data.skillTags) ? entry.data.skillTags : []) {
      if (hiddenSkills.has(skill)) {
        errors.push(`${file}: "${skill}" is a hidden skill; it isn't put in skillTags but listed in that skill's rank in src/_data/skills.json`);
      } else if (!skillNames.has(skill)) {
        errors.push(`${file}: uses skill "${skill}", which isn't in src/_data/skills.json. Add it there (same spelling).`);
      }
    }
    taggedSkills.set(`${slug}/${id}`, Array.isArray(entry.data.skillTags) ? [...entry.data.skillTags] : []);
    // Its line in the project's list of entries: a summary, and optionally featured with a short label.
    if (entry.data.summary !== undefined && isBlank(entry.data.summary)) errors.push(`${file}: "summary" is empty`);
    else if (entry.data.summary === undefined && !entry.data.draft) warnings.push(`${file}: no "summary" yet (one or two sentences for the project's list of entries)`);
    if (entry.data.featured !== undefined && typeof entry.data.featured !== "boolean") errors.push(`${file}: "featured" must be true or false`);
    if (entry.data.short !== undefined && (isBlank(entry.data.short) || entry.data.short.length > 24)) errors.push(`${file}: "short" must be a chip label of 1 or 2 words`);
    else if (entry.data.short === undefined && !entry.data.draft) warnings.push(`${file}: no "short" yet (1 or 2 words for its chip)`);
    // The PDF portfolio (lib/portfolio.js): `portfolio: true` includes it, and
    // `portfolioImage:` picks its image (else its first image or video still).
    if (entry.data.portfolio !== undefined && typeof entry.data.portfolio !== "boolean") errors.push(`${file}: "portfolio" must be true or false`);
    if (entry.data.portfolioImage && !exists(mediaFile(path.dirname(path.dirname(entry.inputPath)), entry.data.portfolioImage))) {
      errors.push(`${file}: portfolioImage "${entry.data.portfolioImage}" not found`);
    }
    // An entry's basic facts (shown under its links): known fields, each text or a list of text.
    if (entry.data.info !== undefined) {
      const info = entry.data.info;
      if (!info || typeof info !== "object" || Array.isArray(info)) {
        errors.push(`${file}: "info" must be fields like language: C++ and role: Solo`);
      } else {
        for (const [key, value] of Object.entries(info)) {
          if (!INFO_FIELDS.includes(key)) errors.push(`${file}: info has an unknown field "${key}" (use ${INFO_FIELDS.join(", ")})`);
          const ok = typeof value === "string" || (Array.isArray(value) && value.every((v) => typeof v === "string"));
          if (!ok) errors.push(`${file}: info.${key} must be text or a list of text`);
          else if ([value].flat().join(", ").length > INFO_MAX) {
            errors.push(`${file}: info.${key} is longer than ${INFO_MAX} characters; keep it short enough for one line ("Solo", "On the robot")`);
          }
        }
      }
    } else if (!entry.data.draft) {
      warnings.push(`${file}: no "info" yet (language, tools, hardware, role, status)`);
    }
    // An entry's links (shown under its title): a list of { label, url }.
    if (entry.data.links !== undefined) {
      if (!Array.isArray(entry.data.links)) {
        errors.push(`${file}: "links" must be a list of { label, url }`);
      } else {
        for (const link of entry.data.links) {
          if (!link || !link.label || !link.url) errors.push(`${file}: every link needs a label and a url`);
        }
      }
    }
  }

  // Projects: required fields and media files.
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
    if (data.portfolio !== undefined && typeof data.portfolio !== "boolean") errors.push(`${file}: "portfolio" must be true or false`);
    for (const field of ["cover", "hero", "coverPoster", "heroPoster", "portfolioImage"]) {
      if (data[field] && !exists(mediaFile(dir, data[field]))) {
        errors.push(`${file}: ${field} "${data[field]}" not found (looked for ${rel(mediaFile(dir, data[field]))})`);
      }
    }
    for (const link of data.links ?? []) {
      if (isBlank(link.label) || isBlank(link.url)) errors.push(`${file}: every link needs a "label" and a "url"`);
    }

    if (data.highlights !== undefined) {
      errors.push(`${file}: "highlights" was replaced: mark an entry "featured: true" (with a "short" label) and put its skills in its "skillTags"`);
    }
  }

  // Skills: unique names and page URLs, and a `rank` of exactly the entries tagged with the skill
  // (for a hidden skill, the rank is the tagging: no chip, no tag on entries, only its page).
  const seen = new Set();
  const slugs = new Map();
  for (const skill of skills) {
    if (isBlank(skill.name)) {
      errors.push(`src/_data/skills.json: every skill needs a "name"`);
      continue;
    }
    const key = skill.name.toLowerCase();
    if (seen.has(key)) errors.push(`src/_data/skills.json: "${skill.name}" is listed twice`);
    seen.add(key);
    const slug = skillSlug(skill.name);
    if (slugs.has(slug)) {
      errors.push(`src/_data/skills.json: "${skill.name}" and "${slugs.get(slug)}" would share the page /skills/${slug}/. Rename one.`);
    }
    slugs.set(slug, skill.name);

    if (skill.hidden !== undefined && typeof skill.hidden !== "boolean") errors.push(`src/_data/skills.json: "${skill.name}" hidden must be true or false`);
    if (isBlank(skill.description)) warnings.push(`skills.json: "${skill.name}" has no "description" (shown at the top of its page)`);
    // A hidden skill is tagged by its rank alone; a visible one by entries' skillTags.
    const usedBy = skill.hidden
      ? (skill.rank ?? []).filter((key) => taggedSkills.has(key))
      : [...taggedSkills].filter(([, list]) => list.includes(skill.name)).map(([k]) => k);
    if (skill.best !== undefined) errors.push(`src/_data/skills.json: "${skill.name}" uses "best"; list its entries in "rank" instead (the first is the best example)`);
    if (skill.rank !== undefined && !Array.isArray(skill.rank)) {
      errors.push(`src/_data/skills.json: "${skill.name}" rank must be a list of "<project folder>/<entry>"`);
    } else {
      const rank = skill.rank ?? [];
      for (const key of rank) {
        if (!taggedSkills.has(key)) {
          errors.push(`src/_data/skills.json: "${skill.name}" rank lists "${key}", which isn't a log entry (use "<project folder>/<entry>")`);
        } else if (!skill.hidden && !taggedSkills.get(key).includes(skill.name)) {
          errors.push(`src/_data/skills.json: "${skill.name}" rank lists "${key}", which isn't tagged with "${skill.name}" (in its skillTags)`);
        }
      }
      if (new Set(rank).size !== rank.length) errors.push(`src/_data/skills.json: "${skill.name}" rank lists an entry twice`);
      // Every published entry with this skill has a fixed place on its page.
      for (const key of usedBy) {
        const published = !draftEntries.has(key) && !draftProjects.has(key.split("/")[0]);
        if (published && !rank.includes(key)) {
          errors.push(`src/_data/skills.json: "${key}" is tagged with "${skill.name}" but isn't in its rank; add it where it belongs (first = best example)`);
        }
      }
    }
    if (!usedBy.length) warnings.push(`skills.json: "${skill.name}" isn't on any log entry yet, so it has no page and is hidden on the home page`);
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

  if (resume.preview && !exists(path.join(INPUT, resume.preview))) {
    errors.push(`src/_data/resume.json: preview "${resume.preview}" not found (paths start at src/)`);
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
