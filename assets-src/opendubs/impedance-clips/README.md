# Impedance clips

The three robot clips behind `src/projects/opendubs/images/impedance-control-clips.mp4`
(each Eric's Cartesian impedance controller: gravity compensation only; stiff in x and y,
compliant in z and rotation; stiff in x and y, compliant in rotation). Rebuild the combined
video, 16 s, with a label on each:

    F=/usr/share/fonts/opentype/inter/Inter-Medium.otf
    lab() { echo "drawtext=fontfile=$F:text='$1':fontcolor=white:fontsize=$2:x=14:y=14:box=1:boxcolor=black@0.55:boxborderw=8"; }
    ffmpeg -t 16 -i impedance-control-hand-guided.mp4 -t 16 -i impedance-control-wrist.mp4 \
      -t 16 -i impedance-control-rotation-compliant.mp4 -filter_complex \
      "[0]scale=360:640,setsar=1,$(lab 'Gravity comp only' 20)[a];[1]scale=360:640,setsar=1,$(lab 'Compliant in z and rotation' 20)[b];[2]scale=720:406,setsar=1,$(lab 'Compliant in rotation only' 22)[c];[a][b]hstack[top];[top][c]vstack,format=yuv420p" \
      -an -c:v libx264 -crf 27 -preset slow -movflags +faststart impedance-control-clips.mp4
