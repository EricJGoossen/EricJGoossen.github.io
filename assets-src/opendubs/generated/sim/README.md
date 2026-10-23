# OpenDubs lidar / SLAM / Nav2 replay in Gazebo

Eric asked for simulated media of his lidar and Nav2 work instead of real video. This folder
runs his code in Gazebo Harmonic and renders the result (`src/projects/opendubs/images/sim-slam-nav2.mp4`).

## What's his, unmodified (`eric/`)

From `rajitzg/opendubs-core` at `5d540e6` (Jun 2, 2026):

- `open_dubs_description.urdf`: the robot description (frame, four wheels, front and back lidar links).
- `lidar_merger.py`: the merger, run with the parameters from his `robot_params.yaml`
  (`target_frame: base_link`, `scan_output: /scan`, `min_range: 0.2`).
- `slam_toolbox_params.yaml`: his slam_toolbox settings.

## What's reconstructed for the sim

- `worlds/lab.sdf`: a made-up 10 m × 7 m lab room, not any real one.
- `urdf/opendubs_gz.urdf.xacro`: wraps his URDF with two simulated RPLIDAR A1s (360 samples,
  0.15–12 m, 7 Hz, 1 cm noise) and a body-velocity drive standing in for the mecanum wheels.
- `launch/sim.launch.py`: Gazebo, robot_state_publisher, the ros_gz bridge, his merger,
  slam_toolbox and Nav2. The robot's own visuals are hidden from its lidars: the sim draws his
  frame as one solid box, where the real frame is open rails the lidars mostly see through.
- `config/nav2_params.yaml`: Nav2's Jazzy defaults with the OpenDubs footprint, a holonomic (Omni)
  MPPI controller, and a lighter MPPI for a 4-core machine. His Nav2 config isn't in any repo.

## Running it

ROS 2 Jazzy with Nav2, slam_toolbox and ros_gz (the cloud run used RoboStack via micromamba,
since the ROS apt servers were unreachable):

    ros2 launch launch/sim.launch.py
    python3 scripts/tour.py tour.pkl                # Nav2 goals around the room, recorded at 5 Hz
    python3 scripts/render_tour.py tour.pkl frames 6  # top-down frames at 6x speed
    ffmpeg -framerate 10 -i frames/frame_%05d.png -vf scale=960:-2 -c:v libx264 -pix_fmt yuv420p -crf 26 sim-slam-nav2.mp4

## The recorded run

8 Nav2 goals, 7 succeeded. The first, a tight spot beside the west bench, timed out after
5 minutes; the clip starts at the second goal and covers the remaining 255 s at 6× speed.
