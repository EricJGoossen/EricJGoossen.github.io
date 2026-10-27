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
**I designed and wrote Achilles from scratch, alone, from the first idea to every line: the math, dynamics, collisions and memory layout are all my own code, and the only libraries are for SIMD (xsimd), drawing to the screen (OpenGL/GLFW) and testing (GoogleTest).** Achilles is a C++ 20 articulated rigid-body simulator I’m building. Its motivation changed as its scope grew (it started as an in-house simulator for my club's code; see the first entry). Today, the motivation for the system is to beat the performance of off the shelf simulators when tackling the specific problems my club, Advanced Robotics at the University of Washington, is facing. By improving the performance in massively multi-agent simulations which are robust to small numerical loss, I can speed up reinforcement learning and improve our iterations time when trying to automate our robots when competing on the field. Eventually I plan to port the simulator to CUDA and build a reinforcement learning harness to allow us to iterate on agents that can compete in our game instead of our drivers. The architectural philosophy that governs my development of Achilles emphasizes branchless code (to facilitate the CUDA port later), SoA architecture for cache locality, and extreme generality on which algorithms are mutating data to allow any system to be slotted into the backend without significant engine changes.
