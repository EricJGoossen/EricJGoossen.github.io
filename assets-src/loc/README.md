# Lines of code per entry (`loc:`)

Each log entry's `loc:` is the number of lines of code Eric wrote for it, shown
as "Code I wrote" in the entry's facts. A project's total is the sum of its
entries. Counted on 2026-10-26 by `count.py` (not run by the build; it needs
clones of the repos, which aren't part of this repo).

How it counts, per entry, from the code the entry links to:

- Commits: only those authored by Eric (any of his emails) or by Claude in his
  own repos (Claude Code working under his direction). Merge commits are skipped.
- Scope (`ENTRIES` in `count.py`): a linked commit or squash-merged PR is that
  commit; a linked PR is its commits; a linked tree is everything up to it (or
  since the previous entry's link in the same repo); a linked folder is that folder.
- Lines: non-blank added lines in code files (C/C++, Python, Java, JS/TS,
  shaders, shell, CMake, YAML/TOML configs, launch files, HTML/CSS). Not data,
  docs, notebooks, lock files, vendored or generated code (e.g. the
  ssik-generated `openarm_*_ik.py`). Renames aren't counted as new lines.
- A line already credited to an earlier entry in the same repo (a branch later
  squash-merged) isn't counted again.

Entries without code (talks, the competition, the paper, demos) have no `loc:`.

To recount: clone the repos into a folder, then
`LOC_REPOS=<folder> python3 assets-src/loc/count.py` (in a cloud session) and
copy the numbers from `counts.json` into each entry's `loc:`.
