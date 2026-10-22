// Adds a progress log entry to a project.
// Usage: node scripts/new-entry.js <project-folder> "Entry title" [YYYY-MM-DD]
//   e.g. npm run new:entry -- opendubs "SIMD optimization"
// The anchor (used by highlights and skill links) is made from the title.
import fs from "node:fs";
import path from "node:path";

const [slug, title, date = new Date().toISOString().slice(0, 10)] = process.argv.slice(2);
if (!slug || !title) {
  console.error('Usage: npm run new:entry -- <project-folder> "Entry title" [YYYY-MM-DD]');
  process.exit(1);
}
const logDir = path.join("src/projects", slug, "log");
if (!fs.existsSync(path.join("src/projects", slug, "index.md"))) {
  const known = fs.readdirSync("src/projects").filter((n) => fs.existsSync(path.join("src/projects", n, "index.md")));
  console.error(`No project "${slug}". Projects: ${known.join(", ")}`);
  process.exit(1);
}
if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
  console.error(`Date must look like 2026-10-21, got "${date}"`);
  process.exit(1);
}

// Anchor from the title; add -2, -3... if the project already has one by that name.
const base = title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "entry";
fs.mkdirSync(logDir, { recursive: true });
const taken = new Set(fs.readdirSync(logDir).map((name) => name.replace(/^\d{4}-\d{2}-\d{2}-/, "").replace(/\.md$/, "")));
let id = base;
for (let n = 2; taken.has(id); n++) id = `${base}-${n}`;

const file = path.join(logDir, `${date}-${id}.md`);
fs.writeFileSync(
  file,
  `---
title: ${JSON.stringify(title)}
---
What you did, what was hard, and how it turned out.

{#- Images and videos go in the project's images/ folder. Usually each paragraph
gets one, beside it:
{% row "images/my-chart.svg", "What the image shows", { caption: "Optional" } %}
The paragraph.
{% endrow %}
Other examples:
![What the image shows](images/my-photo.jpg)
{% video "images/my-clip.mp4", "What the clip shows" %}
{% youtube "VIDEO_ID", "What the video shows" %}
This note is a template comment and never shows on the site. Delete it when done. -#}
`
);

console.log(`Created ${file}
Anchor: #${id}  (link: /projects/${slug}/#${id})
To make it a highlight, add to highlights in src/projects/${slug}/index.md:
  - label: ${title}
    entry: ${id}
    skills: [...]`);
