// Each project's index.md becomes /projects/<folder>/, unless it's marked
// `draft: true`. Log entries are only shown inside their project page, never
// as pages of their own.
export default {
  eleventyComputed: {
    permalink: (data) =>
      data.page.inputPath.includes("/log/") || data.draft ? false : `/projects/${data.page.fileSlug}/`,
  },
};
