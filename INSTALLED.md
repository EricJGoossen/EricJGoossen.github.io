# Installed tools

Everything installed for this project, so it can be moved into Docker or uninstalled later.

| Tool | How installed | Uninstall |
|------|---------------|-----------|
| Claude Code CLI 2.1.306 (needed for `claude plugin` commands) | Official installer: `curl -fsSL https://claude.ai/install.sh \| bash` → `~/.local/bin/claude` | `rm ~/.local/bin/claude && rm -rf ~/.local/share/claude` |
| Docker image `node:22-alpine` (Node 22 for building/previewing the site) | Pulled by `docker run` / `docker compose up` | `docker compose down && docker rmi node:22-alpine` |
| Eleventy 3.1.7 + deps | `npm install` inside the container → `node_modules/` in this folder (gitignored) | `rm -rf node_modules _site` |

## Achilles V2 revival (`~/projects/TMP/achilles-v2-revival`)

| Tool | How installed | Uninstall |
|------|---------------|-----------|
| Docker image `achilles-v2-cpp` (~750 MB: Ubuntu 24.04 + g++, CMake, git, Valgrind) for compiling the April 2026 Achilles code | `docker build -t achilles-v2-cpp -f docker/cpp.Dockerfile docker` | `docker rmi achilles-v2-cpp ubuntu:24.04` |
| Docker image `achilles-v2-py` (~910 MB: Python 3.12 + MuJoCo 3.3.0, numpy, matplotlib, imageio/ffmpeg, OSMesa) for the MuJoCo comparison and video | `docker build -t achilles-v2-py -f docker/py.Dockerfile docker` | `docker rmi achilles-v2-py python:3.12-slim` |
| Eigen 3.4.0 source, downloaded by CMake during the V2 build | Inside `~/projects/TMP/achilles-v2-revival/build/` | `rm -rf ~/projects/TMP/achilles-v2-revival` (removes the whole revival workspace) |

Already on the machine before this project (not installed by us): Docker, git, gh.
