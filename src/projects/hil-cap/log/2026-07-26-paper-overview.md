---
title: "The paper: A Few Words Go a Long Way"
date: 2026-07-26 12:00:00
summary: "The paper my benchmark fed: ARCHITECT, which fixes LLM-written robot code with a few words from a person, succeeded 70 to 100% of the time on all eight tasks."
featured: true
short: "1.75× over VLAs"
skillTags: [Robot learning]
info:
  hardware: Franka Panda
  role: Co-author
  status: On arXiv
links:
  - label: "Paper"
    url: "https://arxiv.org/abs/2607.23784"
  - label: "Website"
    url: "https://robo-architect.github.io/"
---
{# Confirmed by Eric (Oct 25). Everything here is from the paper (arXiv 2607.23784v1); ARCHITECT itself is the lab's system, by Daphne Chen and the co-authors, not Eric's work. Numbers: Table 1; human evaluation with N = 6: queries per trial 4.67 to 0.83 (p = 0.036), Task 2 success 0/6 without skills, 4/6 with. Media (Oct 24, per Eric: one chart and one 2×2 video): the paper's human-evaluation chart and the website's banana-under-cloth comparison. #}
{% row "images/compare-banana-under-cloth.mp4", "Four rollouts in a two-by-two grid of moving a cloth off a banana and putting the banana on a plate: ARCHITECT, Code as Policies, π0 and π0.5", { poster: "images/compare-banana-under-cloth.jpg", caption: "Banana under a cloth: ARCHITECT, Code as Policies, π0 and π0.5.", more: [{ src: "images/human-eval-queries.png", alt: "Bar chart of human queries per trial with and without a skill library: about 4.7 without, under 1 with, one line per participant", caption: "Corrections needed, without and with skills from an earlier task (N = 6)." }] } %}
ARCHITECT is the lab's system, not mine: I'm a co-author for the VLA benchmark behind its comparison. The paper asks whether robot programs written by a coding agent, and fixed with a few words from a person, can beat end-to-end VLAs. ARCHITECT has an LLM write a program from perception and control tools, runs it, and reads back an execution trace. When it fails, a person says what went wrong ("grasp the cup from the top"), and the fix is saved to a skill library the agent reuses on later tasks.

On eight real tasks on a Franka Panda, **ARCHITECT succeeded 70 to 100% of the time on every one**, while Code as Policies, which writes the program once, topped out at 60%. The VLAs held their own only on simple pick and place, where π0.5 succeeded 90% of the time on the banana and every time on the block, against ARCHITECT's 80% and 70%; they scored 0 to 10% on the drawer, the cloth and the hidden banana. A six-person study tested the skill library: with skills learned on the cup task, people needed **0.83 corrections per trial on the box task instead of 4.67**, and with no corrections at all, success on the box task went from 0 of 6 to 4 of 6.
{% endrow %}
