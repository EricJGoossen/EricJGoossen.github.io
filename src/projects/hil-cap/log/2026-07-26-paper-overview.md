---
title: "The paper: A Few Words Go a Long Way"
date: 2026-07-26 12:00:00
---
{# Placeholder: Eric to confirm. Everything here is from the paper (arXiv 2607.23784v1); ARCHITECT itself is the lab's system, by Daphne Chen and the co-authors, not Eric's work. Numbers: Table 1; human evaluation with N = 6: queries per trial 4.67 to 0.83 (p = 0.036), Task 2 success 0/6 without skills, 4/6 with. Media: the website's videos and the paper's figures. #}
{% row "images/architect-overview.png", "Diagram of ARCHITECT: an instruction, the human's corrections, a skill library and the robot's primitives go into an LLM, which writes code that runs on the robot; the robot's execution trace comes back, and a human watches and adds a correction", { caption: "ARCHITECT, from the paper's website." } %}
The paper asks whether robot programs written by a coding agent, and fixed with a few words from a person, can beat end-to-end VLAs. ARCHITECT has an LLM write a program from perception and control tools, runs it, and reads back an execution trace. When it fails, a person says what went wrong ("grasp the cup from the top"), and the fix is saved to a skill library the agent reuses on later tasks.
{% endrow %}

{% row "images/compare-banana-under-cloth.mp4", "Four side-by-side rollouts of moving a cloth off a banana and putting the banana on a plate: ARCHITECT, Code as Policies, π0 and π0.5", { poster: "images/compare-banana-under-cloth.jpg", caption: "Banana under a cloth: ARCHITECT, Code as Policies, π0 and π0.5.", more: [{ src: "images/compare-close-drawer.mp4", poster: "images/compare-close-drawer.jpg", alt: "Four side-by-side rollouts of closing a cabinet drawer", caption: "Closing a drawer." }, { src: "images/compare-fold-cloth.mp4", poster: "images/compare-fold-cloth.jpg", alt: "Four side-by-side rollouts of folding a cloth into a triangle", caption: "Folding a cloth." }, { src: "images/compare-apple-bread-bowl.mp4", poster: "images/compare-apple-bread-bowl.jpg", alt: "Four side-by-side rollouts of putting an apple and bread into a bowl", caption: "An apple, then bread, into a bowl." }] } %}
On eight real tasks on a Franka Panda, **ARCHITECT succeeded 70 to 100% of the time on every one**, while the VLAs did well only on simple pick and place and Code as Policies, which writes the program once, topped out at 60%. The VLAs scored 0 to 10% on the drawer, the cloth and the hidden banana.
{% endrow %}

{% row "images/human-eval-queries.png", "Bar chart of human queries per trial with and without a skill library: about 4.7 without, under 1 with, one line per participant", { caption: "Corrections needed, without and with skills from an earlier task (N = 6).", more: [{ src: "images/human-eval-success.png", alt: "Bar chart of success rate on the second task: 0 without skills, about 0.67 with", caption: "Success on the second task." }, { src: "images/human-eval-012.jpg", alt: "The Franka arm lifting a green cup above a small white table", caption: "Task 1: place the cup upright." }, { src: "images/human-eval-018.jpg", alt: "The Franka arm holding a pasta box above a wooden shelf", caption: "Task 2: place the box on the shelf." }] } %}
A six-person study tested the skill library. With skills learned on the cup task, people needed **0.83 corrections per trial on the box task instead of 4.67**, and with no corrections at all, success on the box task went from 0 of 6 to 4 of 6.
{% endrow %}

{% row "images/architect-video.mp4", "The paper's supplementary video", { play: true, poster: "images/architect-video.jpg", caption: "The supplementary video (with sound)." } %}
The supplementary video walks through the system and the comparisons.
{% endrow %}
