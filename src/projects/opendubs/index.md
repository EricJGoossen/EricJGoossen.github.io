---
layout: project.njk
draft: true   # hidden from the site until this line is removed
title: OpenDubs
org: "Personal Robotics Lab"
timeline: Oct 2025 – present
tools: [ROS 2, Python, C++, ArduPilot / MAVROS, Pinocchio, MuJoCo, Docker, WebXR]
order: 1
summary: A bimanual mobile manipulator for the Personal Robotics Lab, from drive and localization bring-up to two arms planned and run as one.
cover: images/cover-arcs.jpg   # Eric with the robot at ARCS Night to Ignite. Photo: Jason J. Kim Photography
hero: images/hero-handover.mp4
heroAlt: The robot's two OpenArm arms, one blue and one orange, passing a red can between them over a table and setting it down, rendered in MuJoCo
heroPoster: images/hero-handover.jpg
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
  - label: Arm code
    url: https://github.com/EricJGoossen/openarm_robot-code
  - label: OpenDubs
    url: https://github.com/UW-Allen-School-Robotics/opendubs
---
{# Placeholder: Eric to confirm the overview. Navigation only worked in simulation, so it isn't claimed here (the resume still does; Eric will handle it). UW-Allen-School-Robotics/opendubs is private as of Oct 23, so that link 404s for visitors until it's public. The hero is a MuJoCo render of a two-arm can handover planned with ArmGroup (assets-src/opendubs/generated/scripts/plan_handover.py; the can is carried kinematically). Eric wants to replace the tile photo eventually; cover-with-dubs.jpg (the robot with Dubs) is a candidate. #}
OpenDubs is the Personal Robotics Lab's bimanual mobile manipulator: a holonomic mecanum base, an NVIDIA Jetson Thor and two 7-DOF OpenArm arms, granted by NVIDIA. I'm on the four-person undergraduate team building its software, and I own base navigation, localization and arm control: each piece built in simulation first, then brought up on the hardware. Both arms now move in 3D under planned and teleoperated control, and I've led demos of the robot for industry visitors and donors.
