---
layout: project.njk
draft: true   # hidden from the site until this line is removed
title: Advanced Robotics at UW
org: "Advanced Robotics at UW"
timeline: Oct 2025 – present
tools: [C++, Python, ROS 2, Kalman filter, LQR, motion capture]
order: 4
summary: Control and localization for ARUW's competition robots, from Kalman-filter odometry and LQR path tracking to a mocap campaign that measures the sentry's localization.
highlights:
  - label: Localization campaign
    entry: odin-characterization
    skills: [State estimation, Python, Experiment design]
  - label: LQR path tracking
    entry: lqr-path-tracking
    skills: [C++]
links:
  - label: GitHub
    url: https://github.com/EricJGoossen/odin-characterization
---
{# Placeholder: Eric to confirm the whole page, and to add photos or video of the robots. Drafted from his resume and EricJGoossen/odin-characterization (Sep 28 – Oct 8, 2026; much of it written with Claude Code, per the commit authors) and EricJGoossen/LQRPathing (May 2026, private). The ARUW team code (aruw-mcb, project-otto) isn't in any repo this session can read. Needed: a cover and a hero (robot photos or competition footage). #}
I'm a control systems programmer on Advanced Robotics at UW, working on how the team's competition robots know where they are and how they follow a path. I implemented Kalman-filter odometry tuned on the physical robots, led a rewrite of path tracking on the embedded controller from pure pursuit to LQR, and built a motion-capture campaign that measures exactly how good the sentry's lidar-inertial localization is.
