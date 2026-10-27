---
title: "Actuators: closing the loop"
date: 2026-10-27 12:00:00
summary: "Motors a controller drives every step, shown balancing a ball on a tilting plate and checked against MuJoCo."
short: "Actuators"
skillTags: [Kinematics & Dynamics, C++, Simulation (MuJoCo)]
loc: 6303
info:
  language: [C++20, Python]
  tools: [MuJoCo]
  hardware: Laptop
  role: Solo
  status: On a branch
links:
  - label: "Code"
    url: "https://github.com/EricJGoossen/Achilles/tree/EricG/actuator-control"
---
{# From Eric (Oct 26): text, facts, line count and both media (~/projects/Achilles/media). The Code link is the EricG/actuator-control branch: pin it to a commit once his local commits (ball axis fix) are pushed or merged. #}
{% row "images/ball-balance.mp4", "A square plate on two pivots, viewed from above at an angle, with a ball on it. The plate starts tipped with the ball on its high corner; it tilts to catch the ball before it rolls off, brings it to the center, then rolls it around a figure-8", { caption: "Real time, rendered by the Achilles viewer: semi-implicit Euler at a 4 ms step. The controller sees only the delayed, noisy camera; the simulation sees only the two pivot torques." } %}
Until now, every torque in Achilles came from the scene file, so a robot could fall or collide but never react. Actuators let a controller outside the simulation push on a joint every step. An actuator is a direction in its joint's frame, an angular one for a torque or a linear one for a force. Attaching it projects that direction onto the joint's free axes once, so applying an effort later costs only a few multiply-adds into the joint-torque field. The simulation never owns or loops over actuators: each one is a small handle into that field, which is now double-buffered. A controller writes one half while the step reads the other, and the halves swap at the start of every step. An effort therefore acts over exactly the next step and is then gone, so a stale command can never leak into a later frame. Here, two actuators tilt a plate to balance a ball. The controller never sees the ball directly, only through a simulated camera that reports its position 30 times a second, 50 ms late, with 2 mm of noise. The plate can tilt no faster than 3 rad/s, about what a hobby servo manages. The plate starts tipped with the ball on its high corner, and the controller has to catch the ball before it rolls off, center it, then roll it around a figure-8.
{% endrow %}

{% row "images/actuation-vs-mujoco.png", "Two charts over 5 seconds for a six-joint arm. Top: each joint's angle following its own sine wave, between about -2 and 2 rad, with Achilles drawn dashed on top of MuJoCo and the lines indistinguishable. Bottom, log scale: the largest joint-angle difference. Achilles against MuJoCo stays around one millionth of a radian; MuJoCo against itself at a 100 times smaller step stays near a thousandth; MuJoCo with torques applied one step late swings up to about 1 rad", { chart: true, caption: "Every joint torque-driven by PD toward a sine, semi-implicit Euler at a 2 ms step. Achilles in float32, MuJoCo in float64." } %}
To check that an effort lands on exactly the step it was meant for, I drove a six-joint arm in both Achilles and MuJoCo 3.17. Every joint has an actuator running a PD loop toward its own sine wave, with torques up to 146 N·m. Both engines start from the same state at the same 2 ms step, and each step they read the joints, compute the torques, and apply them over the next step. Over 20 seconds, Achilles stays within 10⁻⁵ rad of MuJoCo under both semi-implicit Euler and RK4, which is float32 round-off, and the torques agree to 3×10⁻⁵. If the torques land one step late, MuJoCo ends up 1 to 2 rad away from its on-time run, so a timing slip would stand out by five orders of magnitude. The free-swinging arms in my throughput benchmark drifted apart after a few seconds because they're chaotic. Here the controller keeps pulling both arms back onto their targets, so the two engines stay together for the whole run.
{% endrow %}
