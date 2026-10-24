# ARUW media sources

`make_aruw.py <odin-characterization checkout> <images dir>` draws, from EricJGoossen/odin-characterization:

- `odin-course.svg` (no longer on the site): `config/campaign.yaml`'s geofence, mapping lanes, figure-8 and
  hold spots, with the paths made by the repo's own `odin_char.robot.motion.figure8_path` and `lawnmower_path`.
- `odin-day1.svg`: the per-step minutes `scripts/estimate_time.py` prints for day 1.
- `odin-system.svg`: the three-part system from the README.

`make_holdout_chart.py <out.svg>` draws `odin-holdout.svg`: the hold-out check from Eric's Odin1 Error
Characterization report (Table 4), each axis's real RMSE against the model's simulated 5–95% band.

From Eric's own figures and screenshots (Oct 24), cropped only:

- `ld19-map.png`: map_01 from the LD19 test (Odin-posed LD19 scans, 5 cm cells, pushed path in red).
- `sensor-coverage.png`: the sentry's sensor coverage, top-down, from the hand-eye mounting.
- `odin-camera-view.jpg`: the view from the Odin's camera on the new mount.
