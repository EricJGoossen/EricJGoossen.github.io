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

`make_kf_media.py <odom_data dir> <out dir>` draws the Kalman-filter clips from Eric's competition logs
(`odom_data.zip`, sent Oct 24, kept out of the repo): `kf-competition-run.mp4` (the engineer's logged pose
from `Ozone_DataSampling_260630.csv` over `field.png`, with `path.yaml`'s stops, cut to the 4.2 s drive
plus half a second either side) and `kf-tuning.mp4` (`odo_tuner/strafe.csv`, the 5 m sideways push,
replayed by Eric's `odo_tuner/field_odometry_replay.py` with the pods moving from their design values to
his tuned ones, against the same log's IMU heading; the dashed reference is that IMU heading's version of the push, moving
straight sideways in the robot's frame while turning as the IMU says, scaled to 5 m). Frames to clips (960 px wide):

    ffmpeg -framerate 30 -i auto/frame_%04d.png -vf scale=960:-2 -c:v libx264 -crf 26 -preset slow -pix_fmt yuv420p -an -movflags +faststart kf-competition-run.mp4
    ffmpeg -framerate 30 -i sweep/frame_%04d.png -vf scale=960:-2 -c:v libx264 -crf 26 -preset slow -pix_fmt yuv420p -an -movflags +faststart kf-tuning.mp4

`make_lqr_media.py <csv dir> <out dir>` draws `lqr-vs-pure-pursuit.mp4` (frames; then
`ffmpeg -framerate 30 -i frames/frame_%04d.png -vf scale=720:-2,tpad=stop_mode=clone:stop_duration=1.5 ...`)
and `lqr-vs-pure-pursuit.svg` from `data/{slalom,square,engineer}.csv`, the output of LQRPathing's
`tools/compare_pure_pursuit` (branch `finish-mvp`) for these waypoints:

    compare_pure_pursuit 0.4 0.5 3.2 0.9 0.8 1.9 3.4 2.9 0.6 3.9 > slalom.csv
    compare_pure_pursuit 0.5 0.5 4.0 0.5 4.0 4.0 0.5 4.0 > square.csv
    compare_pure_pursuit 0.93 4.10 2.2 3.4 3.54 2.70 > engineer.csv

Why not the square run: `odo_tuner/deadwheel_log.csv` replays (and the firmware logged it) as a loop of
about 1.5 by 1.7 m ending 30–45 cm from its start, while the tool compares it with a closed 1.3 m square.
A joint fit of all nine pod parameters to the square, the spin and the two pushes can only close that
loop by breaking agreement with the IMU (strafe heading +48° against the IMU's −13°), so the square's
true shape is unknown and it is left out. With the tuned pods the pushes come to 4.98 and 4.99 m and
their headings to within 1° of the IMU's; with the design values the strafe reads 4.44 m and +79°.
The tuned strafe ends 20 cm from the IMU's path (the design values, 3.7 m): the two headings wander a
few degrees apart during the minute-long push and meet again at the end.
- `hero-match.mp4`, `.jpg` (hero): round 2 of "ARUW vs RoboGrinder | Match 113 | 3v3 ARC
  Championship 2026" (YouTube PqSzhmRSAZA, MKV from Eric, Oct 25), 8:38–8:50, cropped to the
  center of the field (`crop=1000:1000:400:60`, scaled to 900), CRF 27, no audio.
- `cover-reveal.mp4`, `.jpg` (card): three shots of the sentry from "ROBOT // REVEAL 2026"
  (FGh1yQdJGeM, WebM from Eric): 55.90–57.40 s, 67.00–68.85 s and 69.62–71.52 s, cut at the
  scene changes, cropped to 3:2 and scaled to 960×640, CRF 26, no audio.
