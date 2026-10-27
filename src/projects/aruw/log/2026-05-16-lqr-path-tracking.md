---
title: "Path tracking: from pure pursuit to LQR"
date: 2026-05-16 12:00:00
summary: "I led replacing the chassis's pure pursuit with LQR path tracking that models the robot's accelerations: within 3.2 cm of the path in simulation."
featured: true
portfolio: true
short: "LQR tracking"
skillTags: [Control systems, Technical leadership, C++]
loc: 1880
info:
  language: C++
  tools: [Eigen]
  hardware: Engineer robot
  role: Lead
  status: In simulation
links:
  - label: "Code"
    url: "https://github.com/EricJGoossen/LQRPathing/tree/999e391"
  - label: "The LQR study"
    url: "https://ieeexplore.ieee.org/document/9517448"
---
{# Confirmed by Eric (Oct 25). From Eric (Oct 24): led the feature from idea to implementation, wrote the proposal and gathered its resources; the driver-assist retargeting never happened and is left out. The MVP was finished by Claude on Oct 24 (EricJGoossen/LQRPathing, branch finish-mvp, commit e0212d7, 818 lines on Eric's framework of May 6-16; public since Oct 26 and linked at 999e391, where that MVP was merged as PR #1) and compared, in simulation, against a reimplementation of aruw-mcb's ChassisAutoNavController (pure pursuit: 0.2 m lookahead, speed ramped at 1 m/s^2). The simulated chassis's mass (20 kg), yaw inertia (0.6 kg m^2) and traction limit (4 m/s^2) are picked, not measured; both controllers get the same path and a 2 m/s top speed. Media: assets-src/aruw/generated/make_lqr_media.py. #}
{% row "images/lqr-vs-pure-pursuit.mp4", "Two dots racing along an S-shaped path with hairpin turns: the blue one, LQR, stays on the path; the orange one, pure pursuit, swings out in a loop at every hairpin and finishes later", { narrow: true, poster: "images/lqr-vs-pure-pursuit.jpg", caption: "The same slalom, the same simulated chassis and the same 2 m/s top speed: LQR (blue) against the team's pure pursuit (orange), in real time.", more: [{ src: "images/lqr-vs-pure-pursuit.svg", alt: "Bar charts for three paths: LQR finishes each sooner and stays within about 3 cm of the path, against 33 to 46 cm for pure pursuit", caption: "Three paths: LQR finishes 1.5 to 2.1 s sooner and stays within 3.2 cm of the path; pure pursuit strays up to 46 cm." }] } %}
Our chassis followed paths with pure pursuit: aim at a point a fixed distance down the path and ramp the speed up toward it. The robot's accelerations stay implicit in that, so it has no idea how hard it can brake or how fast it can take a corner, and at speed it swings wide of turns and overshoots where it should stop. I proposed replacing it with path tracking that models those accelerations explicitly, and led the feature from idea to implementation: I wrote the design and gathered the resources behind it, from spline fitting and arc-length reparametrization to the Riccati equation and [a study](https://ieeexplore.ieee.org/document/9517448) that found LQR tracks more accurately than pure pursuit. First, a cubic spline through the waypoints is reparametrized by arc length, the speed at each point is capped by its curvature, and a forward and a backward pass keep every speed-up and every stop within what the robot can deliver. Then an LQR tracks that profile on a world-frame model of the chassis, where its dynamics stay constant, and its force is rotated into the robot's frame. I designed it and built the framework; the comparison here runs the finished MVP against our pure pursuit in simulation.
{% endrow %}
