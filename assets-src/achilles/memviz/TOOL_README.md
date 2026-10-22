# memviz: see how Achilles uses memory

Records every load and store the compiled engine makes during a few steps, labels each one with the memory it touched (which arena field block, the stack, or other heap), replays the stream through a model of the CPU's caches and TLB, and writes one HTML page that plays it back as an animation.

What the page shows:

- **Three headline numbers:** the share of accesses to simulation data that load or store a whole SIMD vector at once, the share served from L1, and the share that goes to the stack.
- **The animation.** A memory map drawn the way the arena is actually laid out. Each field block is a grid: rows are its components (the planar layout's separate arrays) and columns are SIMD batches. **Each bar is one SIMD vector**: one component for `lanes` consecutive rows (8 with AVX2, 4 with SSE), drawn as that many lane slots. Playback walks through the recorded steps in program order. A bar lights up when the trace shows it loaded or stored, colored by where it came from (green L1, yellow L2, orange L3, red main memory), then fades. An outlined bar with one lit lane is an access narrower than a vector, such as a scalar read or a broadcast. Stack and other heap are drawn per cache line.
- **Vector ticker.** Above the map, the most recent vector loads in this moment, each as a register with numbered lanes and a label like "Joint velocity · component 2 of 6 · rows 8–15, one 32-byte load".
- **Around it:** the pass that's running, the cache-level mix for this moment, and a scrub bar with every pass colored by algorithm. Controls: play/pause (space), speed, previous/next pass, scrub, arrow keys for single frames, and hover for block, component and rows.
- **Full breakdown** (collapsed): per-pass and per-block tables, the reuse-distance histogram against the L1/L2/L3 capacities, page faults, TLB walks and the cache model used.

Registers can't be traced directly: a value kept in a register makes no memory access at all. Two things in the report stand in for it. Fewer accesses per instruction means more work stayed in registers. Stack traffic inside a pass is mostly **register spills**, where values didn't fit and got pushed to the stack.

## How it works

| Piece | What it does |
|---|---|
| `include/util/memviz.hpp` | Markers. `ACHILLES_MEMVIZ_REGION` labels a field block with its planar layout (component count, scalar size, lane count); `ACHILLES_MEMVIZ_SCOPE` brackets a pass or step. **They compile to nothing unless the build sets `-DACHILLES_MEMVIZ=ON`.** When on, each is a Valgrind client request: a few no-op instructions outside Valgrind, an in-order line in the trace under it. Names are turned into C strings at compile time so markers don't add their own copying to the trace. |
| Engine hooks | `SimAllocator::Carve` labels each field block, `RunPass` brackets each pass (Op and traversal names), `Simulation::Step` brackets each step. That's the whole footprint in engine code. |
| `driver.cpp` → `memviz_driver` | Loads a scene and runs exactly `--steps` ticks. `src/main.cpp` ticks by wall-clock time, which doesn't suit a 100× slower Valgrind run. |
| Valgrind Lackey | Records every data access the program makes, after compiler optimization, register spills included. |
| `sim.cpp` → `memviz_sim` | Reads the trace from a pipe, maps each arena access to the (field, component, batch) vector it touched and whether it was a full aligned vector, and simulates L1/L2/L3 (LRU, set-associative, allocate on miss), a two-level TLB, first-touch page faults and reuse distance. |
| `memviz.py` | Runs `valgrind … memviz_driver | memviz_sim`, then writes `report.html` and `summary.json`. Standard-library Python. |
| `report_template.html` | The page: no external scripts or fonts, light and dark mode. |

## Run it

Inside the dev container, or any machine with Valgrind and its headers (`apt install valgrind`):

```bash
cmake -S . -B build-memviz -G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=OFF -DACHILLES_MEMVIZ=ON
cmake --build build-memviz
python3 tools/memviz/memviz.py examples/three_joint_arm.arow examples/sim_config.yaml --copies 8 --steps 2 --warmup 2
# -> build-memviz/memviz-report/report.html
```

| Flag | Default | Meaning |
|---|---|---|
| `--copies N` | 1 | Instances of the scene's archetype. The root can't be repeated, so the tool writes a temporary scene with the original as the root plus N−1 attached copies. They all attach to the root's first joint, so they overlap and the contact solver does a lot of work. |
| `--steps` / `--warmup` | 2 / 2 | Steps recorded / steps run first so the caches start warm |
| `--caches` | `L1=48K/12,L2=3M/12,L3=24M/12` | Sizes and ways of each level |
| `--tlb` | `64/4,2048/16` | DTLB and STLB entries / ways |
| `--frames` | 600 | Animation frames the recorded steps are cut into (600 is 20 s at 1×). Each frame shows every line touched in its slice of program order; the tables count every access. |
| `--focus-op` | `IntegrateVelocityOp` | In `summary.json` (`focus`), the access widths, alignment, loads and stores per block for passes whose op name contains this. Every block in `by_region` also carries its access widths: 16 B accesses are SSE batches (4 floats), 32 B are AVX2 batches (8 floats). |
| `--validate` | off | Also runs Callgrind's own cache simulator on the same steps and prints both side by side |
| `--build`, `-o` | `build-memviz`, `build-memviz/memviz-report` | Build directory and output directory |

For an 8-lane (AVX2) build, configure a second build directory with `"-DCMAKE_CXX_FLAGS=-mavx2 -mfma"` and pass `--build build-memviz-avx2`. Avoid `-march=native` here: newer CPUs enable instruction sets Valgrind 3.19 can't run.

Time: about 20 s for one arm and 2 minutes for 8 three-joint arms (the program runs roughly 50 to 100× slower under Valgrind).

## How far to trust it

- **The accesses are exact.** Valgrind sees every load and store the binary really performs. `--validate` checks the count against Callgrind: one arm, steps 3–4 matched to within 0.01% (933,808 vs 933,817 reads).
- **Where each was served from is a model.** The default geometry is what the development laptop reports (Intel Core Ultra 9 285H: 48 KiB 12-way L1d, 3 MiB L2, 24 MiB L3, 64 B lines). TLB sizes are typical values; WSL exposes neither TLB geometry nor hardware performance counters, so there's nothing to measure against directly. Against Callgrind's independent simulator with the same L1, L1 misses agreed within 2% (6,490 vs 6,616). Real hardware also has prefetchers, which this model doesn't, so real miss rates on streaming access are lower.
- **Markers cost a little.** Each pass marker is a Valgrind client request whose own argument setup adds a few stack stores per pass. That's about 800 markers per step against hundreds of thousands of accesses.
- **Valgrind 3.19 handles up to AVX2.** Builds with `-march=native` on AVX-512 machines won't run under it.
