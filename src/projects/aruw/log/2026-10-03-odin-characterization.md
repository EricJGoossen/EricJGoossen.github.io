---
title: Measuring the sentry's localization against motion capture
date: 2026-10-03 12:00:00
---
{# Placeholder: Eric to confirm. From EricJGoossen/odin-characterization (Sep 28 – Oct 8). The diagram, the course and the schedule are drawn from the repo's README, config/campaign.yaml (with the repo's own path functions) and scripts/estimate_time.py; see assets-src/aruw/generated. Needed: a photo of the sentry with the Odin1 on its turret, and the mocap room. #}
{% row "images/odin-system.svg", "Diagram of the system: motion capture and the Odin1 sensor feed the characterization scripts, which record every run and write a report; in autonomous mode they send chassis velocities over UDP to the Jetson, which forwards them over UART to the sentry's motor control board", { caption: "The three parts, and the default human-driven mode." } %}
To know how far to trust the sentry's lidar-inertial sensor, an Odin1, I built [a sensor-agnostic pipeline](https://github.com/EricJGoossen/odin-characterization) that measures it against the motion capture room. It starts and stops the sensor, records every run, and guides whoever is driving with live mocap feedback. It can also drive the robot itself, through the Jetson and the robot's controller, with a watchdog and speed caps.
{% endrow %}

{% row "images/odin-course.svg", "Top-down plan of the campaign: a geofence, mapping lanes, a figure-8 and four hold spots facing different ways", { caption: "The course, from the campaign config.", more: [{ src: "images/odin-day1.svg", alt: "Bar timeline of day 1: preflight 8 minutes, calibration 3, mapping 5, figure-8 laps 6, holds 41, latency 3, cold starts 16, outages 11; 93 minutes in all", caption: "Day 1, step by step, from the campaign's time estimate." }] } %}
A campaign day runs a fixed protocol: calibration spins, a mapping drive, figure-8 laps at set speeds, ten-minute holds at four spots, back-and-forth motion to measure latency, 24 cold starts, and outages where someone covers the sensor. From that, the analysis fits an error model. Placeholder: the model's result, 5.1 cm horizontal, 0.6 cm vertical and under 0.5° from the resume, with how it was validated.
{% endrow %}
