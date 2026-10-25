---
layout: project.njk
draft: true   # hidden from the site until this line is removed
title: Fleet RL
org: "WEIRD Lab"
timeline: Sep 2026 – present
tools: [Python, OpenCV, AprilTags, SO-101]
order: 3
summary: Twelve low-cost robot arms learning one task together, with resets that need no human.
# Placeholder: Eric will pick the hero (a fleet panorama) and the card (the twelve scene cameras).
# The two images below, from the fleet handbook, hold their places until then.
cover: images/scene-cams-all.jpg
hero: images/fleet-panorama.jpg
heroAlt: Panorama of the fleet lab, with orange and blue low-cost robot arms at workstations along three walls, each under an aluminium frame holding its cameras, and a desk with a monitor in the foreground
highlights:
  - label: Automatic reset
    entry: automatic-reset
    skills: [Reinforcement learning, Motion planning, Python]
links:
  - label: GitHub
    url: "https://github.com/knightnemo/fleet_so101_infra"
---
{# From Eric (Oct 24): the overview is about cohesive learning across 12 arms, with an expected improvement of more than 12x. #}
We're building a system in which twelve robot arms with diverse embodiments learn together: every arm's experience trains one shared policy. With the arms learning from each other, we expect more than a twelvefold improvement over a single arm. Online reinforcement learning only works if the arms can keep practising without a person resetting every trial, so my part so far is the automatic reset.
