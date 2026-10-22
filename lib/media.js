// HTML for images and videos. Anywhere the site takes an image path (cover,
// hero, publication teaser) an .mp4/.webm works too.

const VIDEO = /\.(mp4|webm|mov|m4v)$/i;
const escape = (s = "") => String(s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");

export const isVideo = (src = "") => VIDEO.test(src);

// "images/x.jpg" in a project's front matter is relative to that project;
// "/..." and full URLs are used as they are.
export const mediaUrl = (base, src = "") => (/^(\/|https?:)/.test(src) ? src : `${base}${src}`);

// A short looping clip plays like a GIF (muted, inline) but keeps controls so
// it can be paused. `play: true` gives a normal click-to-play video with sound.
function videoTag(src, alt, { play = false, controls = true, poster = "", className = "" } = {}) {
  const attrs = [
    `src="${escape(src)}"`,
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

// {% video "images/clip.mp4", "What it shows", { play: true, poster: "images/still.jpg", caption: "..." } %}
export function videoShortcode(src, alt = "", opts = {}) {
  if (!isVideo(src)) throw new Error(`{% video %} expects an .mp4 or .webm file, got "${src}"`);
  const caption = opts.caption ? `<figcaption>${escape(opts.caption)}</figcaption>` : "";
  return `<figure class="video">${videoTag(src, alt, opts)}${caption}</figure>`;
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
