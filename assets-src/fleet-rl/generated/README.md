# Fleet RL generated media

`auto-reset-sim.mp4` (and its poster `auto-reset-sim.jpg`) on the automatic-reset entry is a
render of Eric's reset planner, not footage of the real arm.

1. `capture_reset.py` runs the planner from `fleet_so101_infra` (branch `EricG/automatic-reset`)
   through the repo's own mock-arm unit-test setup (`tests/unit/tasks/test_prop_reset.py`),
   records every joint command with its time, and saves four resets from four scrambled peg
   spots to an `.npz`. Run it from the fleet repo root with its dependencies installed.
2. `render_reset.py <reset.npz> <menagerie robotstudio_so101 dir> <out dir> [speed]` replays
   the commands on MuJoCo Menagerie's SO-101, whose joint chain matches the repo's kinematics,
   and writes frames; encode them with
   `ffmpeg -framerate 30 -i <out>/%05d.png -c:v libx264 -crf 26 -preset slow -pix_fmt yuv420p -an -movflags +faststart auto-reset-sim.mp4`.

The peg in the render is carried kinematically, so where it lands is only approximate (a few
millimetres); don't quote placement accuracy from it.

`peg-tag-guide.png`, `fleet-panorama.jpg` and `scene-cams-all.jpg` are copied from the fleet
repo's handbook (`handbook/assets/`). The panorama and scene cameras hold the hero and card
places until Eric picks his own.
