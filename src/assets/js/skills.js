// Skill dropdowns are plain <details> elements, so they work without this file.
// This only adds: one open at a time, close on outside click / Escape,
// and keeping the menu on screen near the edges.
const skills = document.querySelectorAll("details.skill");

function closeAll(except) {
  skills.forEach((d) => {
    if (d !== except) d.open = false;
  });
}

skills.forEach((details) => {
  details.addEventListener("toggle", () => {
    if (!details.open) return;
    closeAll(details);
    // Shift the menu left just enough to stay inside the chip row,
    // so it lines up with the page column and never runs off screen.
    const menu = details.querySelector(".skill-menu");
    menu.style.left = "";
    const row = details.parentElement.getBoundingClientRect();
    const rect = menu.getBoundingClientRect();
    const overflow = rect.right - row.right;
    if (overflow > 0) menu.style.left = `${-Math.min(overflow, rect.left - row.left)}px`;
  });
});

document.addEventListener("click", (e) => {
  if (!e.target.closest("details.skill")) closeAll();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeAll();
});
