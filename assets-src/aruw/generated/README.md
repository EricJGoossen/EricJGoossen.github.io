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

`make_kf_media.py <odom_data dir> <out dir>` draws the Kalman-filter clips from Eric's competition logs
(`odom_data.zip`, sent Oct 24, kept out of the repo): `kf-competition-run.mp4` (the engineer's logged pose
from `Ozone_DataSampling_260630.csv` over `field.png`, with `path.yaml`'s stops) and `kf-radius-sweep.mp4`
(`odo_tuner/deadwheel_log.csv` replayed by Eric's `odo_tuner/field_odometry_replay.py` while pod `p1`'s
radius sweeps 85–100% of its tuned value). Frames to clips:

    ffmpeg -framerate 30 -i auto/frame_%04d.png -vf scale=720:-2 -c:v libx264 -crf 26 -preset slow -pix_fmt yuv420p -an -movflags +faststart kf-competition-run.mp4
    ffmpeg -framerate 30 -i sweep/frame_%04d.png -vf scale=720:-2 -c:v libx264 -crf 26 -preset slow -pix_fmt yuv420p -an -movflags +faststart kf-radius-sweep.mp4

`make_lqr_media.py <csv dir> <out dir>` draws `lqr-vs-pure-pursuit.mp4` (frames; then
`ffmpeg -framerate 30 -i frames/frame_%04d.png -vf scale=720:-2,tpad=stop_mode=clone:stop_duration=1.5 ...`)
and `lqr-vs-pure-pursuit.svg` from `data/{slalom,square,engineer}.csv`, the output of LQRPathing's
`tools/compare_pure_pursuit` (branch `finish-mvp`) for these waypoints:

    compare_pure_pursuit 0.4 0.5 3.2 0.9 0.8 1.9 3.4 2.9 0.6 3.9 > slalom.csv
    compare_pure_pursuit 0.5 0.5 4.0 0.5 4.0 4.0 0.5 4.0 > square.csv
    compare_pure_pursuit 0.93 4.10 2.2 3.4 3.54 2.70 > engineer.csv
