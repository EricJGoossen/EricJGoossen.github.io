# Installed tools

Everything installed for this project, so it can be moved into Docker or uninstalled later.

| Tool | How installed | Uninstall |
|------|---------------|-----------|
| Claude Code CLI 2.1.306 (needed for `claude plugin` commands) | Official installer: `curl -fsSL https://claude.ai/install.sh \| bash` → `~/.local/bin/claude` | `rm ~/.local/bin/claude && rm -rf ~/.local/share/claude` |
| Docker image `node:22-alpine` (Node 22 for building/previewing the site) | Pulled by `docker run` / `docker compose up` | `docker compose down && docker rmi node:22-alpine` |
| Eleventy 3.1.7 + deps | `npm install` inside the container → `node_modules/` in this folder (gitignored) | `rm -rf node_modules _site` |

Already on the machine before this project (not installed by us): Docker, git, gh.
