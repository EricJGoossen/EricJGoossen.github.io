---
layout: project.njk
title: Achilles
short: Achilles
portfolio: true
org: Orchid Robotics
timeline: 2026 – present
tools: [C++20, xsimd (SIMD), CMake, GoogleTest, OpenGL/GLFW, Valgrind, MuJoCo (benchmarks)]
order: 5
cover: images/eight-pendulums.mp4
coverPoster: images/eight-pendulums.jpg
hero: images/hero-pendulum.mp4
heroAlt: A red and blue double pendulum swinging chaotically under gravity in the Achilles viewer
heroPoster: images/hero-pendulum.jpg
summary: A C++20 rigid-body simulator that steps 8 robots per SIMD instruction, about 3× MuJoCo's single-threaded throughput.
links:
  - label: GitHub
    url: https://github.com/EricJGoossen/Achilles
---
{# Org (Eric, Oct 25): Orchid Robotics, the robotics club he is starting; a personal project motivated by ARUW, meant for more than the club. #}
I designed and wrote Achilles, a C++20 articulated rigid-body simulator, from scratch and alone: the math, dynamics, collisions and memory layout are all my own code, with libraries only for SIMD (xsimd), graphics (OpenGL/GLFW) and testing (GoogleTest). It began as an in-house simulator for my club's codebase (see the first entry), but as its scope grew, the goal became speed: beating off-the-shelf simulators on the problems my club, Advanced Robotics at the University of Washington, faces. Massively multi-agent simulation that tolerates small numerical loss can speed up reinforcement learning, and with it how fast we iterate on automating our competition robots. Eventually I plan to port it to CUDA and build an RL harness, so we can iterate on agents that compete in our game instead of our drivers. Three principles guide the architecture: branchless code (for the CUDA port), structure-of-arrays storage for cache locality, and enough generality that any algorithm can be slotted into the backend without significant engine changes.
