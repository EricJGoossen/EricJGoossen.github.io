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

## Page hero (`images/hero-handover.mp4`, `hero-handover.jpg`)

A two-arm handover of a can, planned with the unmodified ArmGroup planner (openarm's `Openarm`
wrapper around mj_manipulator) in the OpenArm model plus a table (`scripts/handover_scene.py`):
the right arm picks the can, both arms meet in one two-arm plan, the left arm takes it and sets
it down, then the same in mirror so the clip loops. The arms' motions are the planner's, checked
against the table and each other; the can is a prop that follows whichever gripper holds it.
Grasps are angled 45° inward at the handover, where an IK sweep found both arms' reach overlaps.

    python scripts/plan_handover.py handover.npz                    # about 15 minutes
    LOOKAT="0.30 -0.25 0.52" DIST=1.35 AZ=230 EL=-18 python scripts/render_handover.py handover.npz frames 5
    ffmpeg -framerate 30 -i frames/frame_%05d.png -c:v libx264 -crf 28 -preset slow -pix_fmt yuv420p -an -movflags +faststart hero-handover.mp4

(`scripts/render_hero.py` made the earlier hero, the crossing plan alone.)

## More renders

- `scripts/render_plan_extras.py data/bimanual-crossing.npz out`: `arm-group-strobe.jpg` (the
  ArmGroup plan at six moments, with both grippers' paths) and the frames of
  `parallel-arms-sequential.mp4` (the plan run left arm, then right, red while they intersect).
- `scripts/sim_teleop.py teleop.npz` then `scripts/render_teleop.py teleop.npz frames`:
  `teleop-sim.mp4`. Eric's teleop (`openarm.webxr_teleop` HandClutch, TeleopController, the event
  loop tick) run headless with two scripted hands in place of the headset's poses; the only
  changes are an alias so the headless sim context finds each arm by name, and no gripper toggles.
- `scripts/make_prl_charts.py data charts`: also `flow-paths.svg`, the March 29 run from above.
- `sim/scripts/render_stills.py tour.pkl out`: `sim-slam-map.png`, the finished map and path.

## Tile cover (`images/cover-arcs.jpg`)

A 3:2 crop (1170×780 at +830+150, scaled to 1200 wide) of the ARCS Night to Ignite photo of Eric
with the robot, cropped so only Eric and the robot are in it. Photo: Jason J. Kim Photography.
- `sim/scripts/render_urdf.py sim/urdf/opendubs_expanded_mujoco.urdf out.png`: `bringup-urdf.png`.
  Eric's `eric/open_dubs_description.urdf` expanded with xacro, plus a `<mujoco>` compiler tag
  so MuJoCo keeps the fixed links, drawn with every link's frame.
- `scripts/sim_gravcomp.py` then `scripts/render_gravcomp.py`: `impedance-gravcomp-sim.mp4`, and
  `make_prl_charts.py` makes `impedance-gravcomp-sim.svg` from `data/gravcomp-sim.npz`. An
  illustration, not Eric's controller: both arms hold one pose under the same made-up joint
  stiffness and damping (MIT-mode shaped); the right arm adds MuJoCo's gravity torques as the
  feedforward; at 3 s both wrists are pushed down with 15 N for 0.6 s.
