# Media and data generated on 2026-10-22

Made in a cloud container while finishing the Achilles page, from Achilles `main` (`feb1611`) plus the local tools below. Not published; the site uses copies in `src/projects/achilles/images/`.

## On the site

| Entry | Media | How it was made |
|---|---|---|
| Page hero (until 2026-10-22) | `media/double-pendulum.mp4` | Achilles viewer, `examples/two_joint_arm.arow` with the pivot raised to z = 2.2 (`scenes/two_joint_arm_raised.arow`), RK4 at 2 ms, Xvfb + Mesa software GL, frames read back with `glReadPixels` |
| Page hero | `hero-pendulum.mp4` | The same raw frames as `double-pendulum.mp4`, re-cropped (941×529 from the left edge, scaled to 1280×720) so the pivot sits at about two-thirds across, leaving the left side dark for the intro text |
| SIMD | `simd-lanes.svg` | `scripts/make_simd_lanes_chart.py` from `data/simd_lanes_cloud.json`: `achilles_bench throughput` on `claude/perf-vs-mujoco` (355a392), seven-link arm, Euler, 2 ms, built three ways from that branch with flags only (default SSE2; `-mavx2 -mfma`), xsimd 13.0.0, one core of a cloud Xeon @ 2.8 GHz, best of 2 × 9 trials. 1 robot 3.06 µs/step, 4 robots (SSE2) 4.26 µs, 8 robots (AVX2) 4.27 µs. A scalar (no-SIMD) build was tried through xsimd's `emulated<32>` backend, but xsimd 13 can't compile this code that way (its integer ops instantiate a 1-lane double register), so "1 robot" is the default build with three lanes idle |
| SIMD (second) | `simd-throughput.svg` | `scripts/make_simd_chart.py` from `bench-vs-mujoco/throughput_summary.md` (seven-link arm, Euler, f32 AVX2 and f32 SSE2 columns) |
| Viewer, home tile | `eight-pendulums.mp4` | `scenes/eight_pendulums.arow`: eight copies of the demo arm hung off a zero-DOF root, released 0.002 rad apart |
| MuJoCo | `speed-vs-mujoco.svg` | `scripts/make_perf_charts.py` from `bench-vs-mujoco/throughput_summary.md` (V3, N = 1 and N = 64, Euler), `v2-revival/REVIVAL_README.md` (V2) and, for V3 at one link only, `data/speed_vs_mujoco_cloud.json`: measured on a cloud Xeon core, not Eric's laptop (2.79× at 1 robot, 2.75× at 64; `scenes/one_joint_arm.arow`). The same run's 2/3/7-link ratios are within about 15% of the laptop's (1.88/1.45/1.03× at 1 robot, 3.0/3.4/4.3× at 64), so rerun the 1-link points on the laptop |
| (retired 2026-10-22, now `charts/`) | `achilles-vs-mujoco-error.svg` | `scripts/make_sbs_error_chart.py` from `data/dp_results.json` (`tip_err_achilles_rk4_vs_mujoco_rk4`), converted to mm: under 0.04 mm for 4 s, under 1 mm until about 6 s, 13 mm at 8 s |
| MuJoCo | `achilles-vs-mujoco.mp4` | Same raised scene in the Achilles viewer and in MuJoCo 3.15's renderer (`scripts/mj_render.py`, same camera), both RK4 at 2 ms, cut at 8 s |
| Dynamics | `dp-accel-error.svg` | `scripts/make_accel_chart.py` from `data/dp_results.json` (Achilles vs closed form only; the MuJoCo-vs-closed-form line was dropped, since it only shows float64 vs float32) |
| Integrators | `dp-energy.svg` | `scripts/analyze_dp.py` + `scripts/make_dp_charts.py` (below) |
| Collision detection | `collision-detection.mp4` | The `media/collisions.mp4` scene (see below) re-recorded closer in (`ACHILLES_CAM="0.3 0.18 2.8 0 0 2.05"`) at 125 fps of sim time (4 steps of 2 ms per frame), sim 1.6–5.4 s, played at 31.25 fps: 1/4 speed, 15 s |
| Collision response | `domino-amplifier.mp4`, `domino-timing.svg` | See "Dominoes" below |
| (retired 2026-10-22) | `contact-solver.mp4` | Eric's `EricG/collision-resolution` branch at `223af7c`, unmodified Release build, run exactly as `scripts/run-robot-demo.sh` runs it (Euler, 4 ms). Screen-captured at 60 fps under Xvfb with `x11grab -draw_mouse 0`; the camera was zoomed and orbited with the viewer's own mouse controls via `xdotool` while the process was paused (`scripts/rec_robot.sh 6 -50 -150 7`). Played at half speed, first 8 s |
| Collisions | `collision-vs-exact.svg` | `scripts/collide_vs_mujoco.py` + `scripts/collide_truth.py` + `scripts/make_coll_chart.py` (below) |

## Dominoes (`data/dominoes/`, `scenes/amp10.arow`, `scenes/dom14.arow`)

Free-floating plain boxes on a ground slab, in the format of Eric's `robot_on_plane.arow` (Y-up, gravity −y, `scenes/sim_config_y_up.yaml`), made by `scenes/make_scenes.py`. Run on Eric's `EricG/collision-resolution` branch at `223af7c`, **unmodified**, through `scripts/rec_driver.cpp`: a standalone program linked against that branch's Release `libachilles_lib.a` that steps a fixed sim time per frame, renders through the library's own viewer (frames read back from the X server) and logs every body's pose. Semi-implicit Euler, 2 ms (the only integrator with collisions there). MuJoCo 3.15 runs the same scene from the same file (`scripts/arow_boxes_to_mjcf.py`, mapped to Z-up; same boxes, masses, start state, Euler at 2 ms, pyramidal cones, default solref/solimp, the same margins).

- `amp10.arow`, the domino amplifier on the site: ten dominoes, each 1.2× the size of the last (0.3 kg to 41 kg, a 137× mass ratio). Tipping past 45° (250 Hz logs): Achilles and MuJoCo within 0–56 ms on every domino (1.204 vs 1.196 s for the first, 4.772 vs 4.828 s for the last). Resting angles at 7 s within 0.3°.
- `dom14.arow`: 14 equal dominoes. Within 0–72 ms on every domino, resting angles within 0.2°.
- Cost: this cloud core needs about 8 ms per step for the 14-domino scene (40 s of compute for 10 s of sim); MuJoCo runs it far faster. Not a number to publish.
- `scripts/mj_render_boxes.py` renders MuJoCo with the viewer's default camera; its frames line up with Achilles' frame for frame (not used on the site).

**Real-time recordings run slow.** Eric's viewer steps by wall-clock time, so a scene heavier than one core can simulate in real time plays back in slow motion. The retired `contact-solver.mp4` (robot_on_plane, screen-captured with `x11grab`) was labelled half speed but was slower than that; `rec_driver` avoids this.

## Not on the site (here if wanted)

- `media/double-pendulum.mp4` (+ poster): the earlier page hero.

- `media/simd-explainer.mp4`, `media/simd-memtrace.mp4` (+ posters): the explainer and memory-trace clips, replaced on the site by the throughput chart. Made with `scripts/rec_explainer.py` and `scripts/rec_memviz.py`.
- `media/collisions.mp4` (+ poster): two pendulums passing through each other with collision shapes and live contacts drawn on top, from before the contact solver; made with the recording tools patch.
- `charts/dp-accuracy-small-swing.svg`: outer-link error against the closed form for a 30° swing over 20 s. Euler: Achilles and MuJoCo identical (0.06–0.25 % of reach). RK4: MuJoCo (float64) near 1e-8 %, Achilles (float32) 2e-4 to 4.7e-3 % (about 65 µm on the 1.4 m arm), which is float32 round-off.

- `charts/dp-trajectory-error.svg`: outer-link position error against the closed form for the four integrators over 10 s. RK4 starts near 1e-6 % of reach, midpoint 1e-5 %, Verlet and Euler 1e-2 %; all saturate once chaos takes over (about 6–8 s).
- `charts/throughput-seven-link.svg`: robot-steps/s against N for the seven-link arm (Achilles f32 and f64 AVX2, MuJoCo best mode), from `throughput_summary.md`.

## Double pendulum results (`data/dp_results.json`)

`examples/two_joint_arm.arow`, released from horizontal, gravity down, dt = 2 ms (float32-rounded), Achilles default float build (SSE). Closed form = the Lagrangian equations of motion from `tests/examples_two_joint_arm.cpp`, integrated with SciPy DOP853 at rtol = atol = 1e-13.

- ABA joint accelerations vs closed form, every state of 20 s of RK4: max relative error 3.1e-6, median 1.6e-7. Vs MuJoCo 3.15 `qacc`: max 3.1e-6. MuJoCo vs closed form: max 4e-14.
- Max |E(t) − E(0)| over 0–10 s: Euler 0.56 J, Verlet 0.28 J, implicit midpoint 6.2e-4 J, RK4 8.3e-5 J (potential-energy range 16.7 J).
- Outer-link error vs closed form at 1 s / 5 s (% of reach): Euler 0.87 / 7.3, Verlet 0.33 / 3.7, midpoint 2.4e-4 / 0.18, RK4 6.0e-5 / 7.3e-3. MuJoCo Euler matches Achilles Euler; MuJoCo RK4 (double) is 2.6e-8 / 6.0e-6, so float32 RK4 is round-off limited.
- Achilles RK4 vs MuJoCo RK4 tip separation first exceeds 0.1 % of reach at 6.5 s and 1 % at 8.2 s.

## Collision results (`data/collision_results.json`)

1,800 random pairs, 300 each of sphere–sphere, sphere–capsule, capsule–capsule, sphere–box, capsule–box, box–box (sphere r = 0.25; capsule r = 0.12, half-length 0.35; box 0.3 × 0.18 × 0.1 half-extents), random orientations, contact margin 0.3. Each pair goes through the real `narrow_phase::ComputeSweptBoxContactOp`, one pair per SIMD lane (`patches/achilles-recording-tools.patch`, `tools/collision_probe.cpp`). Exact reference: convex QP for the distance between the inner boxes when separated, 15-axis SAT depth when overlapping, plus the sweep radii.

- Achilles vs exact: median |error| 2e-8, max 5.3e-5, over all 1,795 pairs it reported. The 5 it skipped are 0.302–0.310 apart, beyond the 0.3 margin.
- MuJoCo 3.15 vs exact: exact to 1e-16 for sphere and capsule pairs; more than 1e-4 off on 62 separated box–box pairs (up to 0.12) and 24 deeply overlapping capsule–box pairs (up to 0.28).

## Findings for the Achilles repo

0. **No scalar build (note for later).** Eric wants the engine to support a single lane with no SIMD at all, so the SIMD chart's "1 robot" bar can be a true no-SIMD baseline. Today xsimd 13's `emulated<32>` backend can't compile it (see the SIMD row above).

1. **Gravity sign in the example config.** `base_acceleration` is −gravity (Featherstone), so `examples/sim_config.yaml`'s `linear: [0, 0, -9.8]` is *upward* gravity, and the README's snippet says the same. The benchmark's MuJoCo converter also negated it, so the MuJoCo comparison was consistent (both pendulums "hung" upward), but the viewer showed arms falling up.
2. **Viewer was Y-up**, the simulation Z-up: the grid lay in the XZ plane, so gravity pointed along the floor.
3. **Example collision shapes sit half a link off.** `collision_pose` is the identity, so each rounded box is centered on its joint, while the viewer draws each box from the joint outward.
4. **Margin rule vs MuJoCo.** The narrow phase uses max(m_s, m_t), and its comment calls that MuJoCo's rule; MuJoCo 3.15 adds the two geom margins (checked: two spheres with margin 0.3 each make a contact at a gap of 0.5).

`patches/achilles-viewer-fixes.patch` fixes 1–3 as three commits (`git am` on `main`): Z-up camera and grid, `linear: [0, 0, 9.8]` plus the README snippet, and `collision_pose` offsets of 0.5 and 0.4. Achilles' own test suite passes with it in Debug: all 516 tests that run (one more is disabled upstream). Item 4 is a question, not a patch.

`patches/achilles-recording-tools.patch` is local-only tooling on top of the first two fix commits, not meant for upstream: environment-variable hooks for the camera, fixed-step recording and frame dumping, the contact overlay, `tools/achilles_trace.cpp` (the bench's `trace` format for current `main`) and `tools/collision_probe.cpp`.

## Rerunning

The scripts take the working directory as their first argument and expect `bench/` from Achilles' `claude/perf-vs-mujoco` branch next to them (for `arow_to_mjcf.py`). Python needs `mujoco==3.15.0 numpy scipy matplotlib pyyaml playwright glfw`; rendering MuJoCo headless needs `MUJOCO_GL=glfw` under Xvfb.
