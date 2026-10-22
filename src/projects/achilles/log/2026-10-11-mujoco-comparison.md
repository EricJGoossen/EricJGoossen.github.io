---
title: Beating MuJoCo on throughput
date: 2026-10-11 08:52:09
---
{# Placeholder: Eric to confirm. Benchmark numbers are from his 2026-10-11 run; the side-by-side clip was recorded in the cloud. #}
{% row "images/speed-vs-mujoco.svg", "Line chart of speed relative to MuJoCo by number of links. V2 with one robot falls from 1.1× at one link to 0.48× at eight. V3 with one robot is 2.1×, 1.6× and 0.97× at two, three and seven links. V3 with 64 robots batched is 2.6×, 3.0× and 3.3×.", { caption: "Each version timed against MuJoCo on the same laptop, in its own benchmark: V2 against MuJoCo 3.3 (no gravity, 1 ms step), V3 against MuJoCo 3.15 (2 ms step)." } %}
To see where V3 stood, I benchmarked it against MuJoCo 3.15 on the same arm scenes, converted from the same `.arow` files, at the same 2 ms step, single-threaded on my laptop (Intel Core Ultra 9 285H). Batched across SIMD lanes, Achilles steps a seven-link arm **3.3× faster than MuJoCo's best single-threaded mode: 5.45 million robot-steps per second at 64 robots**, and about 3× from 16 robots up. In double precision, MuJoCo's own, it's still 1.5–1.6× faster at most batch sizes. V2 never got there: it was slower than MuJoCo from two links on while skipping much of the physics.
{% endrow %}

{% row "images/achilles-vs-mujoco.mp4", "The same double pendulum side by side, Achilles' viewer on the left and MuJoCo's renderer on the right, moving identically", { poster: "images/achilles-vs-mujoco.jpg", caption: "The same double pendulum in Achilles and MuJoCo, matching out to 8 seconds. Same scene and start, both RK4 at a 2 ms step." } %}
Speed only counts if the answer is the same. Here is one double pendulum, loaded from the same `.arow` file into both engines and released from the same start: Achilles in its own viewer on the left, MuJoCo's renderer on the right, moving together.
{% endrow %}
