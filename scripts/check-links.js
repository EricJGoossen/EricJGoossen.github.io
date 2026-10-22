// Checks every internal link, image/video source and #anchor in the built site.
// Usage: node scripts/check-links.js [_site]   (run after a build; `npm run check` does both)
// Exits 1 if anything points at a missing page, file or anchor.
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(process.argv[2] ?? "_site");
if (!fs.existsSync(root)) {
  console.error(`No build output at ${root}. Run the build first.`);
  process.exit(1);
}

const files = [];
(function walk(dir) {
  for (const name of fs.readdirSync(dir)) {
    const file = path.join(dir, name);
    if (fs.statSync(file).isDirectory()) walk(file);
    else files.push(file);
  }
})(root);
const pages = files.filter((f) => f.endsWith(".html"));

// Every id on every page, so #anchors can be checked.
const ids = new Map();
for (const page of pages) {
  const html = fs.readFileSync(page, "utf8");
  ids.set(page, new Set([...html.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1])));
}

function targetFile(urlPath) {
  const file = path.join(root, decodeURIComponent(urlPath));
  if (urlPath.endsWith("/")) return path.join(file, "index.html");
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) return path.join(file, "index.html");
  return file;
}

let checked = 0;
let placeholders = 0;
const broken = [];
for (const page of pages) {
  const html = fs.readFileSync(page, "utf8");
  const pageUrl = "/" + path.relative(root, page).replace(/index\.html$/, "");
  for (const [, url] of html.matchAll(/\s(?:href|src|poster)="([^"]*)"/g)) {
    if (/^(https?:|mailto:|tel:|data:)/.test(url)) continue;
    checked++;
    if (url === "#") {
      placeholders++;
      continue;
    }
    const [urlPath, hash] = url.split("#");
    const base = pageUrl.endsWith("/") ? pageUrl : path.posix.dirname(pageUrl) + "/";
    const absolute = urlPath === "" ? pageUrl : urlPath.startsWith("/") ? urlPath : path.posix.join(base, urlPath);
    const target = targetFile(absolute);
    if (!fs.existsSync(target)) broken.push(`${pageUrl} → ${url} (no such page or file)`);
    else if (hash && !ids.get(target)?.has(hash)) broken.push(`${pageUrl} → ${url} (no element with id="${hash}")`);
  }
}

for (const line of broken) console.log(`BROKEN  ${line}`);
console.log(
  `${checked} internal links checked: ${broken.length} broken, ${placeholders} placeholder "#" links (see npm run todo)`
);
process.exit(broken.length ? 1 : 0);
