---
title: Running both arms at once
date: 2026-09-01 19:59:00
skillTags: [Python, ROS 2, Motion planning]
---
{# Placeholder: Eric to confirm. Git: EricJGoossen/mj_manipulator_ros (bimanual refactor Sep 1, hardware fixes Sep 9 and 22), EricJGoossen/openarm (hardware validation stages Sep 7–9, thread-safety lock). The chart is the ArmGroup crossing plan run through the old sequential schedule and together, with MuJoCo's signed distance between the closest left and right collision geoms (scripts/clearance.py). #}
{% row "images/parallel-clearance.svg", "Line chart of the closest distance between the two arms over time for one crossing plan. Run left then right or right then left, it takes 44.8 seconds and dips below zero, the arms overlapping, near the end. Run together from one start stamp, it finishes at 22.4 seconds without overlapping", { caption: "The same plan run the old way and together: how close the arms come, and when each run finishes.", more: [{ src: "images/parallel-arms-reach-out.mp4", poster: "images/parallel-arms-reach-out.jpg", alt: "On the robot, both arms extend out to the sides at the same time", caption: "Both arms moving at once on the robot, September 22." }] } %}
A two-arm plan is only safe if both arms run it together, but on hardware they ran one after the other, doubling the time and passing through states the planner never checked: run that way, the crossing plan collides in 97 of 1,400. In [mj_manipulator_ros](https://github.com/EricJGoossen/mj_manipulator_ros), I made every arm start from its own thread on **one shared start stamp**, cancelling the rest if any arm fails.
{% endrow %}
