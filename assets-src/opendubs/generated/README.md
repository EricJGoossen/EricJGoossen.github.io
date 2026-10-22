# OpenDubs: where the figures came from

Everything on the OpenDubs page that isn't a photo was made from Eric's own code
or data, in a cloud session, without changing any of his repositories.

## Optical flow vs mocap (`flow-ekf-vs-mocap.svg`)

- **Data:** the rosbag committed to `rajitzg/opendubs-core` in `391e3ec`
  ("fixes and rosbag", 2026-03-29), `bag_20260329_002904/temp_0.mcap`: 200 s of
  `/mavros/local_position/pose` (ArduPilot's EKF) and `/mocap/opendubs/pose`.
- **Analysis:** `scripts/flow_vs_mocap.py`. The EKF starts in its own frame, so its
  track is fitted to mocap (2D rotation + translation, no scale) over the first
  120 s, then compared over the whole run. Output: `data/flow-ekf-vs-mocap-2026-03-29.npz`.
- **Result:** within 0.74 m (mean 0.23 m) while the robot drove 5.5 m; after it
  spun ~205° in place, the estimate ran away to 155 m while the robot moved < 0.5 m.
  The cause isn't established here.

## Bimanual crossing clip (`bimanual-crossing.mp4`)

- **Code, unmodified:** `EricJGoossen/openarm` (HEAD, Sep 22), `EricJGoossen/mj_manipulator`
  at `de0ae13` (ArmGroup merge, Sep 21), `openarm_assets` at `31eebb9`,
  `mj_environment`, `ssik`; personalrobotics `pycbirrt` at `3401fd9` (v2.0.0, the last
  release before the rename to `sscbirrt`, which the fork still imports) and `tsr` at `a8607c3`.
- **Goal:** openarm's own adversarial pair, `_reach_into_other_workspace` in
  `tests/test_openarm_bimanual_planning.py`. That pair predates ArmGroup's 5 mm
  standoff, so planning runs with `collision_margin_mm = 0` (overlap only), as the README allows.
- **Scripts:** `scripts/plan_crossing.py` (plan with seed 0, check every sample of the
  plan and of the naive straight-line paths with the tests' `_cross_arm_contacts`)
  → `data/bimanual-crossing.npz`; `scripts/render_crossing.py` (MuJoCo offscreen, EGL,
  left arm blue, right arm orange, red outline while the arms intersect); ffmpeg
  hstack + labels, frames 135 onward, last frame held 1.5 s, 2× speed.
- **Result:** plan found in 1.4 s, 22.4 s long, 0 of 2,798 samples in contact;
  the straight-line paths intersect in 467 of 2,798.

## Sequential vs synchronized execution (`bimanual-sequential-vs-sync.svg`)

- `scripts/check_sequential.py` runs the crossing plan the way `mj_manipulator_ros`
  executed multi-arm plans before the bimanual refactor (`c7bedb6^`: one trajectory
  after the other) and checks every 4th sample with the same oracle
  → `data/bimanual-sequential.npz`. Left then right: 97 of 1,400 states intersect;
  right then left: 65 of 1,400; together: 0.
- `scripts/make_prl_charts.py data <images dir>` draws both charts with the Achilles
  `svgchart.py` helper.

## Photos and CAD renders

`thor-install.jpg`, `base-frame-cad.jpg`, `otos-housing-cad.jpg` and `lidar-mount-cad.jpg`
are from the lab's build guide (`UW-Allen-School-Robotics/opendubs`, `docs/assets/build/`),
resized. Placeholder: confirm they can be used here and who to credit.
