---
layout: project.njk
title: Achilles
org: ""
timeline: 2026 – present
tools: [C++20, xsimd (SIMD), CMake, GoogleTest, OpenGL/GLFW, Valgrind, MuJoCo (benchmarks)]
order: 5
cover: images/eight-pendulums.mp4
coverPoster: images/eight-pendulums.jpg
hero: images/double-pendulum.mp4
heroAlt: A red and blue double pendulum swinging chaotically under gravity in the Achilles viewer
heroPoster: images/double-pendulum.jpg
summary: A C++20 rigid-body simulator that steps 8 robots per SIMD instruction, about 3× MuJoCo's single-threaded throughput.
highlights:
  - label: SIMD batching
    entry: simd
    skills: [C++, SIMD, Performance engineering]
  - label: Viewer
    entry: renderer
    skills: [OpenGL]
  - label: 3× MuJoCo
    entry: mujoco-comparison
    skills: [Performance engineering, MuJoCo, C++]
  - label: Dynamics (ABA)
    entry: dynamics
    skills: [Rigid-body dynamics, Numerical methods, C++]
  - label: Collisions
    entry: collisions
    skills: [Collision detection, SIMD, C++]
links:
  - label: GitHub
    url: https://github.com/EricJGoossen/Achilles
---
{# Placeholder: org (personal project or ARUW?) #}
Achilles is a C++20 articulated rigid-body simulator I'm building for my club, Advanced Robotics at UW (ARUW), whose codebase had too much technical debt to take an off-the-shelf simulator. It loads a jointed scene from a YAML file, runs forward dynamics with the Articulated Body Algorithm, integrates at a fixed timestep and can draw the scene live in an OpenGL viewer. Because I want to train RL policies for ARUW without much GPU compute, V3 runs independent robots side by side in SIMD lanes: on one laptop core it steps a seven-link arm 3.3× faster than single-threaded MuJoCo.
