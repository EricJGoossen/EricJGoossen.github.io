---
title: "Arm control: three impedance controllers"
date: 2026-07-13 00:12:00
---
{# Placeholder: Eric to confirm. Sources: EricJGoossen/openarm_ros_controller (Jun 24–Jul 20: devcontainer, bring-up script, latency and effort-noise tests), openarm_cartesian_control (Jun 26–27), openarm_impedance_control (Jun 27–Sep 21). Why was each controller dropped (the commits only say "Switched back to joint space control only")? Latency test results are not in any repo (Slack?): add the numbers. The control rate went 500 Hz (Jun 27) → 750 Hz (Jul 13) → 400 Hz (Sep 9) in the config; the resume says 500 Hz. Which is right? Needs a video or plot of the arms, e.g. gravity comp holding a pose or tracking a trajectory. #}
{% placeholder "Video: an OpenArm holding a pose under gravity compensation" %}

Each OpenDubs arm is a 7-DOF OpenArm whose motors talk CAN-FD to the Thor. I started from the stock OpenArm ROS 2 stack, in a dev container with a script that brings up both CAN buses and builds the workspace, and wrote small tests that time a single trajectory goal from send to result, time a full pick motion, and measure how noisy the joints' torque readings are at rest. {# Placeholder: latency results #} Then I tried three ways to control the arms, each a ros2_control controller using Pinocchio for the arm's kinematics and dynamics:

1. **Cartesian impedance.** The gripper is pulled toward its target pose by a virtual spring and damper, turned into joint torques through the Jacobian (τ = Jᵀ(K·Δx + D·Δẋ)), plus gravity compensation, with a Cartesian trajectory action to stream targets.
2. **Joint impedance**, with the spring and damper on each joint instead, gravity compensation from Pinocchio's recursive Newton–Euler, and later a null-space term, gain clamping and torque and velocity limits.
3. **Gravity compensation over the motors' own PD.** The motors' onboard PD loops track the interpolated trajectory directly, and the controller adds only a gravity feedforward torque, checking every goal against joint, workspace and torque limits before accepting it and tripping if the estimated torque on any joint goes over.

The third is the one on the robot. {# Placeholder: why, in one or two sentences #}
