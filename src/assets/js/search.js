// The search box at the bottom of the home page (#search). The index is a JSON file built with the site
// (src/search-index.njk), so nothing leaves the site: every word typed has to
// appear in a result's title, project or text. Titles count most.
const root = new URL("../../", document.currentScript.src); // this file is /assets/js/search.js
const input = document.getElementById("search-input");
const status = document.getElementById("search-status");
const list = document.getElementById("search-results");
let index = null;

const fold = (s = "") => s.toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "");

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
  const pattern = new RegExp(terms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|"), "gi");
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

function render() {
  const query = input.value.trim();
  const url = new URL(location.href);
  if (query) url.searchParams.set("q", query);
  else url.searchParams.delete("q");
  history.replaceState(null, "", url);

  list.replaceChildren();
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
    link.href = new URL(item.url.replace(/^\//, ""), root);
    link.textContent = item.title;
    li.append(meta, link, snippet(item.text, terms));
    list.append(li);
  }
}

input.value = new URLSearchParams(location.search).get("q") ?? "";
input.addEventListener("input", render);
input.focus();

fetch(new URL("search-index.json", root))
  .then((response) => response.json())
  .then((data) => {
    index = data;
    render();
  })
  .catch(() => {
    status.textContent = "Search couldn't load. Every project is listed on the home page.";
  });
