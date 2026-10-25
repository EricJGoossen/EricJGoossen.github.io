---
title: Where it started
date: 2026-03-04
info:
  language: C++
  hardware: Laptop
  role: Solo
  status: Replaced
links:
  - label: "First commit"
    url: "https://github.com/EricJGoossen/achilles/commit/0dc8cfb"
---
{% row "images/achilles-initial-architecture.svg", "The V2 design as a diagram: the objects (plant, links, joints, actuators, sensors) and the six-step loop each timestep runs" %}
The original inspiration for Achilles was that my club's codebase at Advanced Robotics at UW (ARUW) had gained so much technical debt that integrating an off-the-shelf simulator would have been extremely difficult. That's why I began developing Achilles: an in-house rigid body simulator that could grow with the codebase, rather than being forgotten as previous simulators had been. I was immediately overcome with inspiration and had to start programming. However, I didn't stop to design my system beforehand, so I learned about the systems I was modeling as I wrote, which resulted in a tangled mess. I decided to restart development entirely with Achilles V2, but before I did, I spent time architecting the system so I could follow proper software engineering practices.
{% endrow %}
