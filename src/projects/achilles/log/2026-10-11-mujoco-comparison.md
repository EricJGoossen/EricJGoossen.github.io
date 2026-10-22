---
title: Beating MuJoCo on throughput
---
{# Placeholder: Eric to confirm. Benchmark numbers are from his 2026-10-11 run; the side-by-side clip was recorded in the cloud. #}
To see where V3 stood, I benchmarked it against MuJoCo 3.15 on the same arm scenes, converted from the same `.arow` files, at the same 2 ms step, single-threaded on my laptop (Intel Core Ultra 9 285H). Batched across SIMD lanes, Achilles steps a seven-link arm **3.3× faster than MuJoCo's best single-threaded mode: 5.45 million robot-steps per second at 64 robots**, and about 3× from 16 robots up. In double precision, MuJoCo's own, it's still 1.5–1.6× faster at most batch sizes. V2 never got there: it was slower than MuJoCo from two links on while skipping much of the physics. And V3 gets the same answer, not just a fast one: from the same start, the two engines trace the same path until the chaotic pendulum amplifies their rounding differences.

<figure>
  <img src="images/speed-vs-mujoco.svg" alt="Line chart of speed relative to MuJoCo by number of links. V2 with one robot falls from 1.1× at one link to 0.48× at eight. V3 with one robot is 2.1×, 1.6× and 0.97× at two, three and seven links. V3 with 64 robots batched is 2.6×, 3.0× and 3.3×." loading="lazy" decoding="async">
  <figcaption>Each version timed against MuJoCo on the same laptop, in its own benchmark: V2 against MuJoCo 3.3 (no gravity, 1 ms step), V3 against MuJoCo 3.15 (2 ms step). Seven links is the longest arm V3 was benchmarked on.</figcaption>
</figure>

{% video "images/achilles-vs-mujoco.mp4", "The same double pendulum side by side, Achilles' viewer on the left and MuJoCo's renderer on the right, moving identically", { poster: "images/achilles-vs-mujoco.jpg", caption: "Same scene and start, both RK4 at 2 ms. They stay within 1% of the arm's reach of each other for 8 seconds; after that, the chaotic swing separates any two correct simulators." } %}
