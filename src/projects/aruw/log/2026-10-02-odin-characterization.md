---
title: A test platform against motion capture
date: 2026-10-02 12:00:00
info:
  language: Python
  tools: [OptiTrack motion capture, UDP]
  hardware: [Odin1, NVIDIA Jetson, the sentry]
  role: Solo
  status: Ran the October 3 campaign
links:
  - label: "Code"
    url: "https://github.com/EricJGoossen/odin-characterization/tree/aa1cefe"
---
{# Placeholder: Eric to confirm. From EricJGoossen/odin-characterization (Sep 28 – Oct 8) and Eric's Oct 24 notes: the characterization was to decide whether the sentry could rely on the Odin alone for localization, and to find its weak points; mocap (OptiTrack, 360 Hz) is the reference. The diagram and the day-1 schedule are drawn from the repo's README and scripts/estimate_time.py; see assets-src/aruw/generated. #}
{% row "images/odin-system.svg", "Diagram of the system: motion capture and the Odin1 sensor feed the characterization scripts, which record every run and write a report; in autonomous mode they send chassis velocities over UDP to the Jetson, which forwards them over UART to the sentry's motor control board", { caption: "The three parts, and the default human-driven mode.", more: [{ src: "images/odin-day1.svg", alt: "Bar timeline of day 1: preflight 8 minutes, calibration 3, mapping 5, figure-8 laps 6, holds 41, latency 3, cold starts 16, outages 11; 93 minutes in all", caption: "Day 1, step by step, from the campaign's time estimate." }] } %}
The sentry localizes with an Odin1, a lidar-inertial sensor that relocalizes into a prebuilt map. Before the team decided whether the whole localization system could rely on it alone, we wanted to know how accurate it is and where it is weak. So I built [a test platform](https://github.com/EricJGoossen/odin-characterization) that measures it against the motion capture room, whose OptiTrack tracks the robot to a fraction of a millimeter. It starts and stops the sensor, records every run, guides whoever is driving with live mocap feedback, and can also drive the robot itself through the Jetson and the robot's controller, with a watchdog and speed caps. A campaign day runs a fixed protocol: calibration spins, a mapping drive, figure-8 laps at set speeds, ten-minute holds, back-and-forth motion to measure latency, cold starts, and outages where someone covers the sensor.
{% endrow %}
