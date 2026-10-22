---
title: Integrators that hold energy
date: 2026-10-06 15:28:48
---
{# Placeholder: Eric to confirm. Dated by the WIP commit "integrator work, long-horizon validation" (2026-10-06); merged with the dynamics PR on 2026-10-17. The energy runs and chart were made in the cloud from Achilles main. #}
{% row "images/dp-energy.svg", "Chart of the change in total energy over 10 seconds for four integrators: semi-implicit Euler wanders between about −0.56 and +0.49 joules, velocity Verlet between about −0.28 and +0.24, and implicit midpoint and RK4 stay flat on the zero line", { caption: "Energy should stay constant. Double pendulum released from horizontal, 2 ms step." } %}
With the accelerations right, longer runs showed the next problem: semi-implicit Euler drifts. A double pendulum has no friction, so its total energy should stay constant, but over 10 seconds at a 2 ms step Euler's wanders by up to 0.56 J. The integrator decides how long a simulation stays physical, so I added three more: velocity Verlet, implicit midpoint and RK4. Verlet halves the drift to 0.28 J, while implicit midpoint stays within 0.0006 J and RK4 within 0.0001 J, at the price of four dynamics evaluations per step.
{% endrow %}
