// Each project's index.md becomes /projects/<folder>/.
// Log entries are only shown inside their project page, never as pages of their own.
export default {
  eleventyComputed: {
    permalink: (data) =>
      data.page.inputPath.includes("/log/") ? false : `/projects/${data.page.fileSlug}/`,
  },
};
