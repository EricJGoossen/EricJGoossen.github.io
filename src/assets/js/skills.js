// Skill dropdowns are plain <details> elements, so they work without this file.
// This only adds: one open at a time, close on outside click / Escape,
// and keeping the menu on screen near the right edge.
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
    const menu = details.querySelector(".skill-menu");
    menu.classList.remove("align-right");
    if (menu.getBoundingClientRect().right > window.innerWidth - 16) {
      menu.classList.add("align-right");
    }
  });
});

document.addEventListener("click", (e) => {
  if (!e.target.closest("details.skill")) closeAll();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeAll();
});
