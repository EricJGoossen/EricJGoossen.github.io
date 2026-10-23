---
title: Running both arms at once
date: 2026-09-01 19:59:00
skillTags: [Python, ROS 2, Motion planning]
---
{# Placeholder: Eric to confirm. Git: EricJGoossen/mj_manipulator_ros (bimanual refactor Sep 1, hardware fixes Sep 9 and 22), EricJGoossen/openarm (hardware validation stages Sep 7–9, thread-safety lock). The chart comes from the ArmGroup clip's plan run through the old sequential executor's schedule; see assets-src/opendubs/generated. #}
{% row "images/bimanual-sequential-vs-sync.svg", "Timeline chart of one 22.4-second bimanual plan executed three ways. Run left arm then right arm, it takes 44.8 seconds and red marks show the arms intersecting near the end. Run right then left, it also takes 44.8 seconds with intersections at the very end. Run together from one start stamp, it takes 22.4 seconds with no intersections", { caption: "The ArmGroup plan, executed one arm at a time and together, checked for contact at every step." } %}
A two-arm plan is only safe if both arms run it together, but on hardware they ran one after the other, doubling the time and passing through states the planner never checked: run that way, the crossing plan collides in 97 of 1,400. In [mj_manipulator_ros](https://github.com/EricJGoossen/mj_manipulator_ros), I made every arm start from its own thread on **one shared start stamp**, cancelling the rest if any arm fails.
{% endrow %}

{% row "placeholder", "Render: the arms colliding when the plan runs one arm at a time" %}
Running arms in parallel exposed two bugs: both arms spun ROS's one process-wide executor, and both threads updated the shared MuJoCo copy of the robot at once, crashing it. Each arm now has its own executor, and a lock guards the copy. To bring it up safely, I wrote an eight-stage, operator-gated hardware test suite, from CAN bring-up to a soak test.
{% endrow %}
