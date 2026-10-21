export default function (eleventyConfig) {
  eleventyConfig.addPassthroughCopy("src/assets");
  eleventyConfig.addPassthroughCopy("src/projects/*/images");

  // Project overview pages, in the order set by `order` in each index.md.
  eleventyConfig.addCollection("projects", (api) =>
    api
      .getFilteredByGlob("src/projects/*/index.md")
      .sort((a, b) => (a.data.order ?? 99) - (b.data.order ?? 99))
  );

  // Progress log entries across all projects, oldest first.
  eleventyConfig.addCollection("logEntries", (api) =>
    api.getFilteredByGlob("src/projects/*/log/*.md").sort((a, b) => a.date - b.date)
  );

  eleventyConfig.addFilter("entriesFor", (entries, slug) =>
    entries.filter((e) => e.inputPath.includes(`/projects/${slug}/log/`))
  );

  eleventyConfig.addFilter("entryId", (entry) => entry.data.id ?? entry.fileSlug);

  eleventyConfig.addFilter("readableDate", (date) =>
    new Date(date).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      timeZone: "UTC",
    })
  );

  // For each skill: its best example plus every other highlight that uses it.
  // Built from the `skills` lists on each project's highlights, so nothing is duplicated.
  eleventyConfig.addFilter("skillIndex", (skills, projects) =>
    skills.map((skill) => {
      const uses = [];
      for (const project of projects) {
        for (const h of project.data.highlights ?? []) {
          if (!(h.skills ?? []).includes(skill.name)) continue;
          uses.push({
            key: `${project.fileSlug}/${h.entry}`,
            project: project.data.title,
            label: h.label,
            url: `${project.url}#${h.entry}`,
          });
        }
      }
      const best = uses.find((u) => u.key === skill.best) ?? uses[0];
      if (skill.best && best?.key !== skill.best) {
        console.warn(`[skills] "${skill.name}": best "${skill.best}" isn't a highlight tagged with this skill`);
      }
      return { name: skill.name, best, others: uses.filter((u) => u !== best) };
    })
  );

  // Gray box standing in for an image that hasn't been added yet.
  eleventyConfig.addShortcode(
    "placeholder",
    (label = "Image") =>
      `<div class="ph" role="img" aria-label="Placeholder: ${label}"><span>${label}</span></div>`
  );

  return {
    dir: { input: "src", output: "_site" },
    markdownTemplateEngine: "njk",
  };
}
