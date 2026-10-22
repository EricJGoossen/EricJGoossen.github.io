# Media and data generated on 2026-10-22

Made in a cloud container while finishing the Achilles page, from Achilles `main` (`feb1611`) plus the local tools below. Not published; the site uses copies in `src/projects/achilles/images/`.

## On the site

| Entry | Media | How it was made |
|---|---|---|
| Page hero | `double-pendulum.mp4` | Achilles viewer, `examples/two_joint_arm.arow` with the pivot raised to z = 2.2 (`scenes/two_joint_arm_raised.arow`), RK4 at 2 ms, Xvfb + Mesa software GL, frames read back with `glReadPixels` |
| SIMD | `simd-explainer.mp4` | `explainer/simd-soa-explainer.html`, 8-lane mode, at 1/1.3 speed on a fake clock (`scripts/rec_explainer.py`); the register-spill step is skipped |
| SIMD | `simd-memtrace.mp4` | `memviz/report-avx2.html`, all 400 frames of the recorded step at 1× (`scripts/rec_memviz.py`), cropped to the headline numbers, ticker and shared-state blocks |
| Viewer, home tile | `eight-pendulums.mp4` | `scenes/eight_pendulums.arow`: eight copies of the demo arm hung off a zero-DOF root, released 0.002 rad apart |
| MuJoCo | `speed-vs-mujoco.svg` | `scripts/make_perf_charts.py` from `bench-vs-mujoco/throughput_summary.md` (V3, N = 1 and N = 64, Euler) and `v2-revival/REVIVAL_README.md` (V2) |
| MuJoCo | `achilles-vs-mujoco.mp4` | Same raised scene in the Achilles viewer and in MuJoCo 3.15's renderer (`scripts/mj_render.py`, same camera), both RK4 at 2 ms, cut at 8 s |
| Dynamics | `dp-accel-error.svg`, `dp-energy.svg` | `scripts/analyze_dp.py` + `scripts/make_dp_charts.py` (below) |
| Collisions | `collisions.mp4` | `scenes/two_arms_collide.arow`, Euler at 2 ms (the only integrator that runs the collision passes), half speed, with collision shapes and live narrow-phase contacts drawn on top |
| Collisions | `collision-vs-exact.svg` | `scripts/collide_vs_mujoco.py` + `scripts/collide_truth.py` + `scripts/make_coll_chart.py` (below) |

## Not on the site (here if wanted)

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

1. **Gravity sign in the example config.** `base_acceleration` is −gravity (Featherstone), so `examples/sim_config.yaml`'s `linear: [0, 0, -9.8]` is *upward* gravity, and the README's snippet says the same. The benchmark's MuJoCo converter also negated it, so the MuJoCo comparison was consistent (both pendulums "hung" upward), but the viewer showed arms falling up.
2. **Viewer was Y-up**, the simulation Z-up: the grid lay in the XZ plane, so gravity pointed along the floor.
3. **Example collision shapes sit half a link off.** `collision_pose` is the identity, so each rounded box is centered on its joint, while the viewer draws each box from the joint outward.
4. **Margin rule vs MuJoCo.** The narrow phase uses max(m_s, m_t), and its comment calls that MuJoCo's rule; MuJoCo 3.15 adds the two geom margins (checked: two spheres with margin 0.3 each make a contact at a gap of 0.5).

`patches/achilles-viewer-fixes.patch` fixes 1–3 as three commits (`git am` on `main`): Z-up camera and grid, `linear: [0, 0, 9.8]` plus the README snippet, and `collision_pose` offsets of 0.5 and 0.4. Achilles' own test suite passes with it in Debug: all 516 tests that run (one more is disabled upstream). Item 4 is a question, not a patch.

`patches/achilles-recording-tools.patch` is local-only tooling on top of the first two fix commits, not meant for upstream: environment-variable hooks for the camera, fixed-step recording and frame dumping, the contact overlay, `tools/achilles_trace.cpp` (the bench's `trace` format for current `main`) and `tools/collision_probe.cpp`.

## Rerunning

The scripts take the working directory as their first argument and expect `bench/` from Achilles' `claude/perf-vs-mujoco` branch next to them (for `arow_to_mjcf.py`). Python needs `mujoco==3.15.0 numpy scipy matplotlib pyyaml playwright glfw`; rendering MuJoCo headless needs `MUJOCO_GL=glfw` under Xvfb.
