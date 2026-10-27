// The PDF portfolio (/portfolio.pdf), rebuilt with the site on every build.
// What goes in is tagged in front matter: `portfolio: true` on a project
// (its overview) and on any of its entries. Each item gets its text and its
// most important image: `portfolioImage:` if set, else the first image in it
// (a video's still frame, a chart rasterized from its SVG).
//
// Two steps: portfolioData() gathers everything during the build (written to
// /portfolio.json, which agents can read too), and buildPortfolioPdf() lays it
// out with pdfkit once the build is done (eleventy.after in eleventy.config.js).
import fs from "node:fs";
import path from "node:path";
import PDFDocument from "pdfkit";
import { Resvg } from "@resvg/resvg-js";
import { entryId, entryInfo, entryLoc, entrySkills, projectLoc, projectOf } from "./skills.js";
import { isVideo } from "./media.js";

const FONTS = "assets-src/fonts";
const ENTITIES = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " " };
const decode = (s = "") =>
  s.replace(/&(#x?[0-9a-f]+|[a-z]+);/gi, (m, code) =>
    code[0] === "#"
      ? String.fromCodePoint(code[1].toLowerCase() === "x" ? parseInt(code.slice(2), 16) : parseInt(code.slice(1), 10))
      : ENTITIES[code.toLowerCase()] ?? m
  );

// Paragraphs of an entry or overview as text, with **bold** kept. Figures,
// captions and equations are left out (the image is placed separately).
export function paragraphs(html = "") {
  return decode(
    html
      .replace(/<figure[\s\S]*?<\/figure>/g, "")
      .replace(/<div class="math"[\s\S]*?<\/math>\s*<\/div>\s*<\/div>/g, "")
      .replace(/<math[\s\S]*?<\/math>/g, "")
      .replace(/<(strong|b)>([\s\S]*?)<\/\1>/g, "**$2**")
      .replace(/<li[^>]*>/g, "\n• ")
      .replace(/<\/(p|li|ul|ol|div|h\d)>/g, "\n\n")
      .replace(/<br\s*\/?>/g, "\n")
      .replace(/<[^>]+>/g, "")
  )
    .split(/\n{2,}/)
    .map((p) => p.replace(/\s+/g, " ").trim())
    .filter((p) => p && p !== "•");
}

// The first image in an entry's HTML: an <img> (a YouTube link's thumbnail
// counts) or a video's poster, as a path relative to the project folder.
function firstImage(html = "") {
  for (const fig of html.matchAll(/<figure[^>]*>([\s\S]*?)<\/figure>/g)) {
    const inner = fig[1];
    const video = inner.match(/<video[^>]*>/)?.[0];
    if (video) {
      const poster = video.match(/\sposter="([^"]*)"/)?.[1];
      if (poster) return { src: decode(poster), alt: decode(video.match(/\saria-label="([^"]*)"/)?.[1] ?? "") };
      continue;
    }
    const img = inner.match(/<img[^>]*>/)?.[0];
    if (img) return { src: decode(img.match(/\ssrc="([^"]*)"/)[1]), alt: decode(img.match(/\salt="([^"]*)"/)?.[1] ?? "") };
  }
  return null;
}

// The code link to show for an entry or project in the PDF: the first link to
// a code host (GitHub, GitLab), which a reader can open even where the site
// itself is blocked.
const CODE_HOST = /^https:\/\/(github\.com|gitlab\.com)\//;
const codeLinks = (links = []) => links.filter((l) => CODE_HOST.test(l.url ?? ""));

// A media path from front matter or HTML, as a file under src/.
const fileFor = (projectDir, src) => (src.startsWith("/") ? path.join("src", src) : path.join(projectDir, src));

// Everything the PDF needs, from the published, portfolio-tagged content.
export function portfolioData({ site, projects, entries, skills, publications, resume }) {
  const out = {
    site: { name: site.name, url: site.url, headline: site.headline, bio: site.bio ?? [], mission: site.mission ?? "", photo: site.photo ? path.join("src", site.photo) : "", links: site.links ?? [] },
    resume: resume?.pdf ? `${site.url}${resume.pdf}` : "",
    skills: (skills ?? []).filter((s) => !s.hidden).map((s) => s.name),
    projects: [],
    publications: (publications ?? []).filter((p) => !p.draft),
  };
  for (const p of projects) {
    const own = entries.filter((e) => projectOf(e, [p]) && e.data.portfolio);
    if (!p.data.portfolio && !own.length) continue;
    const d = p.data;
    const dir = path.dirname(p.inputPath);
    const still = (src, poster) => (src && isVideo(src) ? poster : src);
    const img = d.portfolioImage || still(d.hero, d.heroPoster) || still(d.cover, d.coverPoster);
    out.projects.push({
      slug: p.fileSlug,
      title: d.title,
      org: d.org ?? "",
      timeline: d.timeline ?? "",
      tools: d.tools ?? [],
      summary: d.summary ?? "",
      loc: projectLoc(entries.filter((e) => projectOf(e, [p]))),
      url: `${site.url}${p.url}`,
      code: codeLinks(d.links),
      overview: d.portfolio ? paragraphs(p.templateContent) : [],
      image: d.portfolio && img ? { file: fileFor(dir, img), alt: d.heroAlt || d.title } : null,
      entries: own
        .slice()
        .sort((a, b) => a.date - b.date) // oldest first: the story in order
        .map((e) => {
          const pick = e.data.portfolioImage ? { src: e.data.portfolioImage, alt: e.data.title } : firstImage(e.templateContent);
          return {
            title: e.data.title,
            date: e.date.toISOString().slice(0, 10),
            url: `${site.url}${p.url}#${entryId(e)}`,
            code: codeLinks(e.data.links)[0] ?? null,
            summary: e.data.summary ?? "",
            loc: entryLoc(e),
            facts: entryInfo(e).map((f) => `${f.label}: ${f.value}`),
            skills: entrySkills(e, p),
            image: pick ? { file: fileFor(dir, pick.src), alt: pick.alt } : null,
            paragraphs: paragraphs(e.templateContent),
          };
        }),
    });
  }
  return out;
}

// An SVG chart as a PNG: its CSS variables resolved to the light colors (the
// dark-mode block dropped), its text in Inter.
function svgToPng(file, width = 1400) {
  let svg = fs.readFileSync(file, "utf8");
  // Drop @media blocks (brace-matched), then resolve var(--x) from what's left.
  svg = svg.replace(/@media[^{]*\{/g, (m, offset) => `\u0000${m}`);
  let outSvg = "";
  for (let i = 0; i < svg.length; i++) {
    if (svg[i] === "\u0000") {
      let depth = 0;
      for (i++; i < svg.length; i++) {
        if (svg[i] === "{") depth++;
        else if (svg[i] === "}" && --depth === 0) break;
      }
      continue;
    }
    outSvg += svg[i];
  }
  const vars = {};
  for (const [, name, value] of outSvg.matchAll(/(--[\w-]+)\s*:\s*([^;}]+)/g)) vars[name] ??= value.trim();
  for (let pass = 0; pass < 3; pass++) {
    outSvg = outSvg.replace(/var\((--[\w-]+)\s*(?:,\s*([^)]*))?\)/g, (m, name, fallback) => vars[name] ?? fallback ?? m);
  }
  const resvg = new Resvg(outSvg, {
    fitTo: { mode: "width", value: width },
    background: "#ffffff",
    font: {
      loadSystemFonts: false,
      fontFiles: ["Regular", "Medium", "SemiBold", "Bold", "Italic"].map((w) => path.join(FONTS, `Inter-${w}.otf`)),
      defaultFontFamily: "Inter",
      sansSerifFamily: "Inter",
    },
  });
  return resvg.render().asPng();
}

// An image for pdfkit (JPEG or PNG), or null if it can't be placed. Charts
// are rasterized once per build, however many layouts are tried.
const images = new Map();
function loadImage(file) {
  if (!file || !fs.existsSync(file)) return null;
  if (images.has(file)) return images.get(file);
  const ext = path.extname(file).toLowerCase();
  let buf = null;
  try {
    if (ext === ".svg") buf = svgToPng(file);
    else if ([".jpg", ".jpeg", ".png"].includes(ext)) buf = fs.readFileSync(file);
  } catch {
    buf = null; // webp and others: pdfkit can't embed them
  }
  images.set(file, buf);
  return buf;
}

const C = { text: "#1c1917", muted: "#6b6560", accent: "#1d4ed8", border: "#e7e5e4", soft: "#eff4ff" };
const clean = (s = "") => s.replace(/ᵀ/g, "T");
const bare = (url = "") => url.replace(/^mailto:/, "").replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, "");
const lines = (n) => `${Number(n).toLocaleString("en-US")} lines of code I wrote`;

// The first paragraph of an entry, cut at a sentence end to about `max` characters.
function lead(paragraphs = [], max) {
  const p = (paragraphs.find((x) => !x.startsWith("•")) ?? "").replace(/\*\*/g, "");
  if (!max || p.length <= max) return p;
  const cut = p.slice(0, max);
  const end = Math.max(cut.lastIndexOf(". "), cut.lastIndexOf("? "), cut.lastIndexOf("! "));
  return end > max * 0.4 ? cut.slice(0, end + 1) : "";
}

// At most this many pages: if the tagged content runs longer, entries are cut
// to their summaries, then whole projects drop off the end.
export const MAX_PAGES = 8;

// One PDF per entry in src/_data/portfolio.json: its `file`, and an `order`
// of project folders to lead with (the rest follow in home page order), so a
// version for one kind of role can open with the projects that matter to it.
export async function buildPortfolioPdfs(dataFile, outDir, variants) {
  const data = JSON.parse(fs.readFileSync(dataFile, "utf8"));
  for (const v of variants) {
    const lead = (v.order ?? []).map((slug) => data.projects.find((p) => p.slug === slug)).filter(Boolean);
    const projects = [...lead, ...data.projects.filter((p) => !lead.includes(p))];
    await buildPortfolioPdf({ ...data, projects }, path.join(outDir, v.file));
  }
}

// Tries each excerpt length (long, shorter, summaries only) and keeps the one
// with the fewest pages, the longest on a tie, so a few lines never spill onto
// a page of their own. Past MAX_PAGES even with summaries only, projects drop
// off the end.
async function buildPortfolioPdf(data, outFile) {
  let best = null;
  for (let keep = data.projects.length; keep >= 1 && !best; keep--) {
    for (const detail of [520, 300, 0]) {
      const r = await layout({ ...data, projects: data.projects.slice(0, keep) }, detail);
      if (r.pages <= MAX_PAGES && (!best || r.pages < best.pages)) best = { ...r, keep };
    }
  }
  const dropped = data.projects.slice(best.keep).map((p) => p.title);
  if (dropped.length) console.warn(`[portfolio] ${path.basename(outFile)}: left out to stay within ${MAX_PAGES} pages: ${dropped.join(", ")}`);
  fs.writeFileSync(outFile, best.buffer);
  console.log(`[portfolio] ${path.basename(outFile)}: ${best.pages} pages`);
}

// Lays the portfolio out once: a header (name, contacts, mission, a line
// pointing to the site), then each project with its tagged entries, then publications.
// `detail` is how much of each entry's first paragraph to keep (0: summary only).
function layout(data, detail) {
  const doc = new PDFDocument({
    size: "LETTER",
    margins: { top: 48, bottom: 56, left: 54, right: 54 },
    bufferPages: true,
    info: { Title: `${data.site.name}: Portfolio`, Author: data.site.name, Subject: data.site.headline },
  });
  for (const w of ["Regular", "Medium", "SemiBold", "Bold", "Italic"]) doc.registerFont(w, path.join(FONTS, `Inter-${w}.otf`));
  const chunks = [];
  doc.on("data", (c) => chunks.push(c));

  const W = doc.page.width - doc.page.margins.left - doc.page.margins.right;
  const L = doc.page.margins.left;
  const bottom = () => doc.page.height - doc.page.margins.bottom;
  const room = () => bottom() - doc.y;

  // Text with **bold** runs.
  function rich(text, { size = 9.5, color = C.text, gap = 5, lineGap = 2, width = W, x = L } = {}) {
    const parts = clean(text).split(/\*\*/);
    doc.fontSize(size).fillColor(color);
    doc.x = x;
    parts.forEach((part, i) => {
      if (!part) return;
      doc.font(i % 2 ? "SemiBold" : "Regular").text(part, { width, lineGap, continued: i < parts.length - 1 && parts.slice(i + 1).some(Boolean) });
    });
    doc.x = L;
    doc.moveDown(gap / size);
  }
  function fit(file, maxW, maxH) {
    const buf = loadImage(file);
    if (!buf) return null;
    const img = doc.openImage(buf);
    const scale = Math.min(maxW / img.width, maxH / img.height);
    return { img, w: img.width * scale, h: img.height * scale };
  }
  const rule = (gapAbove = 8, gapBelow = 10) => {
    doc.y += gapAbove;
    doc.moveTo(L, doc.y).lineTo(L + W, doc.y).lineWidth(0.6).strokeColor(C.border).stroke();
    doc.y += gapBelow;
  };
  // Links on one line, separated by dots.
  function linkRow(items, { size = 9, y = doc.y, color = C.accent } = {}) {
    let x = L;
    doc.font("Medium").fontSize(size);
    items.forEach((c, i) => {
      if (i) {
        doc.fillColor(C.muted).text("·", x, y, { lineBreak: false });
        x += doc.widthOfString("·") + 7;
      }
      const w = doc.widthOfString(c.label);
      doc.fillColor(color).text(c.label, x, y, { width: w + 1, link: c.url, lineBreak: false });
      x += w + 7;
    });
    doc.x = L;
    doc.y = y + size * 1.5;
  }

  // ---------- Header ----------
  const s = data.site;
  const top = doc.y;
  const photo = s.photo && fs.existsSync(s.photo) ? 64 : 0;
  if (photo) doc.save().circle(L + photo / 2, top + photo / 2, photo / 2).clip().image(s.photo, L, top, { width: photo, height: photo }).restore();
  const tx = L + (photo ? photo + 16 : 0);
  doc.font("Bold").fontSize(22).fillColor(C.text).text(s.name, tx, top + 2, { width: W - (tx - L) });
  doc.font("Regular").fontSize(10).fillColor(C.muted).text(clean(s.headline), tx, doc.y + 2, { width: W - (tx - L), lineGap: 1.5 });
  doc.y = Math.max(doc.y, top + photo) + 10;
  const contacts = [{ label: bare(s.url), url: s.url }, ...s.links.filter((l) => /^https?:|^mailto:/.test(l.url)).map((l) => ({ label: bare(l.url), url: l.url }))];
  linkRow(contacts, { size: 9 });
  doc.y += 4;
  if (s.mission) rich(s.mission, { size: 10.5, color: C.text, gap: 4 });
  // One small line pointing to the site, for videos and more projects.
  doc.font("Regular").fontSize(9.5).fillColor(C.muted).text("More detail, videos and every project at ", L, doc.y + 2, { width: W, continued: true });
  doc.font("Medium").fillColor(C.accent).text(bare(s.url), { link: s.url, continued: true });
  doc.font("Regular").fillColor(C.muted).text(".", { link: null });
  rule(10, 12);

  // ---------- Projects ----------
  const IMG_W = 150;
  const IMG_H = 112;
  const sentences = (t = "") => t.match(/[^.!?]+[.!?]+(\s|$)/g)?.map((x) => x.trim()) ?? (t ? [t] : []);
  // An entry, measured or drawn: its image on the left; title, facts, summary,
  // an excerpt of its first paragraph and its code link beside it.
  function entryParts(e) {
    const pic = e.image ? fit(e.image.file, IMG_W, IMG_H) : null;
    const textX = pic ? L + IMG_W + 14 : L;
    const facts = [e.date.slice(0, 7), ...e.facts.filter((f) => /^(Role|Language)/.test(f))].join("   ·   ");
    const link = e.code
      ? { label: `${e.code.label} on ${/gitlab/.test(e.code.url) ? "GitLab" : "GitHub"} →`, url: e.code.url }
      : { label: "Full write-up, with video →", url: e.url };
    return { pic, textX, textW: W - (textX - L), facts, link };
  }
  function entryHeight(e, parts, para) {
    const { pic, textW, facts } = parts;
    doc.font("SemiBold").fontSize(11);
    let h = doc.heightOfString(clean(e.title), { width: textW }) + 4;
    doc.font("Regular").fontSize(8.5);
    h += doc.heightOfString(facts, { width: textW }) + 4;
    doc.fontSize(9.5);
    if (e.summary) h += doc.heightOfString(clean(e.summary), { width: textW, lineGap: 2 }) + 4;
    doc.fontSize(9);
    if (para) h += doc.heightOfString(clean(para), { width: textW, lineGap: 1.8 }) + 4;
    h += 14;
    return Math.max(h, pic ? pic.h + 2 : 0) + 12;
  }
  // The excerpts to try, longest first: the full one, then a sentence fewer at
  // a time, down to none (summary only), so an entry can fill what's left of a
  // page instead of leaving a gap.
  function excerpts(e) {
    const full = sentences(lead(e.paragraphs, detail));
    return full.map((_, k) => full.slice(0, full.length - k).join(" ")).concat("");
  }
  function drawEntry(e) {
    const parts = entryParts(e);
    const options = excerpts(e);
    let para = options.find((x) => entryHeight(e, parts, x) <= room());
    if (para === undefined) {
      doc.addPage();
      para = options[0];
    }
    const { pic, textX, textW, facts, link } = parts;
    const yTop = doc.y;
    if (pic) doc.image(pic.img, L + (IMG_W - pic.w) / 2, yTop + 2, { width: pic.w, height: pic.h });
    doc.font("SemiBold").fontSize(11).fillColor(C.text).text(clean(e.title), textX, yTop, { width: textW });
    doc.font("Regular").fontSize(8.5).fillColor(C.muted).text(facts, textX, doc.y + 1, { width: textW });
    doc.y += 3;
    if (e.summary) rich(e.summary, { size: 9.5, color: C.text, gap: 3, width: textW, x: textX });
    if (para) rich(para, { size: 9, color: "#3f3a36", gap: 3, lineGap: 1.8, width: textW, x: textX });
    doc.font("Medium").fontSize(8.5).fillColor(C.accent).text(link.label, textX, doc.y + 1, { width: textW, link: link.url });
    doc.x = L;
    doc.y = Math.max(doc.y, yTop + (pic ? pic.h + 2 : 0)) + 12;
  }
  function projectHeadHeight(p) {
    doc.font("Bold").fontSize(15);
    let h = doc.heightOfString(clean(p.title), { width: W });
    if (p.org || p.timeline) h += 12;
    h += 16;
    doc.font("Regular").fontSize(10);
    if (p.summary) h += doc.heightOfString(clean(p.summary), { width: W, lineGap: 2 }) + 6;
    return h;
  }

  data.projects.forEach((p, pi) => {
    // A project's heading always starts on the same page as its first entry
    // (at least that entry's summary).
    const first = p.entries[0];
    const need = projectHeadHeight(p) + (pi ? 18 : 0) + (first ? entryHeight(first, entryParts(first), "") : 0);
    if (room() < need) doc.addPage();
    else if (pi) rule(6, 12);
    doc.font("Bold").fontSize(15).fillColor(C.text).text(clean(p.title), L, doc.y, { width: W });
    const meta = [p.org, p.timeline].filter(Boolean).join("  ·  ");
    if (meta) doc.font("Regular").fontSize(9).fillColor(C.muted).text(meta, { width: W });
    const y0 = doc.y + 1;
    linkRow([{ label: bare(p.url), url: p.url }, ...p.code.map((c) => ({ label: bare(c.url), url: c.url }))], { size: 9, y: y0 });
    if (p.loc) {
      doc.font("SemiBold").fontSize(9);
      const label = lines(p.loc);
      const w = doc.widthOfString(label) + 14;
      doc.roundedRect(L + W - w, y0 - 3, w, 15, 7.5).fill(C.soft);
      doc.fillColor(C.accent).text(label, L + W - w + 7, y0, { lineBreak: false });
      doc.x = L;
    }
    doc.y = y0 + 15;
    if (p.summary) rich(p.summary, { size: 10, gap: 6 });
    for (const e of p.entries) drawEntry(e);
  });

  // ---------- Publications ----------
  if (data.publications.length) {
    if (room() < 150) doc.addPage();
    else rule(4, 12);
    doc.font("Bold").fontSize(15).fillColor(C.text).text("Publications", L, doc.y, { width: W });
    doc.moveDown(0.3);
    for (const pub of data.publications) {
      doc.font("SemiBold").fontSize(10.5).fillColor(C.text).text(clean(pub.title), { width: W });
      doc.font("Regular").fontSize(9).fillColor(C.muted).text((pub.authors ?? []).join(", "), { width: W });
      doc.text([pub.venue, pub.status, pub.year, pub.award].filter(Boolean).join(" · "), { width: W });
      if (pub.tldr) rich(pub.tldr, { size: 9.5, gap: 3 });
      if (pub.links?.length) linkRow(pub.links, { size: 9 });
      doc.moveDown(0.5);
    }
  }

  // ---------- Footers ----------
  const range = doc.bufferedPageRange();
  for (let i = range.start; i < range.start + range.count; i++) {
    doc.switchToPage(i);
    const keep = doc.page.margins.bottom;
    doc.page.margins.bottom = 0;
    doc.font("Regular").fontSize(8).fillColor(C.muted).text(`${s.name}  ·  ${bare(s.url)}`, L, doc.page.height - 34, { width: W / 2, lineBreak: false, link: s.url });
    doc.text(`${i + 1} / ${range.count}`, L + W / 2, doc.page.height - 34, { width: W / 2, align: "right", lineBreak: false });
    doc.page.margins.bottom = keep;
  }
  const pages = range.count;
  doc.end();
  return new Promise((resolve) => doc.on("end", () => resolve({ buffer: Buffer.concat(chunks), pages })));
}
