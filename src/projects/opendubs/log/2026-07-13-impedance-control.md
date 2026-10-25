---
title: "Arm control: three impedance controllers, then a simpler one"
date: 2026-07-13 00:12:00
info:
  language: C++
  tools: [Pinocchio, ROS 2, MuJoCo]
  hardware: [OpenArm (Damiao motors over CAN-FD), NVIDIA Jetson Thor]
  role: Solo
  status: The simpler controller runs on the robot
links:
  - label: "Cartesian control"
    url: "https://github.com/EricJGoossen/openarm_cartesian_control/tree/176f011"
  - label: "Joint and null-space control"
    url: "https://github.com/EricJGoossen/openarm_impedance_control/tree/bea0dfa"
---
{# Placeholder: Eric to confirm. From Eric (Oct 23): three controllers before settling on forwarding; 500 Hz. Latency numbers are from Eric's Slack posts (2.55 ms to goal acceptance; 47 ms command-to-torque-spike across arms, 5 runs, standard deviation 4.7 ms). Motors: Damiao DM-J4310 in MIT mode. Git: EricJGoossen/openarm_cartesian_control, openarm_impedance_control (public), openarm_ros_controller (visibility unknown, not linked). The sim video (Oct 24) runs his four control laws unmodified through a fast reach, a push at the almost straight arm and a sideways elbow push; its gains and the one-cycle delay of the Thor-side loops are the demo's own, not measured; see assets-src/opendubs/generated/README.md. From Eric (Oct 23): all three clips (combined into one video) are his Cartesian impedance controller (gravity compensation only; stiff in x and y, compliant in z and rotation; stiff in x and y, compliant in rotation).  From Eric (Oct 24): the goal was axial compliance in Cartesian space; the combined controller was joint-space impedance with the Cartesian terms subtracted, dropped for numerical instability; the null-space controller was dropped for the motors' lower latency; limits are checked in joint and Cartesian space (FK). #}
{% row "images/impedance-control-clips.mp4", "Three clips of a hand pushing one of the robot's arms: on the top left the arm gives way and holds its new pose, on the top right the wrist holds its place sideways but gives way up and down and in rotation, and below the gripper holds its position but turns freely", { poster: "images/impedance-control-clips.jpg", wide: true, caption: "My Cartesian impedance controller on the robot: gravity compensation only (June 26), stiff in x and y but compliant in z and rotation, and stiff in x and y but compliant in rotation.", more: [{ src: "images/impedance-four-sim.mp4", poster: "images/impedance-four-sim.jpg", alt: "Four simulated arms, one per controller, reaching out fast, pushed down at the elbow, reaching back and pushed sideways; a live readout shows each one's distance from its plan. The motor-loop arm stays on the plan; the others trail it, and the Cartesian one is left bent", caption: "The four controllers in MuJoCo, built unchanged from their repos (faint arm: the plan). On the reaches the motors' own loop stays within about 2 cm of the plan while the others trail by 7 to 18 cm; near the straight arm the Cartesian one stays folded once pushed. Demo gains." }] } %}
Each arm is a 7-DOF OpenArm whose Damiao motors run their own impedance loop: the Thor sends position, velocity and torque targets with gains over CAN-FD, and each motor closes the loop itself. I measured the stock ROS 2 stack first. A goal is accepted in 2.55 ms, and with both arms holding one block, **47 ms passes between a command to one arm and the torque spike in the other** (σ = 4.7 ms).

What I was after was axial compliance in Cartesian space: a gripper that holds firm along some axes and gives along others. I wrote three controllers with Pinocchio to get it ([Cartesian](https://github.com/EricJGoossen/openarm_cartesian_control), [joint and null space](https://github.com/EricJGoossen/openarm_impedance_control)). Pure Cartesian impedance gave that compliance, but it left the redundant elbow free to drift off the collision-checked path. The combined controller ran joint-space impedance and subtracted the Cartesian terms from it, keeping the axial compliance and control of the null space, but it was numerically unstable. The null-space controller worked, but I switched off it for the much lower latency of the motors' own impedance loops: in the end we gave up Cartesian compliance for speed.

What I settled on is simpler: the planned trajectory goes straight to the motors, plus gravity compensation at 500 Hz from Pinocchio's RNEA (the recursive Newton-Euler algorithm), with every goal checked against position and torque limits in both joint space and Cartesian space (through forward kinematics).
{% endrow %}
