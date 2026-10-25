// The search results page (/search/?q=...), opened from the search box in the header. The index is a JSON file built with the site
// (src/search-index.njk), so nothing leaves the site: every word typed has to
// appear in a result's title, project or text. Titles count most.
// Here the results update as you type. A log entry's result opens the full
// entry in place on the first click, and goes to it on its project page on the second.
const root = new URL("../../", document.currentScript.src); // this file is /assets/js/search.js
const form = document.querySelector(".search-page .search-form");
const input = document.getElementById("search-input");
const status = document.getElementById("search-status");
const list = document.getElementById("search-results");
let index = null;

const fold = (s = "") => s.toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "");
const escape = (t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const siteUrl = (path) => new URL(path.replace(/^\//, ""), root).href;

function score(item, terms) {
  const title = fold(item.title);
  const context = fold(item.context);
  const text = fold(item.text);
  let total = 0;
  for (const term of terms) {
    if (title.includes(term)) total += 10;
    else if (context.includes(term)) total += 3;
    else if (text.includes(term)) total += 1;
    else return 0;
  }
  return total + (item.type === "Skill" || item.type === "Project" ? 1 : 0);
}

// About 200 characters of text around the first match, with every term marked.
function snippet(text, terms) {
  const folded = fold(text);
  const first = Math.min(...terms.map((t) => folded.indexOf(t)).filter((i) => i >= 0));
  const start = Number.isFinite(first) ? Math.max(0, first - 70) : 0;
  const end = Math.min(text.length, start + 200);
  const piece = (start > 0 ? "…" : "") + text.slice(start, end) + (end < text.length ? "…" : "");
  const p = document.createElement("p");
  p.className = "result-snippet";
  const pattern = new RegExp(terms.map(escape).join("|"), "gi");
  let last = 0;
  for (const m of piece.matchAll(pattern)) {
    p.append(piece.slice(last, m.index));
    const mark = document.createElement("mark");
    mark.textContent = m[0];
    p.append(mark);
    last = m.index + m[0].length;
  }
  p.append(piece.slice(last));
  return p;
}

// Wraps every term in the opened entry's text in <mark>.
function markTerms(el, terms) {
  const pattern = new RegExp(terms.map(escape).join("|"), "gi");
  const found = new RegExp(pattern.source, "i"); // no "g": test() would remember its place
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) if (found.test(walker.currentNode.data)) nodes.push(walker.currentNode);
  for (const node of nodes) {
    const parts = document.createDocumentFragment();
    let last = 0;
    for (const m of node.data.matchAll(pattern)) {
      parts.append(node.data.slice(last, m.index));
      const mark = document.createElement("mark");
      mark.textContent = m[0];
      parts.append(mark);
      last = m.index + m[0].length;
    }
    parts.append(node.data.slice(last));
    node.replaceWith(parts);
  }
}

// The full entry, in place of its snippet.
function open(li, item, link, terms) {
  const entry = document.createElement("div");
  entry.className = "entry result-entry";
  entry.innerHTML = item.html;
  for (const el of entry.querySelectorAll("[src], [poster], [href]")) {
    for (const attr of ["src", "poster", "href"]) {
      const value = el.getAttribute(attr);
      if (value?.startsWith("/")) el.setAttribute(attr, siteUrl(value));
    }
  }
  markTerms(entry, terms);
  li.querySelector(".result-snippet").replaceWith(entry);
  li.classList.add("open");
  link.setAttribute("aria-expanded", "true");
  link.title = "Open in its project";
  for (const video of entry.querySelectorAll("video[autoplay]")) video.play().catch(() => {});
}

function render() {
  const query = input.value.trim();
  list.replaceChildren();
  form.closest(".search-page").classList.toggle("empty", !query);
  if (!index) return;
  if (!query) {
    status.textContent = "";
    return;
  }
  const terms = fold(query).split(/\s+/).filter(Boolean);
  const hits = index
    .map((item) => ({ item, score: score(item, terms) }))
    .filter((hit) => hit.score)
    .sort((a, b) => b.score - a.score);
  status.textContent = `${hits.length} ${hits.length === 1 ? "result" : "results"} for “${query}”`;

  for (const { item } of hits) {
    const li = document.createElement("li");
    const meta = document.createElement("p");
    meta.className = "result-meta";
    meta.textContent = [item.type, item.context].filter(Boolean).join(" · ");
    const link = document.createElement("a");
    link.className = "result-title";
    link.href = siteUrl(item.url);
    link.textContent = item.title;
    const text = snippet(item.text, terms);
    li.append(meta, link, text);
    if (item.html) {
      // A click anywhere on the result (its title included) opens the entry;
      // once it's open, the title goes to the entry on its project page.
      li.classList.add("openable");
      link.setAttribute("aria-expanded", "false");
      li.addEventListener("click", (event) => {
        if (li.classList.contains("open")) return;
        const newTab = event.target === link && (event.button || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey);
        if (newTab) return;
        event.preventDefault();
        open(li, item, link, terms);
      });
    }
    list.append(li);
  }
}

// Typing updates the results (and the address, so back and reload keep them).
let pending = 0;
input.addEventListener("input", () => {
  clearTimeout(pending);
  pending = setTimeout(() => {
    const query = input.value.trim();
    history.replaceState(null, "", query ? `?q=${encodeURIComponent(query)}` : location.pathname);
    render();
  }, 120);
});
form.addEventListener("submit", (event) => {
  event.preventDefault();
  clearTimeout(pending);
  render();
});

input.value = new URLSearchParams(location.search).get("q") ?? "";
// With a mouse, keep typing where the words end (on a phone, focus would pop the keyboard over the results).
if (matchMedia("(pointer: fine)").matches) {
  input.focus();
  input.setSelectionRange(input.value.length, input.value.length);
}
render();

fetch(new URL("search-index.json", root))
  .then((response) => response.json())
  .then((data) => {
    index = data;
    render();
  })
  .catch(() => {
    status.textContent = "Search couldn't load. Every project is listed on the home page.";
  });
