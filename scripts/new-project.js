// Creates a new project page with a first log entry, ready to fill in.
// Usage: node scripts/new-project.js <folder-name> "Title" ["Lab or org"]
//   e.g. npm run new:project -- mujoco-hand "Dexterous Hand" "WEIRD Lab"
// The folder name becomes the URL: /projects/<folder-name>/
import fs from "node:fs";
import path from "node:path";

const [slug, title, org = ""] = process.argv.slice(2);
if (!slug || !title) {
  console.error('Usage: npm run new:project -- <folder-name> "Title" ["Lab or org"]');
  process.exit(1);
}
if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(slug)) {
  console.error(`"${slug}" isn't a valid folder name. Use lowercase letters, numbers and dashes, e.g. mujoco-hand`);
  process.exit(1);
}
const dir = path.join("src/projects", slug);
if (fs.existsSync(dir)) {
  console.error(`${dir} already exists.`);
  process.exit(1);
}

// New projects go last; change `order` to move them.
const orders = fs
  .readdirSync("src/projects")
  .map((name) => path.join("src/projects", name, "index.md"))
  .filter((file) => fs.existsSync(file))
  .map((file) => Number(fs.readFileSync(file, "utf8").match(/^order:\s*(\d+)/m)?.[1] ?? 0));
const order = Math.max(0, ...orders) + 1;
const today = new Date().toISOString().slice(0, 10);
const q = JSON.stringify; // quoted strings are always valid YAML

fs.mkdirSync(path.join(dir, "log"), { recursive: true });
fs.mkdirSync(path.join(dir, "images"));
fs.writeFileSync(path.join(dir, "images/.gitkeep"), "");
fs.writeFileSync(
  path.join(dir, "index.md"),
  `---
layout: project.njk
draft: true   # hidden from the site until this line is removed
title: ${q(title)}
org: ${q(org)}
timeline: Placeholder timeline
tools: [Placeholder tool]
order: ${order}
summary: ${q(`Placeholder one-line summary of ${title}.`)}
# cover: images/cover.jpg   # tile image (or .mp4) on the home page
# hero: images/hero.jpg     # big image (or .mp4) at the top of this page
links: []
#  - label: GitHub
#    url: https://github.com/...
---
Placeholder overview of ${title}. What the project is, why it matters, your role, and the headline result, in one short paragraph.
`
);
fs.writeFileSync(
  path.join(dir, "log", `${today}-kickoff.md`),
  `---
title: Project kickoff
---
Placeholder log entry. What the problem was and how you planned to attack it.
`
);

console.log(`Created ${dir}/ as a draft (order ${order}). Remove "draft: true" from index.md to publish it.
Next: fill in ${dir}/index.md, add images to ${dir}/images/, and add log entries with
  npm run new:entry -- ${slug} "What happened"`);
