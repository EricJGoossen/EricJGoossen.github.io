---
title: "Arm control: three impedance controllers, then a simpler one"
date: 2026-07-13 00:12:00
---
{# Placeholder: Eric to confirm the rewrite. From Eric (Oct 23): three controllers before settling on forwarding (reasons as written below); 500 Hz on the robot (the repo config is out of date). Note: in Slack (Jul) Eric wrote "I confirmed the control loop runs at 750 hz", which matches the Jul 13 config; 500 Hz is used here per Eric. Latency numbers are the ones Eric posted in Slack: 2.55 ms to goal acceptance and 63.21 ms to finish a single-iteration move (averaged), and 47 ms from a command on one arm to the torque spike on the other (5 runs, standard deviation 4.7 ms). The motors are Damiao DM-J4310s in MIT mode. Sources: EricJGoossen/openarm_ros_controller, openarm_cartesian_control, openarm_impedance_control. A video of the arms (gravity comp holding a pose, or tracking a trajectory) would replace the gray box. #}
{% placeholder "Video: an OpenArm holding a pose under gravity compensation" %}

Each OpenDubs arm is a 7-DOF OpenArm whose Damiao motors talk CAN-FD to the Thor. The motors run their own impedance loop in MIT mode: the host sends position, velocity and torque targets with gains, and the motor closes the loop internally, reporting torque from its measured current. I started from the stock OpenArm ROS 2 stack, in a dev container with a script that brings up both CAN buses, and measured its latency first. A trajectory goal is accepted in 2.55 ms on average, and a single-step move finishes in 63 ms. To time the whole loop, I had both arms grasp a light block and one arm pull on it: **47 ms passes between the command and the torque spike in the other arm's reading**, with a standard deviation of 4.7 ms over five runs.

Then I wrote three impedance controllers as ros2_control plugins, using Pinocchio for the arm's kinematics and dynamics, before settling on a fourth:

1. **Cartesian impedance.** The gripper is pulled toward its target by a virtual spring and damper, turned into joint torques through the Jacobian (τ = Jᵀ(K·Δx + D·Δẋ)). On a 7-DOF arm that leaves one degree of freedom, the null space, uncontrolled, so the elbow could drift off the path the planner had checked for collisions.
2. **Cartesian and joint impedance together**, meant to cancel each other so the joint controller handled the null space and the Cartesian one the gripper's axes. Numerical slop kept them from cancelling cleanly.
3. **Null-space control**: Cartesian impedance plus a null-space term pulling the redundant joint back onto the collision-checked path, with its own gains.
4. **Forwarding**, which is what runs on the robot. The planned joint trajectory goes straight to the motors' own impedance loops, and the controller adds a gravity-compensation torque from Pinocchio's recursive Newton–Euler at 500 Hz. It checks every goal against joint, workspace and torque limits before accepting it, and trips if the estimated torque on any joint goes over.
