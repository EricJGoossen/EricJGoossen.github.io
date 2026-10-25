---
title: Optical flow odometry, checked against mocap
date: 2026-03-29 00:58:00
summary: "Optical-flow odometry fed into ArduPilot's EKF, with a motion-capture pipeline to tune it until it stayed within 5 mm."
short: "Optical flow"
info:
  language: [C++, Python]
  tools: [micro-ROS, ArduPilot]
  hardware: [Pixhawk, M5Stack]
  role: Solo
  status: Retired
links:
  - label: "micro-ROS bridge"
    url: "https://github.com/EricJGoossen/M5_stack_sensor_transfer/tree/cdbf364"
  - label: "Mocap package"
    url: "https://github.com/EricJGoossen/open_dubs_mocap/tree/f8cd5d2"
---
{# Confirmed by Eric (Oct 25). From Eric (Oct 23): he tuned the flow gain; the final error was 5 mm against motion capture, which is itself more precise than anything measured by hand. Several flow sensors were tried; kept simple here on purpose. Teammates found the 90° mount missing from the config. Git: EricJGoossen/M5_stack_sensor_transfer (micro-ROS), EricJGoossen/open_dubs_mocap. The two charts are from an ArduPilot SITL re-creation (Oct 23), not robot data: see assets-src/opendubs/generated/sim/README.md. #}
{% row "images/flow-sim-paths.svg", "Top-down chart of a simulated drive: with the sensor's mounting missing from the config, the estimate heads 10 meters sideways while the robot drives 6 meters forward and back; with the mounting fixed, it follows the true path", { caption: "In simulation (ArduPilot SITL, flow only, the sensor 10 cm off the floor): with the mounting missing from the config, driving forward reads as driving sideways.", more: [{ src: "images/flow-sim-error.svg", alt: "Chart of simulated position error over time for three configurations: mounting missing, up to about 11 meters; mounting fixed, about 1 meter; flow gain tuned, about half a meter", caption: "The same simulated run, error over time for each config. On the robot, against mocap, the tuned estimate stayed within 5 mm." }] } %}
Before the base could navigate, it had to know where it was. The first source was optical flow: a sensor that watches the floor slide past. I brought it up [over micro-ROS](https://github.com/EricJGoossen/M5_stack_sensor_transfer) and fed it into ArduPilot's EKF alongside the IMU of the Pixhawk the base ran at the time. It only read sensibly within about 10 cm of the floor, so it sits low, lit by its own LED.

To tell whether it worked, I needed ground truth. The lab's motion capture tracks the robot more precisely than anything you could measure by hand, so I wrote [the package that brings it into ROS](https://github.com/EricJGoossen/open_dubs_mocap): the EKF's estimate and the mocap pose land in one bag on one clock, and every run can be compared with the truth point by point. The first runs showed why that mattered: driving 5.5 m, the estimate stayed within 0.74 m of mocap, but spinning in place sent it 155 m off. Once teammates found the sensor's mounting missing from the config, I tuned the flow gain against mocap, run by run, until **the estimate stayed within 5 mm of motion capture.**
{% endrow %}
