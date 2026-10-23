#!/bin/sh
# Build libarmlaws.so: Eric's four control laws, unmodified from his repos at the
# commits below, behind the small C interface in wrapper.cpp, for sim_impedance4.py.
# Needs a Python venv with the pip packages "pin<4" (Pinocchio 3, as in ROS Jazzy),
# cmeel-eigen, cmeel-urdfdom-headers, "cmeel-urdfdom<5" and "cmeel-tinyxml2<11".
#   build_armlaws.sh <venv> <dir holding openarm_cartesian_control and openarm_impedance_control> <out dir>
set -e
V=$1; PRL=$2; OUT=$3
C=$(echo "$V"/lib/python3*/site-packages/cmeel.prefix)
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUT/src" "$OUT/include"
take() {  # take <repo> <commit> <name> <as>
  (cd "$PRL/$1" && git archive "$2" "include/$1/$3.hpp" "src/$3.cpp") | tar -x -C "$OUT/tmp.$4" 2>/dev/null || {
    mkdir -p "$OUT/tmp.$4"; (cd "$PRL/$1" && git archive "$2" "include/$1/$3.hpp" "src/$3.cpp") | tar -x -C "$OUT/tmp.$4"; }
  mkdir -p "$OUT/include/$1"
  cp "$OUT/tmp.$4/include/$1/$3.hpp" "$OUT/include/$1/"
  cp "$OUT/tmp.$4/src/$3.cpp" "$OUT/src/$4_$3.cpp"
}
take openarm_cartesian_control 3bf55b0 cartesian_impedance v1   # pure Cartesian
take openarm_impedance_control 871d1e3 impedance v2             # Cartesian gains in joint space
take openarm_impedance_control eb8e13a impedance_law v3         # Cartesian + null space
take openarm_impedance_control b517999 robot_model v4           # gravity for the motors' PD
g++ -O2 -std=c++17 -shared -fPIC -I "$OUT/include" -I "$C/include" -I "$C/include/eigen3" \
  -I "$C/include/urdfdom" -I "$C/include/urdfdom_headers" "$OUT"/src/*.cpp "$here/wrapper.cpp" \
  -o "$OUT/libarmlaws.so" -L "$C/lib" -lpinocchio_default -lpinocchio_parsers -lurdfdom_model \
  -lconsole_bridge -Wl,-rpath,"$C/lib"
