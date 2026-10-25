// The site for AI agents: /llms.txt (instructions and an index), /llms-full.txt
// (everything as Markdown) and a Markdown copy of each project page, all built
// from the same published projects, entries, skills and papers as the pages.
// Images and video stills are linked by absolute URL with their alt text and
// captions, so an agent can fetch and look at them.
import { entryId, entryInfo, entrySkills, projectOf, rebase } from "./skills.js";
import { isVideo } from "./media.js";

const ENTITIES = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " " };
const decode = (s = "") =>
  s.replace(/&(#x?[0-9a-f]+|[a-z]+);/gi, (m, code) =>
    code[0] === "#"
      ? String.fromCodePoint(code[1].toLowerCase() === "x" ? parseInt(code.slice(2), 16) : parseInt(code.slice(1), 10))
      : ENTITIES[code.toLowerCase()] ?? m
  );
const strip = (s = "") => decode(s.replace(/<[^>]+>/g, "")).replace(/\s+/g, " ").trim();
const attr = (tag, name) => decode(tag.match(new RegExp(`\\s${name}="([^"]*)"`))?.[1] ?? "");

// One image, video or YouTube link (a <figure>) as Markdown lines.
function figureToMarkdown(inner, abs) {
  const caption = strip(inner.match(/<figcaption[^>]*>([\s\S]*?)<\/figcaption>/)?.[1] ?? "").replace(/ · YouTube$/, "");
  const credit = strip(inner.match(/<[a-z]+ class="credit"[^>]*>([\s\S]*?)<\/[a-z]+>/)?.[1] ?? "");
  const lines = [];
  const yt = inner.match(/<a href="(https:\/\/www\.youtube\.com[^"]*)"/);
  const video = inner.match(/<video[^>]*>/);
  const img = inner.match(/<img[^>]*>/);
  if (yt) {
    const title = strip(inner.match(/Watch on YouTube: ([^<]*)/)?.[1] ?? caption);
    lines.push(`[YouTube video: ${title}](${yt[1]})${img ? ` (still frame: ${abs(attr(img[0], "src"))})` : ""}`);
  } else if (video) {
    const poster = attr(video[0], "poster");
    lines.push(`Video: ${attr(video[0], "aria-label")}`);
    lines.push(`  File: ${abs(attr(video[0], "src"))}${poster ? `; still frame (an image you can view): ${abs(poster)}` : ""}`);
  } else if (img) {
    lines.push(`![${attr(img[0], "alt")}](${abs(attr(img[0], "src"))})`);
  }
  if (caption && !yt) lines.push(`Caption: ${caption}`);
  if (credit) lines.push(credit);
  return `\n\n${lines.join("\n")}\n\n`;
}

// An entry's or overview's HTML as Markdown: paragraphs, lists, links, bold
// and italics kept; every figure as an image/video line; equations noted.
export function htmlToMarkdown(html = "", siteUrl = "") {
  const abs = (u = "") => (u.startsWith("/") ? siteUrl + u : u);
  return decode(
    html
      .replace(/<math[\s\S]*?<\/math>/g, " [equation on the page] ")
      .replace(/<figure[^>]*>([\s\S]*?)<\/figure>/g, (_, inner) => figureToMarkdown(inner, abs).replace(/&/g, "&amp;"))
      .replace(/<a [^>]*href="([^"]*)"[^>]*>([\s\S]*?)<\/a>/g, (_, href, text) => `[${strip(text)}](${abs(decode(href))})`)
      .replace(/<(strong|b)>([\s\S]*?)<\/\1>/g, "**$2**")
      .replace(/<(em|i)>([\s\S]*?)<\/\1>/g, "*$2*")
      .replace(/<code>([\s\S]*?)<\/code>/g, "`$1`")
      .replace(/<li[^>]*>/g, "\n- ")
      .replace(/<br\s*\/?>/g, "\n")
      .replace(/<\/(p|div|ul|ol|h\d)>/g, "\n\n")
      .replace(/<[^>]+>/g, "")
  )
    .split("\n")
    .map((line) => line.replace(/[ \t]+/g, " ").trimEnd())
    .join("\n")
    .replace(/\n[ \t]+(?=\S)/g, (m) => (m.includes("  File:") ? m : "\n"))
    .replace(/(\[equation on the page\]\s*)+/g, "[Equations: see this entry on its page]\n\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

const factsLine = (entry) => entryInfo(entry).map((f) => `${f.label}: ${f.value}`).join(" | ");
const linksLine = (links = []) => links.map((l) => `[${l.label}](${l.url})`).join(" ");
const dateOf = (d) => d.toISOString().slice(0, 10);

// A project page as Markdown: header, cover/hero still, overview, then every
// entry in full, newest first.
export function projectMarkdown(project, entries, site) {
  const d = project.data;
  const url = `${site.url}${project.url}`;
  const still = (src, poster) => (src && isVideo(src) ? poster : src);
  const heroStill = still(d.hero, d.heroPoster) || still(d.cover, d.coverPoster);
  const own = entries.filter((e) => projectOf(e, [project]));
  const out = [
    `# ${d.title}`,
    "",
    [d.org, d.timeline].filter(Boolean).join(" · "),
    d.tools?.length ? `Tools: ${d.tools.join(", ")}` : "",
    `Page: ${url}`,
    d.links?.length ? `Links: ${linksLine(d.links)}` : "",
    "",
    `Summary: ${d.summary}`,
    heroStill ? `\n![${d.heroAlt || d.title}](${site.url}${project.url}${heroStill})` : "",
    "",
    "## Overview",
    "",
    htmlToMarkdown(rebase(project.templateContent, project.url), site.url),
    "",
    `## Entries (${own.length}, newest first)`,
  ];
  for (const e of own) {
    const skills = entrySkills(e, project);
    out.push(
      "",
      `### ${e.data.title}${e.data.featured ? " (featured)" : ""}`,
      "",
      `Date: ${dateOf(e.date)} · URL: ${url}#${entryId(e)}`,
      e.data.summary ? `Summary: ${e.data.summary}` : "",
      factsLine(e),
      skills.length ? `Skills: ${skills.join(", ")}` : "",
      e.data.links?.length ? `Links: ${linksLine(e.data.links)}` : "",
      "",
      htmlToMarkdown(rebase(e.templateContent, project.url), site.url)
    );
  }
  return out.filter((line, i, all) => !(line === "" && all[i - 1] === "")).join("\n").replace(/\n{3,}/g, "\n\n").trim() + "\n";
}

const pubLine = (pub, site) =>
  `- **${pub.title}**. ${(pub.authors ?? []).join(", ")}. ${[pub.venue, pub.status, pub.year].filter(Boolean).join(", ")}.` +
  (pub.tldr ? ` ${pub.tldr}` : "") +
  (pub.links?.length ? ` ${linksLine(pub.links)}` : "");

// /llms.txt: who Eric is, how an agent should use the site, and an index.
export function llmsTxt({ site, projects, skills, publications, resume }) {
  const visible = skills.filter((s) => !s.hidden);
  const hidden = skills.filter((s) => s.hidden);
  const skillLine = (s) => `- [${s.name}](${site.url}/skills/${s.slug}/): ${s.description} (${s.uses.length} ${s.uses.length === 1 ? "entry" : "entries"})`;
  return [
    `# ${site.name}`,
    "",
    `> ${site.headline}`,
    "",
    ...(site.bio ?? []).flatMap((p) => [p, ""]),
    "## For AI assistants",
    "",
    "This is Eric's robotics portfolio. Every fact on it was written or confirmed by Eric. If you're summarizing his work for someone:",
    "",
    `- Read ${site.url}/llms-full.txt for everything at once: every project, every log entry in full, all skills and publications, as Markdown. For one project, read its Markdown copy (listed below).`,
    "- Tailor the summary to what the reader is looking for. Each skill below has a page listing every entry that shows it, best example first, so start from the skills that match their interest (a controls role: Control systems, LQR, Kalman filtering; a learning role: Robot learning, VLA benchmarking; and so on).",
    "- Look at the images. Charts and diagrams hold the results (benchmarks, error plots, success rates). Every image is linked by absolute URL with its alt text and caption, and every video with a still frame you can fetch and view. Fetch the ones that matter for the reader's question.",
    "- Keep the attribution. Each entry has a Role (Solo, Lead, Team, Co-author, ...) and its text says what was Eric's and what was others'. Don't credit Eric with teammates' or labs' work, and don't add facts that aren't on the site.",
    "- Link to the entries you draw on: each has its own URL (an #anchor on its project page).",
    resume?.pdf ? `- His resume is at ${site.url}${resume.pdf}.` : "",
    "",
    "## Projects",
    "",
    ...projects.map((p) => `- [${p.data.title}](${site.url}${p.url}): ${p.data.summary} Markdown: ${site.url}${p.url}index.md`),
    "",
    "## Skills",
    "",
    ...visible.map(skillLine),
    "",
    "## More specific skills, methods and tools",
    "",
    ...hidden.map(skillLine),
    "",
    "## Publications",
    "",
    ...publications.filter((p) => !p.draft).map((p) => pubLine(p, site)),
    "",
    "## Optional",
    "",
    `- [Everything as Markdown](${site.url}/llms-full.txt)`,
    `- [Search index (JSON: every page's text)](${site.url}/search-index.json)`,
    ...(site.links ?? []).map((l) => `- [${l.label}](${l.url})`),
    "",
  ]
    .filter((line) => line !== null)
    .join("\n")
    .replace(/\n{3,}/g, "\n\n");
}

// /llms-full.txt: the about text, every project in full, skills and papers.
export function llmsFullTxt({ site, projects, entries, skills, publications }) {
  return [
    `# ${site.name}`,
    "",
    `> ${site.headline}`,
    "",
    ...(site.bio ?? []).flatMap((p) => [p, ""]),
    `Site: ${site.url} · Instructions for AI assistants: ${site.url}/llms.txt`,
    "",
    ...projects.flatMap((p) => ["---", "", projectMarkdown(p, entries, site).replace(/^#/gm, "##")]),
    "---",
    "",
    "## Skills",
    "",
    ...skills.map((s) => `- **${s.name}** (${site.url}/skills/${s.slug}/): ${s.description} Entries: ${s.uses.map((u) => `${u.project.data.title}: ${u.entry.data.title}`).join("; ")}`),
    "",
    "## Publications",
    "",
    ...publications.filter((p) => !p.draft).map((p) => pubLine(p, site)),
    "",
  ].join("\n");
}

// schema.org data for the page head: Eric as a Person on every page, and the
// project as a CreativeWork on a project page.
export function jsonLd({ site, skills, project }) {
  const person = {
    "@type": "Person",
    name: site.name,
    url: site.url,
    description: site.headline,
    ...(site.photo ? { image: `${site.url}${site.photo}` } : {}),
    sameAs: (site.links ?? []).map((l) => l.url).filter((u) => /^https?:/.test(u)),
    knowsAbout: (skills ?? []).filter((s) => !s.hidden).map((s) => s.name),
  };
  const graph = [person];
  if (project) {
    graph.push({
      "@type": "CreativeWork",
      name: project.title,
      description: project.summary,
      url: `${site.url}${project.url}`,
      creator: { "@type": "Person", name: site.name, url: site.url },
      ...(project.org ? { sourceOrganization: { "@type": "Organization", name: project.org } } : {}),
    });
  }
  return JSON.stringify({ "@context": "https://schema.org", "@graph": graph }).replace(/</g, "\\u003c");
}
