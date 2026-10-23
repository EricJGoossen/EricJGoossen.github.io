---
title: Optical flow odometry, checked against mocap
date: 2026-03-29 00:58:00
---
{# Placeholder: Eric to confirm. From Eric (Oct 23): he tuned the flow gain; the final error was 5 mm against motion capture, itself below what a person could measure by hand. Several flow sensors were tried; kept simple here on purpose. Teammates found the 90° mount missing from the config. Git: EricJGoossen/M5_stack_sensor_transfer (micro-ROS), EricJGoossen/open_dubs_mocap. The CAD render is from the lab's build guide. #}
{% row "placeholder", "Simulation: the flow sensor and the EKF on a simulated base" %}
Before the base could navigate, it had to know where it was. The first source was optical flow: a sensor that watches the floor slide past. I brought it up [over micro-ROS](https://github.com/EricJGoossen/M5_stack_sensor_transfer) and fed it into ArduPilot's EKF alongside the Pixhawk's IMU. It only read sensibly within about 10 cm of the floor, so it sits low, lit by its own LED.
{% endrow %}

{% row "placeholder", "Simulation: the estimate against ground truth, before and after the fix" %}
To measure it, I wrote [the package that brings the lab's motion capture into ROS](https://github.com/EricJGoossen/open_dubs_mocap), so both land in one bag. Early runs showed why that mattered: **driving 5.5 m, the estimate stayed within 0.74 m, but spinning in place sent it 155 m off.** Once teammates found the sensor's mounting missing from the config, I tuned the flow gain against mocap until **the estimate stayed within 5 mm of motion capture**, finer than you could measure by hand.
{% endrow %}
