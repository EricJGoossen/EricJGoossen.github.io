---
layout: project.njk
title: Achilles
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
highlights:
  - label: SIMD batching
    entry: simd
    skills: [Performance & SIMD, C++]
  - label: 3× MuJoCo
    entry: mujoco-comparison
    skills: [Simulation (MuJoCo), Performance & SIMD, C++]
  - label: O(n) dynamics
    entry: dynamics
    skills: [Kinematics & Dynamics, C++]
  - label: Contact solver
    entry: collision-response
    skills: [Kinematics & Dynamics, C++]
  - label: Integrators
    entry: integrators
    skills: [Kinematics & Dynamics, C++]
  - label: OpenGL renderer
    entry: renderer
    skills: [C++]
links:
  - label: GitHub
    url: https://github.com/EricJGoossen/Achilles
---
{# Org (Eric, Oct 25): Orchid Robotics, the robotics club he is starting; a personal project motivated by ARUW, meant for more than the club. #}
Achilles is a C++ 20 articulated rigid-body simulator I’m building. The motivation for the system is to beat the performance of off the shelf simulators when tackling the specific problems my club, Advanced Robotics at the University of Washington, is facing. By improving the performance in massively multi-agent simulations which are robust to small numerical loss, I can speed up reinforcement learning and improve our iterations time when trying to automate our robots when competing on the field. Eventually I plan to port the simulator to CUDA and build a reinforcement learning harness to allow us to iterate on agents that can compete in our game instead of our drivers. The architectural philosophy that governs my development of Achilles emphasizes branchless code (to facilitate the CUDA port later), SoA architecture for cache locality, and extreme generality on which algorithms are mutating data to allow any system to be slotted into the backend without significant engine changes.
