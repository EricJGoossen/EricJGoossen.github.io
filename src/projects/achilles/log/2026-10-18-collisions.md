---
title: Collision detection
date: 2026-10-18 14:43:13
skillTags: [C++]
links:
  - label: "Pull request"
    url: "https://github.com/EricJGoossen/achilles/pull/20"
---
{# Placeholder: Eric to confirm. The 1,800-pair test and the clip were made in the cloud from Achilles main. #}
{% row "images/collision-detection.mp4", "Two double pendulums swinging through each other, close up at quarter speed, with each body's collision shape outlined in white and magenta markers and normal lines appearing wherever they touch", { poster: "images/collision-detection.jpg", caption: "Detection only, at quarter speed: white outlines are the collision shapes, magenta the contacts and normals the narrow phase finds each frame. Nothing pushes back yet, so the arms pass through.", more: [{ src: "images/collision-vs-exact.svg", alt: "Scatter chart of reported against exact signed distance for 1,795 random shape pairs. Every Achilles point lies on the diagonal. MuJoCo's points also lie on it except for 86 box pairs, which scatter off the line", caption: "Each pair's distance as reported by each engine, against the exact answer. Sphere, capsule and box, all six combinations, from 0.35 overlapping to 0.3 apart." }] } %}
Before contacts can be resolved, they have to be found, and that happens in two phases. Every body carries a single "sphere-swept box," a box whose surface is pushed outward by a radius, so one shape type covers spheres, capsules, boxes and rounded boxes. The broad phase cheaply narrows the search. Each frame, it wraps every body in a world-aligned bounding box and tests every pair for overlap. It skips pairs whose collision groups exclude each other and bodies directly joined by a joint. The narrow phase then examines only the remaining candidates. For each pair, it computes a contact normal and up to four contact points, each with a signed distance that turns negative once the shapes overlap. Contacts within a small margin are kept even before the shapes touch, so the solver can react early. Both phases treat every pair the same way and mask out irrelevant results instead of branching, which keeps them SIMD- and GPU-friendly.
{% endrow %}
