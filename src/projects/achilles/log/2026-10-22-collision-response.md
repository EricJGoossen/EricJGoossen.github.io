---
title: Collision response
date: 2026-10-22 01:22:05
summary: "A soft-contact solver with Coulomb friction that turns contacts into forces, run on a domino scene next to MuJoCo."
featured: true
portfolio: true
short: "Contact solver"
skillTags: [Kinematics & Dynamics, C++]
loc: 2041
info:
  language: C++20
  tools: [MuJoCo]
  hardware: Laptop
  role: Solo
  status: On a branch
links:
  - label: "Code"
    url: "https://github.com/EricJGoossen/achilles/tree/223af7c"
---
{# Confirmed by Eric (Oct 25). Dated by the "added contact solving" commit on EricG/collision-resolution (not merged yet). The domino scene, both runs and the clip were made in the cloud from that branch, unmodified, through a small standalone driver. #}
{% row "images/domino-amplifier.mp4", "Ten dominoes, each bigger than the last, topple in a chain from a tiny one to one taller than a person; the largest falls flat", { poster: "images/domino-amplifier.jpg", caption: "Real time, rendered by the Achilles viewer: semi-implicit Euler at a 2 ms step.", more: [{ src: "images/domino-timing.svg", alt: "Chart of the time each of the ten dominoes tipped past 45 degrees, from 1.2 seconds for the first to 4.8 seconds for the last. Achilles' points sit inside MuJoCo's rings for every domino.", caption: "The same scene in MuJoCo 3.15: each domino tips within 56 ms of MuJoCo's time, and all ten come to rest within 0.3° of MuJoCo's angles." }] } %}
Detecting contacts is only half the battle; working out what happens next is the rest. Once accelerations and contacts are known, the solver adjusts the accelerations so bodies respect their contacts. It uses a "soft contact" model in which each contact acts like a stiff spring-damper, pushing harder the deeper and faster two bodies collide. Friction follows Coulomb's law, whose cone of allowed forces is approximated by a four-sided pyramid of push-only edges, letting bodies grip or slide. Each frame, the solver minimizes

½ (a − a₀)ᵀ M (a − a₀) + Σᵢ ½ Dᵢ (Jᵢ a − a_ref,ᵢ)²,

staying close to the unconstrained acceleration a₀ while penalizing contact violations. It warm-starts from the previous frame's solution when that costs less, then runs a fixed 20 conjugate-gradient iterations to suit SIMD and GPUs, never building the mass matrix. The corrected acceleration then goes to the integrator.
{% endrow %}
