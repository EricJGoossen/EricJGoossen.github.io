import crypto from "node:crypto";
import fs from "node:fs";
import { jsonLd, llmsFullTxt, llmsTxt, projectMarkdown } from "./lib/agents.js";
import { checkSite } from "./lib/checks.js";
import { buildPortfolioPdfs, portfolioData } from "./lib/portfolio.js";
import { isVideo, media, mediaUrl, rowShortcode, tileMedia, videoShortcode, youtubeShortcode } from "./lib/media.js";
import { entryId, entryInfo, entryLoc, entrySkills, formatLoc, projectLoc, rebase, searchIndex, skillPages, skillSlug } from "./lib/skills.js";

export default function (eleventyConfig) {
  eleventyConfig.addPassthroughCopy("src/assets");
  eleventyConfig.addPassthroughCopy("src/_headers"); // security headers, read by Cloudflare
  eleventyConfig.addPassthroughCopy("src/_redirects"); // moved URLs, read by Cloudflare
  eleventyConfig.addPassthroughCopy("src/resume.pdf"); // at /resume.pdf, beside /portfolio.pdf
  // Each project's images/ folder. Copied as a directory (not a glob) so images
  // added while the preview is running show up without a restart. A draft
  // project's images stay out too, so nothing of it is reachable by URL
  // (read once at startup: restart the preview after changing `draft`).
  const draftProjects = fs.readdirSync("src/projects").filter((folder) => {
    const file = `src/projects/${folder}/index.md`;
    if (!fs.existsSync(file)) return false;
    const frontMatter = fs.readFileSync(file, "utf8").split(/^---\s*$/m)[1] ?? "";
    return /^draft:\s*true\b/m.test(frontMatter);
  });
  eleventyConfig.addPassthroughCopy(
    { "src/projects": "projects" },
    { filter: ["*/images/**", "!**/.gitkeep", ...draftProjects.map((folder) => `!${folder}/**`)] }
  );

  // Log entries can hold many images, so only load them as they scroll into view.
  eleventyConfig.amendLibrary("md", (md) => {
    const renderImage = md.renderer.rules.image;
    md.renderer.rules.image = (tokens, idx, options, env, self) => {
      tokens[idx].attrSet("loading", "lazy");
      tokens[idx].attrSet("decoding", "async");
      return renderImage(tokens, idx, options, env, self);
    };
  });

  // Anything marked `draft: true` (a project, log entry or publication) is
  // left out of the built site entirely until the line is removed.

  // Published project pages, in the order set by `order` in each index.md.
  const publishedProjects = (api) =>
    api
      .getFilteredByGlob("src/projects/*/index.md")
      .filter((p) => !p.data.draft)
      .sort((a, b) => (a.data.order ?? 99) - (b.data.order ?? 99));
  eleventyConfig.addCollection("projects", publishedProjects);

  // Not a real collection: runs lib/checks.js on every build. A real build
  // (npm run build, Cloudflare) stops with the list of problems. The local
  // preview keeps running and shows them in a red banner on every page instead.
  const preview = process.env.ELEVENTY_RUN_MODE === "serve";
  let checkErrors = [];
  eleventyConfig.addCollection("_checks", (api) => {
    const { errors, warnings } = checkSite(api);
    for (const w of warnings) console.warn(`[checks] warning: ${w}`);
    checkErrors = errors;
    if (errors.length) {
      const message = `Site checks failed:\n${errors.map((e) => `  - ${e}`).join("\n")}\n`;
      if (!preview) throw new Error(message);
      console.error(`[checks] ${message}`);
    }
    return [];
  });
  eleventyConfig.addShortcode("checkBanner", () =>
    preview && checkErrors.length
      ? `<div class="check-banner" role="alert"><strong>Site checks failed. A real build would stop here:</strong><ul>${checkErrors
          .map((e) => `<li>${e.replace(/&/g, "&amp;").replace(/</g, "&lt;")}</li>`)
          .join("")}</ul></div>`
      : ""
  );

  // Progress log entries across all projects, newest first. A `date:` with a
  // time in an entry's front matter orders entries from the same day.
  const publishedEntries = (api) =>
    api
      .getFilteredByGlob("src/projects/*/log/*.md")
      .filter((e) => !e.data.draft)
      .sort((a, b) => b.date - a.date);
  eleventyConfig.addCollection("logEntries", publishedEntries);

  // One page per skill (src/skill.njk), composed from every entry whose
  // skillTags list it. See lib/skills.js.
  eleventyConfig.addCollection("skillPages", (api) =>
    skillPages(api.getAll()[0]?.data.skills ?? [], publishedProjects(api), publishedEntries(api))
  );

  eleventyConfig.addFilter("published", (list = []) => list.filter((item) => !item.draft));
  // URL of a published project page, or "" if it's a draft or doesn't exist.
  eleventyConfig.addFilter("projectUrl", (slug, projects = []) => projects.find((p) => p.fileSlug === slug)?.url ?? "");

  eleventyConfig.addFilter("entriesFor", (entries, slug) =>
    entries.filter((e) => e.inputPath.includes(`/projects/${slug}/log/`))
  );

  // Links to files that aren't in src/ yet (e.g. /resume.pdf) are left
  // out until the file is added, so the site never shows a dead link.
  const fileReady = (url = "") => !/^\/.+\.[a-z0-9]+$/i.test(url) || fs.existsSync(`src${url}`);
  eleventyConfig.addFilter("fileReady", fileReady);
  // "?v=<hash of the file>" on the stylesheet and scripts, so browsers fetch a
  // changed file fresh instead of running a cached old copy.
  eleventyConfig.addFilter("versioned", (url) => {
    const file = `src${url}`;
    if (!fs.existsSync(file)) return url;
    return `${url}?v=${crypto.createHash("sha1").update(fs.readFileSync(file)).digest("hex").slice(0, 8)}`;
  });
  eleventyConfig.addFilter("readyLinks", (links = []) => links.filter((link) => fileReady(link.url)));

  eleventyConfig.addFilter("entryId", entryId);
  eleventyConfig.addFilter("entryLoc", entryLoc);
  eleventyConfig.addFilter("projectLoc", projectLoc);
  eleventyConfig.addFilter("formatLoc", formatLoc);
  eleventyConfig.addFilter("skillSlug", skillSlug);
  eleventyConfig.addFilter("rebase", rebase);
  eleventyConfig.addFilter("searchIndex", (collections, site, publications) =>
    searchIndex({
      site,
      projects: collections.projects,
      entries: collections.logEntries,
      skills: collections.skillPages,
      publications,
    })
  );

  // For AI agents (lib/agents.js): /llms.txt, /llms-full.txt, a Markdown copy
  // of each project, and schema.org data in every page's head.
  const agentArgs = (collections, site, publications, resume) => ({
    site, resume, publications: publications ?? [],
    projects: collections.projects, entries: collections.logEntries, skills: collections.skillPages,
  });
  eleventyConfig.addFilter("llmsTxt", (c, site, pubs, resume) => llmsTxt(agentArgs(c, site, pubs, resume)));
  eleventyConfig.addFilter("llmsFullTxt", (c, site, pubs) => llmsFullTxt(agentArgs(c, site, pubs)));
  eleventyConfig.addFilter("projectMarkdown", (project, entries, site) => projectMarkdown(project, entries, site));
  // The PDF portfolio: gathered into /portfolio.json during the build, laid out
  // once the build is done (lib/portfolio.js), once per entry in
  // src/_data/portfolioPdfs.json (/portfolio.pdf, and /portfolio-ml.pdf leading
  // with the ML projects).
  eleventyConfig.addFilter("portfolioData", (c, site, pubs, resume) => portfolioData(agentArgs(c, site, pubs, resume)));
  eleventyConfig.on("eleventy.after", async ({ directories }) => {
    const out = directories?.output ?? "_site";
    if (fs.existsSync(`${out}/portfolio.json`)) await buildPortfolioPdfs(`${out}/portfolio.json`, out, JSON.parse(fs.readFileSync("src/_data/portfolioPdfs.json", "utf8")));
  });
  eleventyConfig.addFilter("jsonLd", (site, skills, project) => jsonLd({ site, skills, project }));

  // An entry's skill tags (its `skillTags:` list).
  eleventyConfig.addFilter("entrySkills", entrySkills);
  // Its basic facts (`info:` in its front matter), as [{ label, value }].
  eleventyConfig.addFilter("entryInfo", entryInfo);
  eleventyConfig.addFilter("projectFor", (projects, slug) => projects.find((p) => p.fileSlug === slug));

  eleventyConfig.addFilter("readableDate", (date) =>
    new Date(date).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      timeZone: "UTC",
    })
  );

  // Images and videos (see lib/media.js). In Markdown:
  //   {% video "images/clip.mp4", "What it shows" %}   {% youtube "VIDEO_ID", "Title" %}
  //   {% row "images/chart.svg", "What it shows" %} A paragraph. {% endrow %}
  eleventyConfig.addShortcode("media", media);
  eleventyConfig.addShortcode("tileMedia", tileMedia);
  eleventyConfig.addShortcode("video", videoShortcode);
  eleventyConfig.addShortcode("youtube", youtubeShortcode);
  eleventyConfig.addPairedShortcode("row", rowShortcode);
  eleventyConfig.addFilter("isVideo", isVideo);
  eleventyConfig.addFilter("mediaUrl", (src, base) => mediaUrl(base, src));

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
