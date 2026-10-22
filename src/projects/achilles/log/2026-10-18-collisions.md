---
title: Collision detection
---
{# Placeholder: Eric to confirm, and add a clip of the contact solver once it's on GitHub (branch EricG/collision-resolution). The clip and the 1,800-pair test were made in the cloud from Achilles main. #}
The design doc planned cuRobo-style sphere colliders. What I built is more general: every body is a sphere-swept box, so zero extents make a sphere, one extent a capsule and zero radius a plain box. A broad phase tests swept-box world bounds and writes a bitmask of candidate pairs, and a MuJoCo/MJX-style narrow phase turns each candidate into up to four contacts with a normal, a signed distance and a point, computed across SIMD lanes like everything else. To check it, I ran 1,800 random sphere, capsule and box pairs through the narrow phase and compared each against an exact signed-distance calculation: **every distance Achilles reported agreed to within 5×10⁻⁵** (median 2×10⁻⁸), and the 5 pairs it skipped really were beyond the contact margin. MuJoCo, on the same pairs, matched for spheres and capsules, but its box colliders, which approximate some cases, were off on 86. The contact solver that pushes bodies apart is working on a branch that isn't on GitHub yet, so for now the arms below pass through each other.

{% video "images/collisions.mp4", "Two double pendulums swinging through each other at half speed, with each body's collision shape outlined in white and magenta markers and normal lines appearing wherever they touch", { poster: "images/collisions.jpg", caption: "Half speed. White: each body's collision shape. Magenta: the narrow phase's contacts and normals, every frame." } %}

<figure>
  <img src="images/collision-vs-exact.svg" alt="Scatter chart of reported against exact signed distance for 1,795 random shape pairs. Every Achilles point lies on the diagonal. MuJoCo's points also lie on it except for 86 box pairs, which scatter off the line" loading="lazy" decoding="async">
  <figcaption>Each pair's distance as reported by each engine, against the exact answer. Sphere, capsule and box, all six combinations, from 0.35 overlapping to 0.3 apart.</figcaption>
</figure>
