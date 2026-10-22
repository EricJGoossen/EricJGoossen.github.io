---
layout: project.njk
draft: true   # hidden from the site until this line is removed
title: OpenDubs
org: "Personal Robotics Lab"
timeline: Oct 2025 – present
tools: [ROS 2, Python, C++, ArduPilot / MAVROS, Pinocchio, MuJoCo, Docker, WebXR]
order: 1
summary: A bimanual mobile manipulator for the Personal Robotics Lab, from drive and localization bring-up to two arms planned and run as one.
cover: images/bimanual-crossing.mp4
coverPoster: images/bimanual-crossing.jpg
# hero: images/hero.mp4     # Placeholder: real footage of the robot, subject on the right
highlights:
  - label: Flow vs mocap
    entry: optical-flow
    skills: [State estimation, ROS 2]
  - label: Merged lidar
    entry: lidar
    skills: [State estimation, ROS 2, Python]
  - label: Impedance control
    entry: impedance-control
    skills: [Impedance control, C++, ROS 2]
  - label: Quest teleop
    entry: teleop
    skills: [Teleoperation, Python]
  - label: N-arm planning
    entry: arm-group
    skills: [Motion planning, Python, MuJoCo]
links:
  - label: GitHub
    url: https://github.com/EricJGoossen/mj_manipulator
---
{# Placeholder: Eric to confirm the whole page. Drafted from his commits in rajitzg/opendubs-core, EricJGoossen/open_dubs_mocap, project_openDubs, the openarm_* repos and the mj_manipulator / mj_manipulator_ros forks, plus his resume. Which GitHub link(s) should the header show? The cover is a MuJoCo render (images/bimanual-crossing.mp4); swap in real robot footage when there is some. #}
OpenDubs is the Personal Robotics Lab's bimanual mobile manipulator: a holonomic mecanum base, an NVIDIA Jetson Thor and two 7-DOF OpenArm arms, granted by NVIDIA. I lead the four-person undergraduate team building its software, and I own base navigation, localization and arm control: each piece built in simulation first, then brought up on the hardware. Today the robot navigates point to point on its own, and both arms move in 3D under autonomous and teleoperated control.
