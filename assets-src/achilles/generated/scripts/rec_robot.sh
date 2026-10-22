#!/usr/bin/env bash
# Record the stock robot_on_plane demo: pause the viewer, queue camera input, capture, resume.
set -e
C=/home/user/ericjgoossen/achilles-cr; export DISPLAY=:99
ZOOM=${1:-6}; DY=${2:--50}; DX=${3:-0}; SECS=${4:-14}; OUT=${5:-robot_raw.mp4}
xdotool mousemove 640 400
$C/build-release/achilles $C/examples/robot_on_plane/robot_on_plane.arow $C/examples/robot_on_plane/sim_config.yaml --integrator euler --dt 0.004 > run.log 2>&1 &
PID=$!
xdotool search --sync --name "Achilles Viewer" > /dev/null
kill -STOP $PID
xdotool mousemove 640 400
for i in $(seq 1 $ZOOM); do xdotool click 4; done
xdotool mousedown 1; xdotool mousemove_relative -- $DX $DY
ffmpeg -loglevel error -y -f x11grab -draw_mouse 0 -framerate ${FPS:-30} -video_size 1280x800 -i :99 -t $SECS -c:v libx264 -crf 16 -preset veryfast -pix_fmt yuv420p $OUT &
FF=$!
kill -CONT $PID
sleep 0.3; xdotool mouseup 1; xdotool mousemove 1279 799
wait $FF; kill $PID 2>/dev/null || true
