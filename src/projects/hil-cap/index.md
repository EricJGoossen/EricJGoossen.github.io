---
layout: project.njk
title: Benchmarking VLAs for ARCHITECT
short: HCRL
portfolio: true
org: "Human Centered Robotics Lab"
timeline: Apr 2026 – present
tools: [Python, DROID, Franka Panda, openpi, GR00T, MolmoAct2, WebSocket, ZMQ]
order: 2
summary: The real-robot benchmark behind a paper on language-guided robot code, from the evaluation harness to what four VLAs can and can't do.
cover: images/compare-banana-under-cloth.mp4
coverPoster: images/compare-banana-under-cloth.jpg
hero: images/hero-architect.mp4
heroAlt: A Franka Panda arm in a dark lab putting an apple and bread into a bowl, closing a drawer, and folding a cloth into a triangle
heroFade: strong
heroSize: large
heroPoster: images/hero-architect.jpg
links:
  - label: GitHub
    url: https://github.com/EricJGoossen/VLA_benchmarking
  - label: Paper
    url: https://arxiv.org/abs/2607.23784
  - label: Website
    url: https://robo-architect.github.io/
---
{# Confirmed by Eric (Oct 25). Drafted from EricJGoossen/VLA_benchmarking (Jun 28 – Oct 14, 2026), the paper (arXiv 2607.23784v1, Jul 26, 2026) and his resume. The rollout clips, the comparison grids and the hero are built from the videos on the paper's website (robo-architect/robo-architect.github.io); the human-evaluation photos and charts are the paper's figures. Eric (Oct 25): he ran all of the VLA runs, and the overview's "designed the experiments" stands. #}
In the Human Centered Robotics Lab, I built and ran the real-robot benchmark for ARCHITECT, the lab's system for writing robot programs with a coding agent and fixing them with plain-language corrections. Its paper compares that approach against vision-language-action (VLA) models, so I wrote the open-source harness that runs any VLA on a Franka Panda through DROID, designed the experiments, and benchmarked π0, π0.5, MolmoAct2 and GR00T N1.7 on eight real manipulation tasks, from pick and place to closing a drawer, folding a cloth and uncovering a banana hidden under one, plus an ablation of fifteen ways to word the same instruction. Along the way I learned where these models are strong, where they fall apart, and how to measure the difference fairly.
