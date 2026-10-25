---
title: "SKIDADDLE: a path follower that plans with physics"
date: 2025-10-01
summary: "A Java path-following library for FTC that plans with a physics model of the robot, with math I derived by hand."
featured: true
portfolio: true
short: "SKIDADDLE"
skillTags: [Motion planning, Java, Open source]
info:
  language: Java
  hardware: FTC robot
  role: Solo
  status: Open source
links:
  - label: "Code"
    url: "https://github.com/EricJGoossen/SKIDADDLE/tree/7d3240c"
---
{# Built at the end of summer 2025 (Eric, Oct 25); the math is all Eric's own. From the SKIDADDLE repo (README and code at 7d3240c, Sep 27 – Oct 1, 2025). The video and chart are the repo's own simulator, run on one Bézier path with SIMULATING on; the chart has every series but speed, acceleration and the speed limit clicked off in its legend. #}
{% row "images/skidaddle-sim.mp4", "Top-down FTC field: a round robot follows a red S-shaped path from the bottom-left corner, around the centre structure, to the top-right, between four white control points", { poster: "images/skidaddle-sim.jpg", caption: "SKIDADDLE's own simulator following a cubic Bézier path, in real time.", more: [{ src: "images/skidaddle-chart.png", alt: "Line chart over the run: blue speed rises, follows the green speed limit through the turns and falls to zero at the end; the red acceleration sits at its cap and drops whenever the speed reaches the limit", caption: "The simulator's graph of the same run: speed (blue) tracking the look-ahead's speed limit (green), acceleration (red) mostly at its cap." }] } %}
SKIDADDLE is a path-following library for FTC robots, written in Java, that I built to fix inefficiencies in Road Runner, the usual FTC path library, and get better paths. It plans with a physics model of the robot, and I derived all of its math by hand, myself, without AI or earlier work to build on. A path, a cubic Bézier for autonomous or a Hermite spline built on the fly in tele-op, is flattened into straight segments by adaptive De Casteljau subdivision, and a curve whose turns would need more than the robot's acceleration is relaxed until they don't. Every loop it splits the robot's velocity into a convergent part, toward the goal, and a transverse part, everything else. It first spends its acceleration budget cancelling the transverse part, then speeds up the convergent part, so from any starting position or velocity the robot converges on the path. A look-ahead over the stopping distance sets the fastest speed for each corner, and the robot switches segments when its braking distance says it must. Heading is a separate controller, and the result goes through PIDF and feedforward to the four wheels. A simulator draws the field and graphs every step.
{% endrow %}
