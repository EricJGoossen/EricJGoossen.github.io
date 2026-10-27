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
      title: d.title,
      org: d.org ?? "",
      timeline: d.timeline ?? "",
      tools: d.tools ?? [],
      summary: d.summary ?? "",
      loc: projectLoc(entries.filter((e) => projectOf(e, [p]))),
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
// to their summaries, then whole projects drop off the end (the home page
// order sets which come first).
export const MAX_PAGES = 8;

export async function buildPortfolioPdf(dataFile, outFile) {
  const data = JSON.parse(fs.readFileSync(dataFile, "utf8"));
  const tries = [];
  for (let keep = data.projects.length; keep >= 1; keep--) {
    for (const detail of [520, 300, 0]) tries.push({ keep, detail });
  }
  let result = null;
  for (const t of tries) {
    result = await layout({ ...data, projects: data.projects.slice(0, t.keep) }, t.detail);
    if (result.pages <= MAX_PAGES) {
      const dropped = data.projects.slice(t.keep).map((p) => p.title);
      if (dropped.length) console.warn(`[portfolio] left out to stay within ${MAX_PAGES} pages: ${dropped.join(", ")}`);
      break;
    }
  }
  fs.writeFileSync(outFile, result.buffer);
  console.log(`[portfolio] ${result.pages} pages`);
}

// Lays the portfolio out once: a header (name, contacts, mission, a pointer to
// the site), then each project with its tagged entries, then publications.
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
  // The portfolio is meant to be seen on the site: say so, loudly, in a box.
  {
    const pad = 12;
    const y = doc.y + 6;
    const head = `This portfolio is meant to be viewed at ${bare(s.url)}`;
    const body = "This PDF is only a short summary. The website has every project's full write-up, with videos, code links and more projects. Please read it there.";
    doc.font("Bold").fontSize(12.5);
    const hh = doc.heightOfString(head, { width: W - 2 * pad });
    doc.font("Regular").fontSize(10);
    const bh = doc.heightOfString(body, { width: W - 2 * pad, lineGap: 1.5 });
    const boxH = pad + hh + 4 + bh + pad;
    doc.roundedRect(L, y, W, boxH, 8).fill(C.accent);
    doc.font("Bold").fontSize(12.5).fillColor("#ffffff").text(head, L + pad, y + pad, { width: W - 2 * pad, link: s.url });
    doc.font("Regular").fontSize(10).fillColor("#ffffff").text(body, L + pad, doc.y + 4, { width: W - 2 * pad, lineGap: 1.5, link: s.url });
    doc.x = L;
    doc.y = y + boxH;
  }
  rule(10, 12);

  // ---------- Projects ----------
  const IMG_W = 150;
  const IMG_H = 112;
  data.projects.forEach((p, pi) => {
    // A project's heading never sits alone at the bottom of a page.
    if (room() < 150) doc.addPage();
    else if (pi) rule(6, 12);
    doc.font("Bold").fontSize(15).fillColor(C.text).text(clean(p.title), L, doc.y, { width: W });
    const meta = [p.org, p.timeline].filter(Boolean).join("  ·  ");
    if (meta) doc.font("Regular").fontSize(9).fillColor(C.muted).text(meta, { width: W });
    const y0 = doc.y + 1;
    const row = [{ label: bare(p.url), url: p.url }];
    linkRow(row, { size: 9, y: y0 });
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

    for (const e of p.entries) {
      const pic = e.image ? fit(e.image.file, IMG_W, IMG_H) : null;
      const textX = pic ? L + IMG_W + 14 : L;
      const textW = W - (textX - L);
      const para = lead(e.paragraphs, detail);
      const facts = [e.date.slice(0, 7), e.loc && lines(e.loc), ...e.facts.filter((f) => /^(Role|Language)/.test(f))].filter(Boolean).join("   ·   ");
      // Measure the block so it never splits across pages.
      doc.font("SemiBold").fontSize(11);
      let h = doc.heightOfString(clean(e.title), { width: textW }) + 16;
      doc.font("Regular").fontSize(8.5);
      h += doc.heightOfString(facts, { width: textW }) + 4;
      doc.fontSize(9.5);
      if (e.summary) h += doc.heightOfString(clean(e.summary), { width: textW, lineGap: 2 }) + 4;
      doc.fontSize(9);
      if (para) h += doc.heightOfString(clean(para), { width: textW, lineGap: 1.8 }) + 4;
      h += 14;
      h = Math.max(h, pic ? pic.h : 0) + 12;
      if (room() < h) doc.addPage();
      const yTop = doc.y;
      if (pic) doc.image(pic.img, L + (IMG_W - pic.w) / 2, yTop + 2, { width: pic.w, height: pic.h });
      doc.font("SemiBold").fontSize(11).fillColor(C.text).text(clean(e.title), textX, yTop, { width: textW });
      doc.font("Regular").fontSize(8.5).fillColor(C.muted).text(facts, textX, doc.y + 1, { width: textW });
      doc.y += 3;
      if (e.summary) rich(e.summary, { size: 9.5, color: C.text, gap: 3, width: textW, x: textX });
      if (para) rich(para, { size: 9, color: "#3f3a36", gap: 3, lineGap: 1.8, width: textW, x: textX });
      doc.font("Medium").fontSize(8.5).fillColor(C.accent).text("Full entry, with video and code →", textX, doc.y + 1, { width: textW, link: e.url });
      doc.x = L;
      doc.y = Math.max(doc.y, yTop + (pic ? pic.h + 2 : 0)) + 12;
    }
  });

  // ---------- Publications ----------
  if (data.publications.length) {
    if (room() < 110) doc.addPage();
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
    doc.font("SemiBold").fontSize(8).fillColor(C.accent).text(`Best viewed at ${bare(s.url)}`, L, doc.page.height - 34, { width: W / 2, lineBreak: false, link: s.url });
    doc.font("Regular").fillColor(C.muted).text(`${s.name}  ·  ${i + 1} / ${range.count}`, L + W / 2, doc.page.height - 34, { width: W / 2, align: "right", lineBreak: false });
    doc.page.margins.bottom = keep;
  }
  const pages = range.count;
  doc.end();
  return new Promise((resolve) => doc.on("end", () => resolve({ buffer: Buffer.concat(chunks), pages })));
}
