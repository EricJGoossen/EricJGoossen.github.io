---
title: "Path tracking: from pure pursuit to LQR"
date: 2026-05-16 12:00:00
---
{# Placeholder: Eric to write or confirm. From the resume: led the path-tracking rewrite on the embedded RTOS, replacing pure pursuit with LQR that models the robot's dynamics. EricJGoossen/LQRPathing (private, May 2026) holds the framework: paths, position and velocity state generators, an LQR state controller and an LQR autonav controller. The date is that repo's last commit. Needed: what the dynamics model is, how tracking improved, and a clip or plot of the robot following a path. #}
{% row "placeholder", "Video or plot: the robot following a path under LQR, beside pure pursuit" %}
Pure pursuit steers toward a point a fixed distance down the path and ignores how the robot actually responds, so it cuts corners and overshoots at speed. I led the rewrite of the team's path tracking to LQR, which plans with a model of the robot's dynamics and trades tracking error against control effort. Placeholder: the model, the gains, and what changed on the robot.
{% endrow %}
