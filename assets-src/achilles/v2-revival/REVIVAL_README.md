# Achilles V2 revival

The last commit of the April 2026 Achilles (V2, `39f1713` "Added sensor code", 2026-04-14), brought back to life so it can be compared with MuJoCo now and with the current Achilles later. Done 2026-10-21. Nothing in `~/projects/Achilles` was touched.

## What's here

| Path | What it is |
|---|---|
| `v2-src/` | V2 exactly as committed (`git checkout 39f1713`) |
| `v2-patched/` | Copy with three small fixes so it runs reliably (see below). `results/revival.patch` is the full diff. |
| `driver/` | New code: builds arms out of V2's own classes and steps them with V2's unmodified `Plant::update()`. Modes: `run`, `bench`, `sensors`. |
| `mujoco/compare.py` | MuJoCo reference runs, accuracy metrics, benchmark, plots, video |
| `docker/` | The two images used (`achilles-v2-cpp`, `achilles-v2-py`), logged in `personal_website/INSTALLED.md` |
| `results/` | All data, plots and the video |

## Results

**Video:** `results/v2_vs_mujoco.mp4` (6 s, top-down). Left: V2. Right: MuJoCo. Top row: one-link arm. Bottom row: two-link arm. Same torques, no gravity, 1 ms steps. V2 never had a renderer, so its recorded motion is replayed through MuJoCo's renderer. Still frame: `results/v2_vs_mujoco_t3s.png`.

**Accuracy** (`results/accuracy.json`, `results/accuracy_*.png`). Thin rods are 1 kg and 0.5 m; the disk is 1 kg with r = 0.2 m. Both simulators use semi-implicit Euler at 1 ms.

| Scenario | Result |
|---|---|
| Disk, mass on the joint axis, constant torque | V2 matches MuJoCo and the exact answer to within 5 µrad (the CSV's print precision) |
| One-link arm, sinusoidal torque | V2 swings **exactly 4× too fast**: peak speed 1.528 vs 0.382 rad/s. It uses the free-body inverse inertia (`Sᵀ I⁻¹ S τ`) instead of the pinned-joint inertia (`τ / Sᵀ I S`), which drops the parallel-axis term: 0.0833 / 0.0208 = 4. MuJoCo matches the exact answer to 1e-15. |
| Two-link arm | Wrong shape, not just scale. After 6 s, V2 has joint 2 at +2.87 rad while MuJoCo has it at −1.43 rad. V2's inward and outward passes never transform inertias or accelerations between frames, so where joint 2 sits on link 1 never reaches the dynamics. There are also no velocity-dependent (Coriolis/centrifugal) terms and no gravity. |

**Performance** (`results/performance.png`, median of 3 runs, Intel Core Ultra 9 285H, V2 at `-O3`, MuJoCo 3.3.0 via `rollout` with contacts off):

| Links | V2 (µs/step) | MuJoCo (µs/step) | V2 / MuJoCo |
|---|---|---|---|
| 1 | 0.35 | 0.39 | 0.92× |
| 2 | 0.62 | 0.50 | 1.25× |
| 4 | 1.31 | 0.93 | 1.41× |
| 8 | 2.65 | 1.26 | 2.10× |
| 16 | 5.51 | 2.44 | 2.26× |
| 32 | 10.91 | 5.42 | 2.01× |
| 64 | 22.90 | 17.10 | 1.34× |

MuJoCo is doing much more per step: full Coriolis/centrifugal terms, the mass matrix and its factorization, actuators and sensors. V2 skips most of that physics and is still up to about 2.3× slower from 2 links on. Per-step hash-map lookups, virtual calls, recursion and 6×6 Eigen temporaries are the likely costs.

**Sensor models** (`results/sensor_distortion.png`, `results/v2_sensors.csv`). Six V2 `Encoder`s sit on one swinging joint at once: ideal, white noise, Gauss–Markov drift, a 5 Hz low-pass filter, a +3% scale-factor error, and all of them combined. Each run is one random sample, because V2 seeds its generators from the system. The encoder distorts each step's angle *increment* and then accumulates ticks, so noise and drift build up over time (see the green drift curve).

## Bugs found while reviving it

1. **CRTP call before the derived object exists** (`base_joint.hpp:35`). `BaseJoint`'s constructor calls `Derived::makeJointPose()`, which reads `RevoluteJoint::b_` before `RevoluteJoint` has been constructed. UBSan flags it as a downcast to an object that isn't a `RevoluteJoint` yet. Depending on leftover memory, the starting angle was 0 or NaN.
2. **"Zero" vectors that weren't zero** (`vector.hpp`). `Vector() = default` relies on value-initialization to zero the Eigen storage. GCC's lifetime dead-store elimination (on at `-O2` and up) removes that zeroing, so `Surge::zero()` and `Twist::identity()` returned garbage. Valgrind traced the uninitialized value to `Surge::zero()` in `JointTree::propagateAccelerations`. `-fno-lifetime-dse` alone fixed it, which confirmed the cause. This produced NaNs or a steady phantom acceleration that came and went as unrelated code changed.
3. **The sensor code never compiled** (`gaussian.hpp`). `Gaussian::sample()` is `const` but advances a non-`mutable` `std::mt19937`. Nothing in V2 included the sensor headers, so no build ever hit it.
4. **Angles fold above π** (`pose.cpp`). `Pose::angle()` is `2·acos(w)`, and Eigen returns quaternions with w ≥ 0, so any angle θ > π reads as 2π − θ. `Encoder` builds on `Angle()`, so past π it would count backwards. Not patched: the sensor scenario keeps the swing below π, and the driver reads signed angles from the quaternion itself.
5. **V2's own CMakeLists can't build**: it expects a `src/main.cpp` and a test file that the frames rework deleted. The driver has its own CMakeLists that compiles V2's sources unmodified.

Fixes 1–3 are in `v2-patched/` (each marked `REVIVAL PATCH`). Fix 1 hard-codes the starting joint coordinate to zero, which is correct because every scenario starts at the zero pose.

## Rerun everything

From this folder:

```bash
docker build -t achilles-v2-cpp -f docker/cpp.Dockerfile docker
docker build -t achilles-v2-py -f docker/py.Dockerfile docker

# V2 (patched), -O3 like V2's own Release config
docker run --rm -u 1000:1000 -e HOME=/tmp -v "$PWD":/w achilles-v2-cpp sh -c '
  cmake -S driver -B build-o3 -DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_FLAGS_RELEASE=-O3 -g -DNDEBUG" -DV2_SRC=/w/v2-patched &&
  cmake --build build-o3 -j &&
  for s in disk arm arm2; do ./build-o3/v2_driver run $s results/v2_$s.csv; done &&
  ./build-o3/v2_driver sensors results/v2_sensors.csv'
# benchmark: ./build-o3/v2_driver bench <links> <steps>  (prints links,ns_per_step)

# MuJoCo runs, metrics, benchmark, plots, video
docker run --rm -u 1000:1000 -e HOME=/tmp -e MPLCONFIGDIR=/tmp -v "$PWD":/w achilles-v2-py python mujoco/compare.py all
```

To compare the current Achilles later, add a runner that writes the same CSV format (`t,q0,qd0,tau0,...`) for the `disk`, `arm` and `arm2` scenarios in `mujoco/compare.py`, then plot it as a third line.
