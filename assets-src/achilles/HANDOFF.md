# Achilles project page: handoff

Everything needed to finish the Achilles page at `/projects/achilles/`. Written 2026-10-22 from a long working session with Eric. This folder (`assets-src/`) is **not published**: it holds source material and media to pick from. Copy what you use into `src/projects/achilles/images/`.

Follow `AGENTS.md` for everything: work on `phase-1`, **never push or merge to `main`** ("upload to the website" means push `phase-1` so Cloudflare builds a preview; Eric merges to `main` himself), `npm run check` before every commit, no invented facts, `Placeholder` for anything unconfirmed, they/them for anyone whose pronouns aren't stated.

## What Eric asked for

- Finish the whole Achilles section: one progress-log entry per part below, in chronological order.
- **Pictures and graphs over words.** Each entry is short (about one paragraph) and carries at least one strong visual. Keep Eric's own paragraphs nearly as written: minimal, targeted edits only.
- Collect or make the media for each entry.
- When done, push `phase-1` and hand off with what changed and what still needs Eric.

## Site constraints that shape the media

- **No JavaScript** beyond `src/assets/js/skills.js` (and the CSP in `src/_headers` enforces it). The two interactive HTML pages here (`explainer/simd-soa-explainer.html`, `memviz/report-avx2.html`) can't be embedded. **Record them as short MP4 clips** (H.264, muted, under 5 MB, 1280 px wide or less) plus a still poster, and use `{% video %}`. A headless Chromium (e.g. Playwright) plus ffmpeg in the cloud environment works; anything installed there doesn't need logging (INSTALLED.md is only for Eric's machine).
- The `.svg` charts in `charts/` follow light/dark mode on their own when used as images. Use the plain versions (not `-light`/`-dark`) in Markdown: `![alt](images/x.svg)`.
- Images under ~1 MB, videos under 5 MB, nothing over 25 MB. Real alt text on everything.

## Project facts (verified)

| Fact | Source |
|---|---|
| Repo: https://github.com/EricJGoossen/Achilles (public). Language C++20. | GitHub |
| README: "A C++20 articulated rigid-body dynamics engine". Loads a jointed scene from a YAML `.arow` file, runs forward dynamics with the Articulated Body Algorithm, integrates at a fixed timestep, optional live OpenGL viewer. Algorithms are small typed Ops checked by C++20 concepts. | `README.md` on `main` |
| V2 design doc ("Achilles Porject plan") created 2026-03-04 | Eric's Google Drive |
| V2 commits 2026-04-05 → 2026-04-14 (first commit "Initial Commit", last "Added sensor code") | git |
| V3: PR #1 "v2 refactor" merged 2026-09-15 (+11,660/−2,467, 115 files); allocator #4 (09-18); integrators #5 (09-19); visualization #6 (09-19); README #8 (10-12); dynamics #9 (10-17); collisions #20 (10-18). A "cooking" commit on 2026-07-24 is the last V2-era work. | GitHub PRs |
| Version naming: the April code is **V2** (a deleted first attempt was V1); the September rewrite is **V3** even though its commit says "v2 refactor". Eric will add a short note about that in the V3 entry. | Eric |
| Motivation: ARUW's codebase had too much technical debt to integrate an off-the-shelf simulator, so Achilles is an in-house simulator meant to grow with it. Later goal: train an RL policy for ARUW without enough GPU compute, so V3 batches independent environments across SIMD lanes. | Eric; Eric's 2026-10-12 Drive summary |
| Dev machine: Intel Core Ultra 9 285H (48 KiB L1d 12-way, 3 MiB L2, 24 MiB L3) | measured |

## Entries to write (chronological)

Dates are the date the work happened. Use `npm run new:entry -- achilles "Title" YYYY-MM-DD`, delete the placeholder entries in `src/projects/achilles/log/`, and update `index.md` (summary, timeline, tools, links, highlights, cover).

### 1. Where it started (date: 2026-03-04, the design doc)
**Text (Eric's, final; keep as is):**
> The original inspiration for Achilles was that my club's codebase at Advanced Robotics at UW (ARUW) had gained so much technical debt that integrating an off-the-shelf simulator would have been extremely difficult. That's why I began developing Achilles: an in-house rigid body simulator that could grow with the codebase, rather than being forgotten as previous simulators had been. I was immediately overcome with inspiration and had to start programming. However, I didn't stop to design my system beforehand, so I learned about the systems I was modeling as I wrote, which resulted in a tangled mess. I decided to restart development entirely with Achilles V2, but before I did, I spent time architecting the system so I could follow proper software engineering practices.

**Visual:** `charts/achilles-initial-architecture.svg` (the V2 design doc as a chart: objects + the 6-step timestep loop). Eric was considering redrawing it by hand; if a hand drawing shows up in `assets-src/achilles/`, prefer it, captioned "Redrawn from my original design notes."

### 2. V2: types with physical meaning (date: 2026-04-14)
**Text (Eric's draft, lightly edited, not yet confirmed; keep the Placeholder on the IMU clause until Eric confirms):**
> A major part of my design philosophy for V2 was making sure every quantity had a physical meaning. Velocity, acceleration and force each had their own type, and they only combined in physically valid ways: an acceleration integrated into a velocity, and an inertia turned a force into an acceleration. Every link, joint and actuator also carried a typed frame, so frames belonging to different kinds of objects couldn't be mixed up. The core of this model was the joint system. Each joint is defined by its motion subspace S, and a CRTP template turns that into fixed-size math, including the articulated-inertia step, so each joint type can be specialized. Because Achilles was meant to model my club's robots, I also built sensor models, starting with an encoder, with Gaussian noise, Gauss–Markov drift, a low-pass filter and scale-factor error. But when I started planning collisions and rendering, I realized the rigid architecture and very specific type flow had built me into a corner.

Notes: the only sensor in the committed V2 code is an encoder. Eric mentioned an IMU, but there's no IMU file on GitHub, so keep "starting with an encoder" unless Eric confirms. Twists/wrenches did **not** carry frames in the April 14 code; frames lived on links, joints, actuators and transforms (the text above already says that).

**Visual:** `v2-revival/sensor_distortion.png`, the real V2 encoder models running (revived from the April 14 commit). Agreed tweaks before using it: top panel shows only "true" and "all combined"; title it "Simulated sensor errors on a swinging joint (Achilles V2)"; caption: "Each line is a V2 sensor model reading the same joint." The data is in the revival workspace on Eric's machine, so if regenerating isn't possible, use the PNG as is.

### 3. V3: designing for performance (date: 2026-09-15)
**Draft text (Claude's, from the design doc; Eric hasn't approved it, so keep it short and mark anything uncertain):**
> For V3, I wrote a full design document before writing any code. *(My commits call this the "v2 refactor"; the numbering got shuffled along the way.)* The target was concrete: simulate my club's six-robot arena of holonomic turret robots, and treat it as a performance learning exercise, seeing how fast the implementation could get rather than just making it work. One rule drove most decisions: only costs paid every frame matter. Only joint positions and velocities persist between frames; everything else is static data built at load or scratch memory rebuilt each step and reused between passes. In the code, that became fields, small operations that declare exactly which fields they read and write, and traversals that apply them across the joint tree, all checked at compile time. I kept V2's physically meaningful types, but moved them into the math rather than the structure, so adding collisions or rendering meant adding passes instead of rewiring classes.

Open with Eric: whether to credit that the design doc was worked out with Claude as a sounding board (his call; don't add it without asking).
**Visual:** `charts/achilles-v3-design.svg` (per-frame pass pipeline, data lifetimes, frame-arena reuse). Caption it "V3 as designed", since collisions changed later (see entry 8).

### 4. SIMD: structure of arrays, 8 robots per instruction (date: 2026-09-18 or a later SIMD milestone; check `git log` on Achilles `main`)
Eric's emphasis: show the **real system**, not an oversimplified animation, but make the SIMD idea obvious.
**Facts (measured with `tools/memviz`, Valgrind Lackey, 8 three-joint arms, one step):**
- Every field is stored as planar SoA: each component of each field is its own contiguous, aligned array across all joints (`engine/topology/layout_policy.hpp`, `PlanarLayout`).
- **88.9% of all accesses to simulation data are whole, aligned 8-lane vector loads or stores** (AVX2 build). Exceptions: some contact-solver row scalars and transform broadcasts in pair passes.
- `IntegrateVelocityOp` (q̇ += q̈·dt): every access to joint velocity/acceleration is 32 B = 8 floats in the AVX2 build (126 of 126 aligned; 42 + 42 loads, 42 stores = 6 components × 7 batches), and 16 B = 4 floats in the default SSE build (180 of 180; 6 × 10 batches).
- About 80% of all memory accesses in a step go to the stack (locals and register spills: a 6×6 matrix of batches is 36 registers' worth and AVX2 has 16), and they nearly all hit L1. Even simple ops use stack temporaries; likely cause (not verified): op bodies live in `.cpp` files and can't be inlined.
- The default build is SSE (4 lanes); 8 lanes need `-march=native` or `-mavx2 -mfma`.

**Visuals:**
1. Clip recorded from `explainer/simd-soa-explainer.html` (8-lane mode): SoA rows → vector registers → one multiply-add across 8 lanes → store. This is the "how it works".
2. Clip recorded from `memviz/report-avx2.html`: the real trace, with field blocks drawn as 8-lane bars lighting up as they're loaded and a ticker of real vector loads ("Joint velocity · component 2 of 6 · rows 8–15, one 32-byte load"). Record ~10–15 s around an ABA or integrator pass at 1× speed. This is the "proof from the real binary".
3. Optional: a small bar chart of access width (16 B SSE vs 32 B AVX2) from `memviz/summary-*.json` (`focus` and `by_region[].sizes`).

Link mention: the visualizer is Eric's own tooling (`tools/memviz/`, on a local branch `claude/memory-viz` not yet on GitHub; don't link it).

### 5. Dynamics: getting ABA right (date: 2026-10-17, PR #9)
**Facts:**
- V2 (revived from the 2026-04-14 commit and compared with MuJoCo 3.3, same torques, no gravity, 1 ms semi-implicit Euler): matches exactly when the mass sits on the joint axis, but a one-link arm swings **exactly 4× too fast** (free-body inverse inertia; missing the parallel-axis term), and a two-link arm diverges in shape (no frame transforms between links, no velocity-product terms, no gravity). Reviving it also turned up three latent bugs (CRTP call before the derived object exists, "zero" vectors that weren't zeroed under optimization, sensor code that never compiled).
- V3: full ABA with bias (Coriolis/centrifugal) terms, parent-to-body transforms, the joint's fixed placement and gravity as a fictitious base acceleration. Against MuJoCo 3.15 on the same scenes: **max joint-acceleration relative error 2.7e-6 to 3.5e-5**, and tip error 1e-4 to 1e-3 % of reach after 1 s (the arms are chaotic, so long-horizon trajectories diverge for both engines: compare "vs truth" columns).

**Visuals:** `v2-revival/v2_vs_mujoco.mp4` (V2's motion replayed in MuJoCo's renderer next to MuJoCo; it's labeled), `v2-revival/accuracy_arm.png` (the 4× error) or `accuracy_arm2.png`, and for V3 `bench-vs-mujoco/error_three_joint_arm.png` (or another `error_*.png`). Strong pairing: "V2 was 4× off; V3 agrees with MuJoCo to about 1e-5."

### 6. Renderer (date: 2026-09-19, PR #6)
**Facts:** GLFW + OpenGL debug viewer (`include/render/`, `src/render/`), drawn from the sim's own `viz` algorithm state; `achilles` binary opens it unless `--headless`. The design doc's rule: hand rendering to a library, don't hand-roll it.
**Visual:** a short clip of the viewer running. Eric recorded a demo on 2026-10-16; if that file is added to `assets-src/achilles/`, use it. Otherwise build Achilles `main` in the cloud with Xvfb + Mesa (software GL) and record `examples/three_joint_arm.arow` with ffmpeg `x11grab` for ~8 s. If neither works, leave a `{% placeholder %}` and list it for Eric.

### 7. Beating MuJoCo on throughput (date: 2026-10-11, the benchmark run)
**Facts** (`bench-vs-mujoco/README.md`, `throughput_summary.md`; single thread, dt 2 ms, Intel Core Ultra 9 285H, clang 14 `-O3`, MuJoCo 3.15.0 PyPI wheel stepping in C, contacts off):
- seven-joint arm, Euler: achilles f32 AVX2 **5.45M robot-steps/s** at N = 64 vs MuJoCo's best 1.66M → **3.3×**; ~3× from N = 16 up, about even at N = 1.
- three-joint arm, Euler: 12.5M vs 4.25M robot-steps/s → about 2.9–3.0×.
- f64 (MuJoCo's own precision): about 1.5–1.6×. SSE2 (default flags) is slower than AVX2 at large N but still ahead of MuJoCo.
- Accuracy as in entry 5.
- Eric's own one-liner (Drive, 2026-10-12): "Running 16 or more environments at once, it's 2–4× faster than single-threaded MuJoCo on articulated arms of 2 to 7 joints, while matching its joint accelerations to within 0.004% relative error. On a single laptop CPU core, that's over 5 million environment-steps per second for a 7-joint arm."

**Visual:** `bench-vs-mujoco/throughput.png`. Consider redrawing it in the site's style (one clean chart: robot-steps/s vs N for achilles f32 AVX2 vs MuJoCo best, seven-joint arm, log x) from `throughput_summary.md`.

### 8. Collision handling (date: 2026-10-18, PR #20)
**Facts:** the design doc planned cuRobo-style sphere colliders; the built version uses sphere-swept boxes with an occupancy-grid-free broad phase (`broad_phase`: swept-box world bounds → candidate-pair bitmask) and a MuJoCo/MJX-style narrow phase producing up to 4 contacts per pair (`README.md` architecture section). A contact solver followed (Eric's branch `EricG/collision-resolution`, "added contact solving", local, not on GitHub yet). In the memory trace, the contact solver is the heaviest part of a step with overlapping arms.
**Visual:** best is a viewer clip of something colliding (see entry 6 for how). Eric has an untracked `examples/robot_on_plane.arow` locally, so ask for it if needed. Fallback: a small diagram of broad phase → narrow phase → contacts in the same style as `charts/` (copy the SVG's `<style>` block for tokens).

## Highlights, skills, index.md

- `index.md`: title "Achilles"; summary along the lines of "A C++20 rigid-body simulator that steps 8 robots per SIMD instruction, about 3× MuJoCo's single-threaded throughput" (use only the measured numbers above); org: personal project / ARUW (ask, otherwise leave `org` empty); timeline "2026 – present"; tools [C++20, xsimd (SIMD), CMake, GoogleTest, OpenGL/GLFW, Valgrind, MuJoCo (benchmarks)]; links: `[GitHub](https://github.com/EricJGoossen/Achilles)`; cover: a still from the SIMD or viewer clip (video cover + `coverPoster` is allowed).
- Suggested highlights → entries: "SIMD batching" → entry 4; "Dynamics (ABA)" → entry 5; "3× MuJoCo" → entry 7; "Collisions" → entry 8.
- `skills.json` is still placeholder. Add real skills these highlights show (e.g. C++, SIMD, Rigid-body dynamics, Performance engineering), each with `best` pointing at the right entry, and keep the build passing. Other projects' placeholder highlights reference placeholder skills: either keep those skills or update those highlights so `npm run check` passes.

## Still needs Eric (list these in the handoff)

- Confirm the V2 paragraph (IMU claim) and the V3 draft.
- Whether to credit Claude for the V3 design-doc conversation.
- The 2026-10-16 viewer recording (or approval of a cloud-recorded clip).
- Whether the hand-drawn version of the first chart is coming.
- `org` for the project; resume and bio are separate tasks.
