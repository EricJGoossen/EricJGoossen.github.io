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
import { entryId, entryInfo, entrySkills, projectOf } from "./skills.js";
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

// A media path from front matter or HTML, as a file under src/.
const fileFor = (projectDir, src) => (src.startsWith("/") ? path.join("src", src) : path.join(projectDir, src));

// Everything the PDF needs, from the published, portfolio-tagged content.
export function portfolioData({ site, projects, entries, skills, publications, resume }) {
  const out = {
    site: { name: site.name, url: site.url, headline: site.headline, bio: site.bio ?? [], photo: site.photo ? path.join("src", site.photo) : "", links: site.links ?? [] },
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
      title: d.title,
      org: d.org ?? "",
      timeline: d.timeline ?? "",
      tools: d.tools ?? [],
      summary: d.summary ?? "",
      url: `${site.url}${p.url}`,
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
            summary: e.data.summary ?? "",
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

// An image for pdfkit (JPEG or PNG), or null if it can't be placed.
function loadImage(file) {
  if (!file || !fs.existsSync(file)) return null;
  const ext = path.extname(file).toLowerCase();
  if (ext === ".svg") return svgToPng(file);
  if ([".jpg", ".jpeg", ".png"].includes(ext)) return fs.readFileSync(file);
  return null; // webp and others: pdfkit can't embed them
}

const C = { text: "#1c1917", muted: "#6b6560", accent: "#1d4ed8", border: "#e7e5e4", soft: "#eff4ff" };
const clean = (s = "") => s.replace(/ᵀ/g, "T");

export function buildPortfolioPdf(dataFile, outFile) {
  const data = JSON.parse(fs.readFileSync(dataFile, "utf8"));
  const doc = new PDFDocument({
    size: "LETTER",
    margins: { top: 54, bottom: 60, left: 60, right: 60 },
    bufferPages: true,
    info: { Title: `${data.site.name}: Portfolio`, Author: data.site.name, Subject: data.site.headline },
  });
  for (const w of ["Regular", "Medium", "SemiBold", "Bold", "Italic"]) doc.registerFont(w, path.join(FONTS, `Inter-${w}.otf`));
  const stream = fs.createWriteStream(outFile);
  doc.pipe(stream);

  const W = doc.page.width - doc.page.margins.left - doc.page.margins.right;
  const L = doc.page.margins.left;
  const bottom = () => doc.page.height - doc.page.margins.bottom;
  const room = () => bottom() - doc.y;

  // Text with **bold** runs.
  function rich(text, { size = 10, color = C.text, gap = 7, lineGap = 2.5, width = W, x = L } = {}) {
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
  // An image fitted into a box, or null if it can't be placed.
  function fitImage(file, maxW, maxH) {
    let buf = null;
    try {
      buf = loadImage(file);
    } catch {
      buf = null;
    }
    if (!buf) return null;
    const img = doc.openImage(buf);
    const scale = Math.min(maxW / img.width, maxH / img.height);
    return { img, w: img.width * scale, h: img.height * scale };
  }
  function image(file, maxH, { width = W } = {}) {
    let buf = null;
    try {
      buf = loadImage(file);
    } catch {
      buf = null;
    }
    if (!buf) return;
    const img = doc.openImage(buf);
    const scale = Math.min(width / img.width, maxH / img.height);
    const w = img.width * scale;
    const h = img.height * scale;
    if (room() < h + 8) doc.addPage();
    doc.image(img, L, doc.y, { width: w, height: h });
    doc.y += h + 10;
  }
  const link = (label, url, size = 9) => {
    doc.font("Medium").fontSize(size).fillColor(C.accent).text(label, { width: W, link: url, underline: false });
  };

  // ---------- Cover ----------
  const s = data.site;
  const top = doc.y;
  if (s.photo && fs.existsSync(s.photo)) {
    doc.save().circle(L + 48, top + 48, 48).clip().image(s.photo, L, top, { width: 96, height: 96 }).restore();
  }
  doc.font("Bold").fontSize(28).fillColor(C.text).text(s.name, L + 120, top + 14, { width: W - 120 });
  doc.font("Regular").fontSize(11.5).fillColor(C.muted).text(clean(s.headline), L + 120, doc.y + 4, { width: W - 120, lineGap: 2 });
  doc.y = Math.max(doc.y, top + 104) + 14;
  doc.x = L;
  const contacts = [{ label: s.url.replace(/^https?:\/\//, ""), url: s.url }, ...s.links.filter((l) => /^https?:|^mailto:/.test(l.url)).map((l) => ({ label: l.url.replace(/^mailto:/, "").replace(/^https?:\/\/(www\.)?/, ""), url: l.url }))];
  doc.font("Medium").fontSize(9.5);
  let x = L;
  const cy = doc.y;
  for (const c of contacts) {
    const w = doc.widthOfString(c.label);
    if (x + w > L + W) break;
    doc.fillColor(C.accent).text(c.label, x, cy, { width: w + 1, link: c.url, lineBreak: false });
    x += w + 16;
  }
  doc.x = L;
  doc.y = cy + 24;
  for (const p of s.bio) rich(p, { size: 10.5, gap: 8 });
  doc.moveDown(0.3);
  doc.font("SemiBold").fontSize(9).fillColor(C.muted).text("SKILLS", { characterSpacing: 1.2 });
  doc.moveDown(0.3);
  rich(data.skills.join("  ·  "), { size: 9.5, color: C.text, gap: 12 });
  doc.font("SemiBold").fontSize(9).fillColor(C.muted).text("CONTENTS", { characterSpacing: 1.2 });
  doc.moveDown(0.4);
  const contentsY = doc.y;
  doc.y += data.projects.length * 17 + (data.publications.length ? 17 : 0) + 10;
  doc.font("Regular").fontSize(8.5).fillColor(C.muted).text(
    `Generated from ${s.url.replace(/^https?:\/\//, "")} on ${new Date().toISOString().slice(0, 10)}. Every entry links to its full write-up, with videos, on the site.`,
    { width: W, lineGap: 2 }
  );

  // ---------- Projects ----------
  const startPages = [];
  for (const p of data.projects) {
    doc.addPage();
    startPages.push(doc.bufferedPageRange().start + doc.bufferedPageRange().count);
    doc.font("Bold").fontSize(22).fillColor(C.text).text(clean(p.title), { width: W });
    doc.moveDown(0.15);
    doc.font("Regular").fontSize(9.5).fillColor(C.muted).text([p.org, p.timeline].filter(Boolean).join("  ·  "), { width: W });
    if (p.tools.length) doc.text(`Tools: ${p.tools.join(", ")}`, { width: W });
    link(p.url.replace(/^https?:\/\//, ""), p.url);
    doc.moveDown(0.6);
    if (p.image) image(p.image.file, 230);
    rich(p.summary, { size: 11, color: C.text, gap: 8 });
    for (const para of p.overview) rich(para, { size: 10, gap: 7 });
    // Each entry: its heading across the page, its image on the right with the
    // text beside it (full width once past the image). The heading and image
    // always start on the same page.
    for (const e of p.entries) {
      const pic = e.image ? fitImage(e.image.file, W * 0.42, 200) : null;
      const facts = [e.date, ...e.facts].join("   ·   ");
      doc.font("SemiBold").fontSize(13.5);
      const headH = doc.heightOfString(clean(e.title), { width: W }) + 52;
      if (room() < headH + (pic ? pic.h : 90) + 20) doc.addPage();
      else {
        doc.moveDown(0.8);
        doc.moveTo(L, doc.y).lineTo(L + W, doc.y).lineWidth(0.6).strokeColor(C.border).stroke();
        doc.moveDown(0.7);
      }
      doc.font("SemiBold").fontSize(13.5).fillColor(C.text).text(clean(e.title), L, doc.y, { width: W });
      doc.moveDown(0.15);
      doc.font("Regular").fontSize(8.5).fillColor(C.muted).text(facts, { width: W, lineGap: 1.5 });
      if (e.skills.length) doc.text(`Skills: ${e.skills.join(", ")}`, { width: W });
      link("Full entry on the site", e.url, 8.5);
      doc.moveDown(0.6);
      const top = doc.y;
      let imgBottom = top;
      if (pic) {
        doc.image(pic.img, L + W - pic.w, top, { width: pic.w, height: pic.h });
        imgBottom = top + pic.h;
      }
      const page = doc.bufferedPageRange().count;
      for (const para of e.paragraphs) {
        const beside = pic && doc.bufferedPageRange().count === page && doc.y < imgBottom - 10;
        rich(para, { size: 9.5, gap: 6, width: beside ? W - pic.w - 18 : W });
      }
      if (doc.bufferedPageRange().count === page) doc.y = Math.max(doc.y, imgBottom + 4);
    }
  }

  // ---------- Publications ----------
  let pubsPage = 0;
  if (data.publications.length) {
    doc.addPage();
    pubsPage = doc.bufferedPageRange().count;
    doc.font("Bold").fontSize(22).fillColor(C.text).text("Publications", { width: W });
    doc.moveDown(0.6);
    for (const pub of data.publications) {
      doc.font("SemiBold").fontSize(12).fillColor(C.text).text(clean(pub.title), { width: W });
      doc.font("Regular").fontSize(9.5).fillColor(C.muted).text((pub.authors ?? []).join(", "), { width: W });
      doc.text([pub.venue, pub.status, pub.year, pub.award].filter(Boolean).join(" · "), { width: W });
      if (pub.tldr) rich(pub.tldr, { size: 10, gap: 4 });
      for (const l of pub.links ?? []) link(l.label, l.url, 9);
      doc.moveDown(0.8);
    }
  }

  // ---------- Contents (on the cover) and footers ----------
  doc.switchToPage(0);
  let y = contentsY;
  const rows = data.projects.map((p, i) => ({ title: p.title, page: startPages[i] }));
  if (pubsPage) rows.push({ title: "Publications", page: pubsPage });
  for (const r of rows) {
    doc.font("Regular").fontSize(10).fillColor(C.text).text(clean(r.title), L, y, { width: W - 40, lineBreak: false });
    doc.fillColor(C.muted).text(String(r.page), L + W - 40, y, { width: 40, align: "right", lineBreak: false });
    y += 17;
  }
  const range = doc.bufferedPageRange();
  for (let i = range.start; i < range.start + range.count; i++) {
    doc.switchToPage(i);
    const keep = doc.page.margins.bottom;
    doc.page.margins.bottom = 0;
    doc.font("Regular").fontSize(8).fillColor(C.muted).text(`${s.name}  ·  ${s.url.replace(/^https?:\/\//, "")}`, L, doc.page.height - 36, { width: W / 2, lineBreak: false, link: s.url });
    doc.text(`${i + 1} / ${range.count}`, L + W / 2, doc.page.height - 36, { width: W / 2, align: "right", lineBreak: false });
    doc.page.margins.bottom = keep;
  }
  doc.end();
  return new Promise((resolve, reject) => {
    stream.on("finish", resolve);
    stream.on("error", reject);
  });
}
