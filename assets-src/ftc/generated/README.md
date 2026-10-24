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
