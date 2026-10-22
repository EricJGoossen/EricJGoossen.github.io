export default function (eleventyConfig) {
  eleventyConfig.addPassthroughCopy("src/assets");
  // Each project's images/ folder. Copied as a directory (not a glob) so images
  // added while the preview is running show up without a restart.
  eleventyConfig.addPassthroughCopy({ "src/projects": "projects" }, { filter: ["*/images/**", "!**/.gitkeep"] });

  // Log entries can hold many images, so only load them as they scroll into view.
  eleventyConfig.amendLibrary("md", (md) => {
    const renderImage = md.renderer.rules.image;
    md.renderer.rules.image = (tokens, idx, options, env, self) => {
      tokens[idx].attrSet("loading", "lazy");
      tokens[idx].attrSet("decoding", "async");
      return renderImage(tokens, idx, options, env, self);
    };
  });

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

  // The highlight (if any) that points at a log entry, for its skill tags.
  eleventyConfig.addFilter("highlightFor", (highlights, id) =>
    (highlights ?? []).find((h) => h.entry === id)
  );

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
  // Mismatches (unknown skill, bad `best`) are reported by the build checks.
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
      return { name: skill.name, best, others: uses.filter((u) => u !== best) };
    })
    // A skill no highlight uses yet has nowhere to link, so it waits off the page.
    .filter((skill) => skill.best)
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
