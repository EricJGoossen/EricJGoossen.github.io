// Checks the built site before it can go live:
//  - every internal link, image/video source and #anchor resolves
//  - no visible page still has filler: "Placeholder" text, gray placeholder
//    boxes, or "#" links (unfinished things belong in `draft: true` items)
// Usage: node scripts/check-links.js [_site]   (`npm run build` and `npm run check` run it)
// Exits 1 if anything is broken or unfinished.
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
const broken = [];
const filler = [];
for (const page of pages) {
  const html = fs.readFileSync(page, "utf8");
  const pageUrl = "/" + path.relative(root, page).replace(/index\.html$/, "");
  const text = html.replace(/<(script|style)[\s\S]*?<\/\1>/g, "").replace(/<[^>]+>/g, " ");
  if (/placeholder/i.test(text)) filler.push(`${pageUrl}: "${text.match(/[^.\n]{0,40}placeholder[^.\n]{0,40}/i)[0].trim()}"`);
  if (html.includes('aria-label="Placeholder:')) filler.push(`${pageUrl}: gray placeholder image box`);
  for (const [, url] of html.matchAll(/\s(?:href|src|poster)="([^"]*)"/g)) {
    if (/^(https?:|mailto:|tel:|data:)/.test(url)) continue;
    checked++;
    if (url === "#") {
      filler.push(`${pageUrl}: a link that goes nowhere ("#")`);
      continue;
    }
    const [withQuery, hash] = url.split("#");
    const urlPath = withQuery.split("?")[0]; // "?v=..." on assets, "?q=..." on search links
    const base = pageUrl.endsWith("/") ? pageUrl : path.posix.dirname(pageUrl) + "/";
    const absolute = urlPath === "" ? pageUrl : urlPath.startsWith("/") ? urlPath : path.posix.join(base, urlPath);
    const target = targetFile(absolute);
    if (!fs.existsSync(target)) broken.push(`${pageUrl} → ${url} (no such page or file)`);
    else if (hash && !ids.get(target)?.has(hash)) broken.push(`${pageUrl} → ${url} (no element with id="${hash}")`);
  }
}

for (const line of broken) console.log(`BROKEN  ${line}`);
for (const line of [...new Set(filler)]) console.log(`UNFINISHED  ${line}`);
if (filler.length) console.log('Fill these in, or mark the project/entry/publication `draft: true` to keep it off the site.');
console.log(`${checked} internal links checked: ${broken.length} broken, ${new Set(filler).size} unfinished`);
process.exit(broken.length || filler.length ? 1 : 0);
