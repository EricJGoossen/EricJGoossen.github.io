---
title: Reworking SKIDADDLE's control
date: 2026-01-03
skillTags: [Motion planning, Java]
---
{# From the SKIDADDLE commits Dec 22, 2025 – Jan 3, 2026 (acceleration allocator, refactored linear control, angular fixes, precompute). The rework's linear controller never reports itself finished yet, so it isn't run in the simulator here; the diagram is drawn from the code at 4b3fdb9. #}
{% row "images/skidaddle-pipeline.svg", "Diagram: once per path, a path generator feeds precomputed speed limits; every loop, controllers send requests to a scheduler, which feeds an allocator that drives the wheels", { caption: "The follower after the rework." } %}
Over winter break I took SKIDADDLE apart into pieces that each do one job. Controllers now only ask for accelerations: one along the path, one back onto it, one for heading, each with a weight and a priority. A scheduler runs whichever are active, and a default controller brings the robot to a stop when none are. A new allocator turns the requests into motor space and hands out each motor's remaining headroom, highest priority first and shared by weight within a priority, so correcting off the path can come before speeding along it without any motor going past its limits. The look-ahead, before the most expensive part of the loop, became a precompute: when a path is made, one backward pass finds the fastest speed the robot can enter each turn at, so the loop only reads it. [[Code](https://github.com/EricJGoossen/SKIDADDLE/tree/4b3fdb9)]
{% endrow %}
