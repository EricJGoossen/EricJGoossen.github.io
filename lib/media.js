// HTML for images and videos. Anywhere the site takes an image path (cover,
// hero, publication teaser) an .mp4/.webm works too.

import fs from "node:fs";
import path from "node:path";

const VIDEO = /\.(mp4|webm|mov|m4v)$/i;
const escape = (s = "") => String(s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");

// Caption and photo credit under a figure. The credit is its own small line,
// right under the media, so a caption doesn't have to carry it.
const figText = (opts) =>
  (opts.credit ? `<small class="credit">${escape(opts.credit)}</small>` : "") +
  (opts.caption ? `<figcaption>${escape(opts.caption)}</figcaption>` : "");

export const isVideo = (src = "") => VIDEO.test(src);

// "images/x.jpg" in a project's front matter is relative to that project;
// "/..." and full URLs are used as they are.
export const mediaUrl = (base, src = "") => (/^(\/|https?:)/.test(src) ? src : `${base}${src}`);

// A short looping clip plays like a GIF (muted, inline) but keeps controls so
// it can be paused. `play: true` gives a normal click-to-play video with sound.
function videoTag(src, alt, { play = false, controls = true, poster = "", className = "", size = "" } = {}) {
  const attrs = [
    `src="${escape(src)}"`,
    size,
    className && `class="${className}"`,
    play ? "" : "autoplay muted loop",
    "playsinline",
    controls ? "controls" : "",
    `preload="${play ? "none" : "metadata"}"`,
    poster && `poster="${escape(poster)}"`,
    alt ? `aria-label="${escape(alt)}"` : `aria-hidden="true"`,
  ];
  return `<video ${attrs.filter(Boolean).join(" ")}></video>`;
}

// Image or video, picked by file extension.
export function media(src, alt = "", opts = {}) {
  if (isVideo(src)) return videoTag(src, alt, opts);
  const cls = opts.className ? ` class="${opts.className}"` : "";
  return `<img src="${escape(src)}"${cls} alt="${escape(alt)}" loading="lazy" decoding="async">`;
}

// Project tile cover: no controls (the whole tile is a link). People who ask
// for reduced motion see a still instead: the poster, or the title box.
export function tileMedia(src, { poster = "", title = "" } = {}) {
  if (!isVideo(src)) return media(src, "");
  const still = poster
    ? `<img class="still" src="${escape(poster)}" alt="" loading="lazy" decoding="async">`
    : `<div class="ph still" aria-hidden="true"><span>${escape(title)}</span></div>`;
  return videoTag(src, "", { controls: false, poster }) + still;
}

// {% video "images/clip.mp4", "What it shows", { play: true, poster: "images/still.jpg", caption: "...", credit: "Video: ..." } %}
export function videoShortcode(src, alt = "", opts = {}) {
  if (!isVideo(src)) throw new Error(`{% video %} expects an .mp4 or .webm file, got "${src}"`);
  return `<figure class="video">${videoTag(src, alt, opts)}${figText(opts)}</figure>`;
}

// Pixel size of an SVG (viewBox), PNG or JPEG file, or null if it can't be read.
function imageSize(file) {
  let buf;
  try {
    buf = fs.readFileSync(file);
  } catch {
    return null;
  }
  if (/\.svg$/i.test(file)) {
    const head = buf.subarray(0, 2000).toString();
    const box = head.match(/viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)/);
    return box ? [Math.round(+box[1]), Math.round(+box[2])] : null;
  }
  if (buf.readUInt32BE(0) === 0x89504e47) return [buf.readUInt32BE(16), buf.readUInt32BE(20)];
  if (buf[0] === 0xff && buf[1] === 0xd8) {
    // Walk the JPEG markers to the frame header (SOF0-SOF15, except DHT/JPG/DAC).
    for (let i = 2; i + 9 < buf.length; ) {
      if (buf[i] !== 0xff) return null;
      const marker = buf[i + 1];
      if (marker >= 0xc0 && marker <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(marker)) {
        return [buf.readUInt16BE(i + 7), buf.readUInt16BE(i + 5)];
      }
      i += 2 + buf.readUInt16BE(i + 2);
    }
  }
  return null;
}

// width/height attributes so the browser reserves the media's space before it
// loads (otherwise a row grows mid scroll-in and jumps). A video takes its
// poster's size. `dir` is the folder the relative paths start from.
function mediaSize(dir, src, poster) {
  const file = (p) => (p.startsWith("/") ? path.join("src", p) : path.join(dir, p));
  const still = isVideo(src) ? poster : src;
  return still && !/^https?:/.test(still) ? imageSize(file(still)) : null;
}

// {% row "images/clip.mp4", "What it shows", { caption: "...", credit: "Photo: ...", poster: "images/still.jpg",
//         more: [{ src: "images/chart.svg", alt: "...", caption: "..." }] } %}
// One paragraph of Markdown with its image or video beside it (below it on phones).
// A src of "placeholder" holds the media's place with a gray box labelled with the
// alt text, until the real file exists (the build refuses it on a visible page).
// `more` stacks extra images or videos under the first one, in the same column.
// Portrait media take half the column unless they have `wide: true`.
// The blank lines around the paragraph let Markdown render it inside the HTML.
function rowFigure(dir, src, alt, opts = {}) {
  if (!src || !alt) throw new Error(`{% row %} needs a media file and alt text, got "${src}", "${alt}"`);
  if (src === "placeholder") {
    return `<figure><div class="ph" role="img" aria-label="Placeholder: ${escape(alt)}"><span>${escape(alt)}</span></div>${figText(opts)}</figure>`;
  }
  const dims = mediaSize(dir, src, opts.poster);
  const size = dims ? `width="${dims[0]}" height="${dims[1]}"` : "";
  const shown = isVideo(src)
    ? videoTag(src, alt, { ...opts, size })
    : `<img src="${escape(src)}" alt="${escape(alt)}" ${size} loading="lazy" decoding="async">`.replace("  ", " ");
  // Portrait media take half the column, so two sit side by side; `wide: true` keeps
  // one at full width (a portrait grid of clips that would be too small at half).
  const tall = !opts.wide && dims && dims[1] > dims[0] * 1.1 ? ' class="tall"' : "";
  return `<figure${tall}>${shown}${figText(opts)}</figure>`;
}

// A log entry's media paths start at its project folder, not at log/.
export function rowShortcode(content, src, alt = "", opts = {}) {
  const input = this?.page?.inputPath ?? "";
  const dir = input.includes("/log/") ? input.slice(0, input.lastIndexOf("/log/")) : path.dirname(input);
  const figures = [rowFigure(dir, src, alt, opts), ...(opts.more ?? []).map((m) => rowFigure(dir, m.src, m.alt, m))];
  return (
    `<div class="row">\n<div class="row-text">\n\n${content.trim()}\n\n</div>\n` +
    `<div class="row-media">${figures.join("")}</div>\n</div>\n`
  );
}

// {% youtube "dQw4w9WgXcQ" or a full YouTube link, "Title" %}
// A thumbnail that links to YouTube: no YouTube scripts or cookies on this site.
export function youtubeShortcode(idOrUrl = "", title = "Video") {
  const id =
    String(idOrUrl).match(/(?:v=|youtu\.be\/|shorts\/|embed\/)([\w-]{11})/)?.[1] ??
    (/^[\w-]{11}$/.test(idOrUrl) ? idOrUrl : null);
  if (!id) throw new Error(`{% youtube %} needs a video ID or link, got "${idOrUrl}"`);
  return (
    `<figure class="youtube"><a href="https://www.youtube.com/watch?v=${id}">` +
    `<img src="https://i.ytimg.com/vi/${id}/hqdefault.jpg" alt="" loading="lazy" decoding="async">` +
    `<span class="play" aria-hidden="true"></span>` +
    `<span class="visually-hidden">Watch on YouTube: ${escape(title)}</span></a>` +
    `<figcaption>${escape(title)} <span class="muted">· YouTube</span></figcaption></figure>`
  );
}
