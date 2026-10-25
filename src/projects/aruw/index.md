---
layout: project.njk
title: Advanced Robotics at UW
org: "Advanced Robotics at UW"
timeline: Oct 2025 – present
tools: [C++, Python, ROS 2, Kalman filter, LQR, motion capture]
order: 4
# Card: the sentry in ARUW's 2026 robot reveal (YouTube FGh1yQdJGeM, 0:56, 1:07, 1:10). Hero: the side camera at our (red) end
# of "ARUW vs RoboGrinder | Match 113 | 3v3 ARC Championship 2026" (PqSzhmRSAZA, 16:40.5-16:46, round 3, game clock 4:29-4:24), the close side camera on the capture point, cropped to the hero box at full size. MP4s from Eric, Oct 25.
cover: images/cover-reveal.mp4
coverPoster: images/cover-reveal.jpg
hero: images/hero-match.mp4
heroPoster: images/hero-match.jpg
heroAlt: Our red robot fighting two blue robots on the capture point in round 3 of the 3v3 match against RoboGrinder at the 2026 ARC Championship, with the broadcast's damage numbers over them
heroFade: strong
heroSide: right
summary: Localization and control for ARUW's competition robots, from Kalman-filter odometry and LQR path tracking to measuring the sentry's localization against motion capture.
highlights:
  - label: Kalman-filter odometry
    entry: kalman-filter
    skills: [State estimation, C++]
  - label: LQR path tracking
    entry: lqr-path-tracking
    skills: [Control systems, Technical leadership, C++]
  - label: Odin error model
    entry: odin-error-model
    skills: [State estimation, Experiment design, Python]
  - label: Mocap pipeline
    entry: odin-characterization
    skills: [Experiment design, Python]
links:
  - label: ARUW
    url: https://aruw.org/
  - label: Team code (GitLab)
    url: https://gitlab.com/aruw/controls/aruw-mcb
  - label: Odin characterization
    url: https://github.com/EricJGoossen/odin-characterization
---
{# Confirmed by Eric (Oct 25). Hero and card (Eric, Oct 24-25): the match video for the hero, the robot reveal for the card. Round 2's footage is all from the distant overhead camera, which Eric found dull (Oct 25), so the hero was the side camera at our end of the field from round 1; Eric (Oct 25) asked for combat, so it is now round 3's close camera on the capture point, our red robot against two blue ones. Overview from Eric (Oct 24): started on controls; after the sentry's autonomous navigation struggled at the ARC robotics competition, moved to vision to fix it; this year owns the sentry's path planning and state machine, and wants to look at learning-based control to counter opponents. #}
I joined Advanced Robotics at UW, the university's RoboMaster team, as a control systems programmer: I reworked the chassis's Kalman-filter odometry for new odometry pods and led a rewrite of its path tracking from pure pursuit to LQR. At the ARC robotics competition, the sentry, our autonomous robot, didn't navigate as well as it needed to, so I switched to the vision team to be the one to fix that, starting by measuring exactly how good its localization is against motion capture. This year I own the sentry's path planning and state machine, and I want to look into learning-based control, so it can adapt to opponents as the match unfolds.
