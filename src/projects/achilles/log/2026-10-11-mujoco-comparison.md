---
title: Beating MuJoCo on throughput
date: 2026-10-11 08:52:09
summary: "Benchmarked against MuJoCo on the same scenes: batched across SIMD lanes, Achilles steps a seven-link arm 3.3× faster."
featured: true
short: "3× MuJoCo"
skillTags: [Simulation (MuJoCo), Performance & SIMD, C++]
info:
  language: [C++20, Python]
  tools: [MuJoCo]
  hardware: Laptop
  role: Solo
  status: Measured
links:
  - label: "Benchmark code"
    url: "https://github.com/EricJGoossen/achilles/tree/355a392/bench"
---
{# Confirmed by Eric (Oct 25). Benchmark numbers are from his 2026-10-11 laptop run, except the V3 one-link points on the chart (2.8× and 2.7×), which were measured on a different machine (assets-src/achilles/generated/data/speed_vs_mujoco_cloud.json); rerun them on the laptop. The side-by-side clip was recorded in the cloud. #}
{% row "images/speed-vs-mujoco.svg", "Line chart of speed relative to MuJoCo by number of links. V2 with one robot falls from 1.1× at one link to 0.48× at eight. V3 with one robot is 2.8×, 2.1×, 1.6× and 0.97× at one, two, three and seven links. V3 with 64 robots batched is 2.7×, 2.6×, 3.0× and 3.3×.", { caption: "Each version timed against MuJoCo on the same machine, in its own benchmark: V2 against MuJoCo 3.3 (no gravity, 1 ms step), V3 against MuJoCo 3.15 (2 ms step).", more: [{ src: "images/achilles-vs-mujoco.mp4", alt: "The same double pendulum side by side, Achilles' viewer on the left and MuJoCo's renderer on the right, moving identically", poster: "images/achilles-vs-mujoco.jpg", caption: "The same double pendulum in Achilles and MuJoCo, matching out to 8 seconds. Same scene and start, both RK4 at a 2 ms step." }] } %}
To see where V3 stood, I benchmarked it against MuJoCo 3.15 on the same arm scenes, converted from the same `.arow` files, at the same 2 ms step, single-threaded on my laptop (Intel Core Ultra 9 285H). Batched across SIMD lanes, Achilles steps a seven-link arm 3.3× faster than MuJoCo's best single-threaded mode, reaching 5.45 million robot-steps per second at 64 robots. In double precision, MuJoCo's own, Achilles is still 1.5–1.6× faster at most batch sizes, and its results match MuJoCo's to about one part in 10¹¹. The one loss is a single seven-link arm, where most SIMD lanes sit empty (0.97×).
{% endrow %}
