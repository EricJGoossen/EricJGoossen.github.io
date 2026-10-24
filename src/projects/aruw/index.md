---
layout: project.njk
draft: true   # hidden from the site until this line is removed
title: Advanced Robotics at UW
org: "Advanced Robotics at UW"
timeline: Oct 2025 – present
tools: [C++, Python, ROS 2, Kalman filter, LQR, motion capture]
order: 4
summary: Localization and control for ARUW's competition robots, from Kalman-filter odometry and LQR path tracking to measuring the sentry's localization against motion capture.
highlights:
  - label: Kalman-filter odometry
    entry: kalman-filter
    skills: [State estimation, C++]
  - label: Odin error model
    entry: odin-error-model
    skills: [State estimation, Experiment design, Python]
  - label: LQR path tracking
    entry: lqr-path-tracking
    skills: [C++, Control systems]
links:
  - label: ARUW
    url: https://aruw.org/
  - label: Team code (GitLab)
    url: https://gitlab.com/aruw/controls/aruw-mcb
  - label: Odin characterization
    url: https://github.com/EricJGoossen/odin-characterization
---
{# Placeholder: Eric to confirm the whole page; the card image is his to add. Hero (Eric, Oct 24): round 2 of his favorite match from the last competition (https://www.youtube.com/watch?v=PqSzhmRSAZA, a best of three), or clips from the robot reveal (https://www.youtube.com/watch?v=FGh1yQdJGeM); try both once the videos can be downloaded. Overview from Eric (Oct 24): started on controls; after the sentry's autonomous navigation struggled at the ARC robotics competition, moved to vision to fix it; this year owns the sentry's path planning and state machine, and wants to look at learning-based control to counter opponents. #}
I joined Advanced Robotics at UW, the university's RoboMaster team, as a control systems programmer: I reworked the chassis's Kalman-filter odometry for new odometry pods and led a rewrite of its path tracking from pure pursuit to LQR. At the ARC robotics competition, the sentry, our autonomous robot, didn't navigate as well as it needed to, so I switched to the vision team to be the one to fix that, starting by measuring exactly how good its localization is against motion capture. This year I own the sentry's path planning and state machine, and I want to look into learning-based control, so it can adapt to opponents as the match unfolds.
