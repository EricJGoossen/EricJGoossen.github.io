// Full-screen view for the images and videos in log entries and paper cards:
// a click (or the expand button in the corner) opens the media over the whole
// page; a click anywhere, the close button or Escape closes it. Media that are
// links (project tiles, YouTube thumbnails) keep doing what links do.
const MEDIA = ".entry figure > img, .entry figure > video, .entry p > img, .pub-media > img, .pub-media > video";

let dialog = null;
function viewer() {
  if (dialog) return dialog;
  dialog = document.createElement("dialog");
  dialog.className = "media-view";
  dialog.setAttribute("aria-label", "Full-screen view");
  dialog.innerHTML = `<button class="media-view-close" type="button" aria-label="Close">×</button><figure></figure>`;
  // A click anywhere but on a playing video's controls closes it.
  dialog.addEventListener("click", (event) => {
    if (event.target.tagName === "VIDEO" && onControls(event, event.target)) return;
    dialog.close();
  });
  dialog.addEventListener("close", () => {
    dialog.querySelector("figure").replaceChildren();
    document.documentElement.classList.remove("media-view-open");
  });
  document.body.append(dialog);
  return dialog;
}

// The bottom of a video with controls is its control bar.
const onControls = (event, video) => video.controls && event.clientY > video.getBoundingClientRect().bottom - 56;

function open(el) {
  const d = viewer();
  const figure = d.querySelector("figure");
  const copy = el.cloneNode(false);
  copy.removeAttribute("width");
  copy.removeAttribute("height");
  copy.removeAttribute("loading");
  if (el.tagName === "VIDEO") {
    copy.controls = true;
    copy.preload = "auto";
    copy.currentTime = el.currentTime;
    copy.muted = el.muted;
    if (el.autoplay || !el.paused) copy.autoplay = true;
    el.pause();
  }
  figure.className = el.closest("figure.chart") ? "chart" : "";
  figure.append(copy);
  const caption = el.closest("figure")?.querySelector("figcaption");
  if (caption) figure.append(caption.cloneNode(true));
  document.documentElement.classList.add("media-view-open");
  d.showModal();
  if (copy.tagName === "VIDEO") copy.play().catch(() => {});
}

document.addEventListener("click", (event) => {
  const button = event.target.closest(".media-expand");
  const el = button ? button.parentElement.querySelector("img, video") : event.target.closest(MEDIA);
  if (!el || el.closest("a, dialog")) return;
  if (!button && el.tagName === "VIDEO" && onControls(event, el)) return;
  event.preventDefault();
  open(el);
});

// An expand button in the corner of each one, so it's plain on any screen
// (and reachable by keyboard) that the media opens. Search adds entries as you
// open them, so new ones get theirs too.
function decorate(root) {
  for (const el of root.querySelectorAll(MEDIA)) {
    const box = el.parentElement;
    if (el.closest("a") || box.querySelector(":scope > .media-expand")) continue;
    box.classList.add("media-box");
    const b = document.createElement("button");
    b.type = "button";
    b.className = "media-expand";
    b.setAttribute("aria-label", `View full screen: ${el.getAttribute("alt") || el.getAttribute("aria-label") || "media"}`);
    b.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>`;
    el.after(b);
  }
}
decorate(document);
new MutationObserver(() => decorate(document)).observe(document.querySelector("main") ?? document.body, { childList: true, subtree: true });
