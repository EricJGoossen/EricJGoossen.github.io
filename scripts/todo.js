// Lists everything on the site that is still placeholder content, grouped by file,
// so filling in real content is a checklist instead of a hunt.
// Usage: node scripts/todo.js   (or npm run todo)
import fs from "node:fs";
import path from "node:path";

const items = new Map(); // file -> list of things to do
const add = (file, text) => {
  if (!items.has(file)) items.set(file, []);
  items.get(file).push(text);
};

function walk(dir, files = []) {
  for (const name of fs.readdirSync(dir)) {
    const file = path.join(dir, name);
    if (fs.statSync(file).isDirectory()) walk(file, files);
    else files.push(file);
  }
  return files;
}

// Placeholder text, placeholder images and "#" links in content and data files.
const contentFiles = walk("src").filter((f) => /\.(md|json)$/.test(f));
for (const file of contentFiles) {
  fs.readFileSync(file, "utf8")
    .split("\n")
    .forEach((line, i) => {
      const where = `line ${i + 1}`;
      const image = line.match(/{%\s*placeholder\s+"([^"]*)"/);
      if (image) add(file, `${where}: placeholder image "${image[1]}"`);
      else if (/placeholder/i.test(line)) add(file, `${where}: ${line.trim().slice(0, 100)}`);
      if (/(url|"url")\s*:\s*"#"/.test(line)) add(file, `${where}: link goes nowhere yet ("#")`);
      if (/^#\s*(cover|hero):/.test(line)) add(file, `${where}: no ${line.match(/(cover|hero)/)[1]} image yet`);
      if (/^draft:\s*true/.test(line)) add(file, `${where}: draft, hidden from the site until this line is removed`);
    });
}

// Files the site expects but that don't exist yet.
const site = JSON.parse(fs.readFileSync("src/_data/site.json", "utf8"));
const resume = JSON.parse(fs.readFileSync("src/_data/resume.json", "utf8"));
const publications = JSON.parse(fs.readFileSync("src/_data/publications.json", "utf8"));
if (resume.pdf && !fs.existsSync(`src${resume.pdf}`)) {
  add("src/assets/", `${resume.pdf} is missing (Resume links stay hidden until it exists)`);
}
if (!site.photo) add("src/_data/site.json", `no "photo" yet (the intro shows without one)`);
if (!site.ogImage) add("src/_data/site.json", `no "ogImage" yet (home page link previews have no image)`);
publications.forEach((pub) => {
  if (pub.draft) add("src/_data/publications.json", `"${pub.title}": draft, hidden from the site`);
  if (!pub.image) add("src/_data/publications.json", `"${pub.title}": no teaser "image" yet (shows as a text-only card)`);
});

let total = 0;
for (const [file, list] of [...items].sort(([a], [b]) => a.localeCompare(b))) {
  console.log(`\n${file}`);
  for (const text of list) console.log(`  - ${text}`);
  total += list.length;
}
console.log(total ? `\n${total} things still to fill in.` : "Nothing left to fill in.");
