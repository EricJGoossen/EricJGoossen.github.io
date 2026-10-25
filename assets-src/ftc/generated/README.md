# FTC generated media

- `skidaddle-sim.mp4`, `skidaddle-sim.jpg`, `skidaddle-chart.png` (SKIDADDLE library entry):
  SKIDADDLE's own Swing simulator at commit 7d3240c (Oct 1, 2025), with `SIMULATING = true` in
  `Util/Constants.java`, run under Xvfb on the Bézier path (-48,-48) (-48,40) (48,-40) (48,48)
  with a -135° heading target. A small driver (`Render.java`, kept in the session scratchpad,
  not here) did what `UnitTests.splinePathTest` does, painted the field panel every 3 steps
  (0.03 s) and the chart panel at the end, with every series but `vel`, `accel` and `max` clicked
  off in its legend. Encoded at 100/3 fps, so the clip runs in real time.
- `skidaddle-pipeline.svg` (rework entry): `make_skidaddle_diagram.py`, drawn from the code at
  4b3fdb9. The reworked follower wasn't rendered: its `LinearController.running()` is stubbed to
  always true, so a run never finishes, and it overshoots its own speed limit.
- `live-view-demo.mp4`, `.jpg` (Live View entry): the demo video from the Live-View repo's history
  (`git show 406ded7:live_view_demo.mp4`; the README links the same video), cropped to the camera
  pane with `crop=560:440:610:110`, audio dropped, CRF 27.
- `skidaddle-hairpin.svg` (rework entry): `make_hairpin_compare.py data <out.svg>`. The traces in
  `data/` come from `harness/Compare.java` (Oct 25, 2026): Road Runner 1.0.1 core and Pedro
  Pathing 3.0.2 core built from their GitHub source, and SKIDADDLE at 1584b3b, all driving one
  simulated mecanum robot (per-axis DC motor model, |forward| + |strafe| <= 1, each wheel's grip
  |ax| + |ay| <= 50 in/s², 10 ms steps). Pedro was tuned with its ForesightTuner steps run on the
  sim; Road Runner and SKIDADDLE's tracking gains were picked by a grid search on a gentle S-curve.
  SKIDADDLE's planner and allocator run unchanged with `SIMULATING = false`, and its plan is
  tracked with feedforward plus a position term (its reworked controller never reports itself
  finished). `run.sh` shows the classpath; `-Damax=30` gives the lower-limit Road Runner run.
  `data/summary-accel*.csv` holds every path: on the 45° and 90° corners and the gentle curve,
  Road Runner at 30 in/s² tracked closer (0.1 to 0.2 in) but took longer. The 45° and diagonal
  paths need the allocator fix on Eric's local branch `fix-allocator-loop` (efed84b, not yet
  pushed); at 1584b3b they loop forever. The hairpin trace is the same with or without it.
- `hero-robot-demo.webp` (hero): `make_ftc_hero.py ../robot-demo-photo.jpg <out.webp>`. Eric's demo
  photo (Oct 25) cropped to the robot and Eric and centred on a transparent canvas with feathered
  edges, so the hero's strong fade leaves the whole robot visible.
