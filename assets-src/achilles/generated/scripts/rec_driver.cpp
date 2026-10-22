// Standalone driver for Achilles (not part of the repo): steps a scene a fixed
// amount of sim time per frame, optionally renders each frame through the
// library's own viewer and reads it back, and logs every visible body's world pose.
//   rec_driver <scene.arow> <sim_config.yaml> <dt> <fps> <seconds> <frames.rgb|-> <poses.csv>
#include <GL/gl.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <vector>

#include "algorithms/conventions.hpp"
#include "algorithms/integrators.hpp"
#include "algorithms/viz/viz_data.hpp"
#include "engine/topology/ordering_policy.hpp"
#include "interface/simulation.hpp"

using achilles::algorithms::ScalarOperationT;
using achilles::algorithms::viz::VizAlgorithm;
using achilles::algorithms::viz::VizField;
using achilles::engine::topology::TopologicalOrdering;

int main(int argc, char** argv) {
  if (argc < 8) {
    std::fprintf(stderr, "rec_driver scene config dt fps seconds frames.rgb|- poses.csv\n");
    return 1;
  }
  const auto dt = static_cast<ScalarOperationT>(std::strtod(argv[3], nullptr));
  const double fps = std::strtod(argv[4], nullptr);
  const double seconds = std::strtod(argv[5], nullptr);
  const std::string frames_path = argv[6];
  achilles::interface::Simulation sim;
  if (!sim.LoadArowFile(argv[1]) || !sim.LoadConfigFile(argv[2]) || !sim.Init()) return 1;
  sim.SetIntegrator(achilles::interface::Simulation::Integrator::kSemiImplicitEuler);
  const bool render = frames_path != "-";
  std::FILE* frames = render ? std::fopen(frames_path.c_str(), "wb") : nullptr;
  std::ofstream poses(argv[7]);
  poses.precision(9);
  const long steps_per_frame = std::lround(1.0 / (fps * static_cast<double>(dt)));
  const long n_frames = static_cast<long>(seconds * fps);
  std::vector<unsigned char> pixels(1280 * 800 * 3);
  Display* dpy = render ? XOpenDisplay(nullptr) : nullptr;
  for (long f = 0; f <= n_frames; ++f) {
    auto view = sim.ViewFor<VizAlgorithm>();
    auto topo = sim.TopologyFor<TopologicalOrdering>();
    poses << f * steps_per_frame * static_cast<double>(dt);
    for (std::size_t row = 0; row < topo.Size(); ++row) {
      auto e = view.Load<VizField::kVisualExtents, ScalarOperationT>(row);
      if (e.IsZero()) continue;
      auto x = view.Load<VizField::kWorldTransform, ScalarOperationT>(row);
      const auto& t = x.Translation();
      const auto& q = x.Rotation();
      poses << ',' << row << ',' << t.X() << ',' << t.Y() << ',' << t.Z() << ',' << q.W() << ',' << q.X() << ','
            << q.Y() << ',' << q.Z();
    }
    poses << '\n';
    if (render) {
      if (!sim.Render()) break;
      // The viewer window sits at the screen's top-left on the bare Xvfb display.
      XSync(dpy, False);
      XImage* img = XGetImage(dpy, DefaultRootWindow(dpy), 0, 0, 1280, 800, AllPlanes, ZPixmap);
      for (int yy = 0; yy < 800; ++yy) {
        for (int xx = 0; xx < 1280; ++xx) {
          unsigned long p = XGetPixel(img, xx, yy);
          unsigned char* o = &pixels[(static_cast<std::size_t>(yy) * 1280 + xx) * 3];
          o[0] = (p >> 16) & 0xff; o[1] = (p >> 8) & 0xff; o[2] = p & 0xff;
        }
      }
      XDestroyImage(img);
      std::fwrite(pixels.data(), 1, pixels.size(), frames);
    }
    if (f == n_frames) break;
    for (long s = 0; s < steps_per_frame; ++s) {
      if (!sim.Step(dt)) return 1;
    }
  }
  if (frames) std::fclose(frames);
  return 0;
}
