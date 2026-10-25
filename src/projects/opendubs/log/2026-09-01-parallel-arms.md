---
title: Running both arms at once
date: 2026-09-01 19:59:00
summary: "Both arms start a plan from one shared timestamp, halving the run time and staying inside what the planner checked."
short: "Parallel arms"
info:
  language: Python
  tools: [ROS 2, MuJoCo]
  hardware: 2× OpenArm
  role: Solo
  status: On the robot
skillTags: [Python, ROS 2, Motion planning]
links:
  - label: "Bimanual refactor"
    url: "https://github.com/EricJGoossen/mj_manipulator_ros/commit/c7bedb6"
---
{# Confirmed by Eric (Oct 25). Git: EricJGoossen/mj_manipulator_ros (bimanual refactor Sep 1, hardware fixes Sep 9 and 22), EricJGoossen/openarm (hardware validation stages Sep 7–9, thread-safety lock). The chart is the ArmGroup crossing plan run through the old sequential schedule and together, with MuJoCo's signed distance between the closest left and right collision geoms (scripts/clearance.py).  97 of 1,400: scripts/check_sequential.py replays the crossing plan the old way (left arm, then right) and checks every 4th of the 2,798 samples with openarm's contact oracle. Thread safety: Openarm._sim_step_lock (openarm, Sep 9) serializes the two arms' threads' access to the shared MuJoCo model and data after concurrent runs segfaulted. From Eric (Oct 24): mention only that he built a HIL bring-up protocol, not its stages or the soak test. #}
{% row "images/parallel-clearance.svg", "Line chart of the closest distance between the two arms over time for one crossing plan. Run left then right or right then left, it takes 44.8 seconds and dips below zero, the arms overlapping, near the end. Run together from one start stamp, it finishes at 22.4 seconds without overlapping", { caption: "The same plan run the old way and together: how close the arms come, and when each run finishes.", more: [{ src: "images/parallel-arms-reach-out.mp4", poster: "images/parallel-arms-reach-out.jpg", alt: "On the robot, both arms extend out to the sides at the same time", caption: "Both arms moving at once on the robot, September 22." }] } %}
A two-arm plan is only safe if both arms run it together: it was checked with each arm where the other would be at the same instant. On hardware, though, [mj_manipulator_ros](https://github.com/EricJGoossen/mj_manipulator_ros), the lab's layer that runs those plans on the robot, ran multi-arm plans one arm after the other, which doubled the time and passed through states the planner never checked. Replaying the crossing plan that way in MuJoCo and checking every fourth of its states, the arms intersect in **97 of 1,400.**

I rebuilt execution so every arm starts its trajectory on **one shared start stamp**: the trajectories must share their timestamps, one stamp a moment in the future is computed once, and each arm sends its goal from its own thread against that stamp, so the motors start together however long each goal takes to send. If any arm fails or is aborted, a shared event cancels the others mid-motion. Running two arms from two threads also meant making the shared code thread-safe: both threads stepped one MuJoCo model, and concurrent runs crashed until I serialized every access to it behind one lock. To bring it all up on the real robot safely, I built a hardware-in-the-loop bring-up protocol.
{% endrow %}
