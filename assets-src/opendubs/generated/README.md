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
it down, then the same in mirror so the clip loops. Each move is the planner's, then made direct: a
straight joint-space move when that is collision-free, otherwise the plan shortcut and splined, every
sample re-checked with the group's own collision checker (table, other arm, 5 mm margin), with
quintic timing so each move starts and stops smoothly. Single-arm moves (lifts, places, short
carries) use ArmGroup's Cartesian planner for a straight gripper line when it can follow one; an
arm with no goal holds still. The can is a prop the collision checker can't see; it turns with
the gripper holding it, and along a planned carry the holding wrist is re-solved at every
waypoint so the can stays level (within 4 degrees). A carry is rejected if the can would dip more
than 6 cm, tip past 35 degrees or swing well past the table's edge, and it is set down by its own
height. For the two-arm move the joint goals are chosen explicitly: the giver's nearest IK
solution, the taker's furthest from its joint limits, grasping unrolled (the gripper isn't
symmetric top to bottom; rolled, its hand meets the table first when setting the can down).
The taker grips 3.5 cm below the handover point so the two grippers keep 5 mm apart, carries the
can over the spot in a straight line (or through a few upright poses), and lowers it to the lowest
height where its hand clears the table; the can settles the last centimeter or two. The left spot
is (0.38, 0.12), inside the left arm's comfortable reach. Every grasp ends with both fingers
0.5 mm from the can. Each finger closes until it touches the
can (the two finger joints are independent, so neither sinks into it). The clip plays at 3x.
Grasps are angled 45° inward at the handover, where an IK sweep found both arms' reach overlaps.

    python scripts/plan_handover.py handover.npz                    # about 10 minutes
    LOOKAT="0.30 -0.25 0.52" DIST=1.35 AZ=230 EL=-18 python scripts/render_handover.py handover.npz frames 3
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

## Four impedance controllers in sim (`images/impedance-four-sim.mp4`)

Eric's four arm control laws, compiled unmodified from his repos into one library
(`armlaws/build_armlaws.sh`, the C interface in `armlaws/wrapper.cpp`) and called from a
MuJoCo loop at 500 Hz on the left OpenArm (the model's own gravity compensation and servos
turned off, torques applied directly):

| panel | law | repo @ commit |
|---|---|---|
| Cartesian | `CartesianImpedance`: J^T (K dx + D dxdot) + gravity | `openarm_cartesian_control` @ `3bf55b0` |
| joint space | `Impedance`: (J^T K J + I) (q* - q) + J^T D J (qd* - qd) + gravity | `openarm_impedance_control` @ `871d1e3` |
| null space | `ImpedanceLaw`: the Cartesian term plus a posture term projected into the null space | `openarm_impedance_control` @ `eb8e13a` |
| motors | `RobotModel::gravityTorqueRT` as the feedforward of the motors' PD (kp, kd from `control_gains.yaml`) | `openarm_impedance_control` @ `b517999` |

The URDF is `openarm_description`'s bimanual xacro (`arm_type:=openarm_v1.0 bimanual:=true
ros2_control:=false`). Pinocchio's gravity torques match MuJoCo's within 2% at the hold pose.
The gains are the demo's own (Cartesian K = 200 N/m, 4 N·m/rad; D = 20, 0.2; null space
K = 10, 2 N·m/rad), the same for the first three. Each arm is pushed with 20 N at the hand
(sideways, 1.0 to 1.6 s), then 20 N at the elbow across the shoulder-wrist line (its swivel,
4.0 to 4.6 s). Measured: Cartesian holds the hand to 3 mm but leaves the elbow 9.2 cm off;
joint space brings it back to 7 mm; null space to 1 mm; motors move the elbow 1.9 cm at most.

    build_armlaws.sh <venv> <prl dir> build
    python scripts/sim_impedance4.py build/libarmlaws.so openarm_bimanual.urdf impedance4.npz
    python scripts/render_impedance4.py impedance4.npz frames
    (ffmpeg 2x2 xstack with labels; see the command below)

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
