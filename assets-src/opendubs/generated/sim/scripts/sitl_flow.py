"""ArduPilot's EKF3 on optical flow alone, in SITL: a simulated rover with a simulated
flow sensor 10 cm above the floor, no GPS. It drives the same test Eric ran with
motion capture: straight 5.5 m, back, then a spin in place. Records the EKF's
position against the simulator's ground truth.

  sitl_flow.py <ardurover binary> <ardupilot dir> <out.npz> <flow yaw, centidegrees>

<flow yaw> is FLOW_ORIENT_YAW, the sensor's mounting as configured. The simulated
sensor reports in the body frame, so 0 is a correct config and 9000 is the 90-degree
mismatch Eric's teammates found.
"""
import glob
import os
import shutil
import subprocess
import sys
import time

import numpy as np
from pymavlink import mavutil

binary, ap, out, yaw_cd = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
H = float(os.environ.get("H", 0.10))          # sensor height above the floor, m
GAIN = int(os.environ.get("GAIN", 0))          # FLOW_FXSCALER/FYSCALER
OFF = float(os.environ.get("OFF", 0.0))       # sensor ahead of the turning centre, m
THR = int(os.environ.get("THR", 40))          # throttle offset from neutral, PWM
T_LEG = float(os.environ.get("T_LEG", 12))    # seconds per straight leg
run = os.path.join(os.path.dirname(os.path.abspath(out)), f"sitl-{yaw_cd}")
shutil.rmtree(run, ignore_errors=True)       # fresh parameters each run
os.makedirs(run)

LAT0, LNG0 = -35.363261, 149.165230        # SITL's default home
PARAMS = {
    "SIM_FLOW_ENABLE": 1, "FLOW_TYPE": 10, "FLOW_ORIENT_YAW": yaw_cd,
    "SIM_FLOW_POS_X": OFF, "SIM_FLOW_POS_Z": -H,                 # sensor 10 cm above the floor (the rover's origin is at the floor)
    "SIM_FLOW_RND": 0.05,
    "FLOW_FXSCALER": GAIN, "FLOW_FYSCALER": GAIN,  # flow gain trim, parts per thousand
    "FLOW_POS_X": OFF if yaw_cd == 0 else 0.0, "FLOW_POS_Y": 0.0, "FLOW_POS_Z": 0.0,
    "SIM_GPS_DISABLE": 1, "GPS1_TYPE": 0,
    "AHRS_EKF_TYPE": 3, "EK3_SRC1_POSXY": 0, "EK3_SRC1_VELXY": 5, "EK3_SRC1_VELZ": 0,
    "EK3_SRC1_POSZ": 1, "EK3_SRC1_YAW": 1,
    "EK3_MAX_FLOW": 7.0,                     # 10 cm off the floor, walking pace is several rad/s of flow
    "RNGFND1_TYPE": 100, "RNGFND1_ORIENT": 25, "RNGFND1_MIN_CM": 2, "RNGFND1_MAX_CM": 400,
    "RNGFND1_GNDCLEAR": 100 * H, "RNGFND1_POS_Z": 0.0, "SIM_SONAR_POS_Z": -H,
    "ARMING_CHECK": 0, "SIM_SPEEDUP": 4,
}


def start():
    dp = os.path.join(ap, "Tools/autotest/default_params")
    return subprocess.Popen([binary, "--model", "rover-skid", "--speedup", "4", "-I0",
                             "--defaults", f"{dp}/rover.parm,{dp}/rover-skid.parm"],
                            cwd=run, stdout=open(os.path.join(run, "sitl.log"), "w"), stderr=subprocess.STDOUT)


def connect():
    for _ in range(60):
        try:
            c = mavutil.mavlink_connection("tcp:127.0.0.1:5760", source_system=255)
            c.wait_heartbeat(timeout=10)
            return c
        except Exception:
            time.sleep(1)
    raise RuntimeError("no SITL")


def set_params(c, params):
    for k, v in params.items():
        c.mav.param_set_send(c.target_system, c.target_component, k.encode(), float(v),
                             mavutil.mavlink.MAV_PARAM_TYPE_REAL32)
        time.sleep(0.05)
    time.sleep(1)


p = start()
c = connect()
print("connected", flush=True)
set_params(c, PARAMS)
c.close()
p.terminate(); p.wait()
time.sleep(3)                                 # let the port go
p = start()                                   # reboot so the sensor and EKF settings take hold
c = connect()
c.mav.request_data_stream_send(c.target_system, c.target_component, mavutil.mavlink.MAV_DATA_STREAM_ALL, 20, 1)
time.sleep(5)
# No GPS: give the EKF an origin (the SITL home).
c.mav.set_gps_global_origin_send(c.target_system, int(LAT0 * 1e7), int(LNG0 * 1e7), 584000)
time.sleep(10)
c.set_mode("MANUAL")
for _ in range(30):
    c.arducopter_arm()
    hb = c.recv_match(type="HEARTBEAT", blocking=True, timeout=2)
    if hb and hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED:
        break
else:
    raise RuntimeError("would not arm")
print("armed", flush=True)

rec = {"t": [], "truth": [], "ekf": [], "yaw": [], "flow": []}
truth = [None, None, None]


def drive(seconds, throttle, steer):
    t_end = time.time() + seconds / 4.0       # SIM_SPEEDUP 4
    while time.time() < t_end:
        c.mav.rc_channels_override_send(c.target_system, c.target_component, steer, 0, throttle, 0, 0, 0, 0, 0)
        msg = c.recv_match(type=["SIMSTATE", "LOCAL_POSITION_NED", "OPTICAL_FLOW", "EKF_STATUS_REPORT"], blocking=True, timeout=0.05)
        if msg is None:
            continue
        if msg.get_type() == "SIMSTATE":
            n = (msg.lat * 1e-7 - LAT0) * 111320.0
            e = (msg.lng * 1e-7 - LNG0) * 111320.0 * np.cos(np.radians(LAT0))
            truth[:] = (n, e, msg.yaw)
        elif msg.get_type() == "EKF_STATUS_REPORT":
            rec["ekf_flags"] = msg.flags
        elif msg.get_type() == "OPTICAL_FLOW":
            rec["flow"].append((msg.flow_comp_m_x, msg.flow_comp_m_y, msg.quality, msg.ground_distance))
        elif truth[0] is not None:
            rec["t"].append(msg.time_boot_ms * 1e-3)
            rec["truth"].append(truth[:2])
            rec["yaw"].append(truth[2])
            rec["ekf"].append((msg.x, msg.y))


# Eric's test: straight out 5.5 m and back, then spin in place. EKF3 ignores flow until
# it sees the vehicle "take off" (for a rover, any turn over 0.1 rad/s), so start with a turn.
drive(3, 1500, 1500)
drive(1.5, 1500, 1700)
drive(1.5, 1500, 1300)
drive(3, 1500, 1500)
drive(T_LEG, 1500 + THR, 1500)
drive(3, 1500, 1500)
drive(T_LEG, 1500 - THR, 1500)
drive(3, 1500, 1500)
drive(20, 1500, 1900)
drive(3, 1500, 1500)
c.mav.rc_channels_override_send(c.target_system, c.target_component, 1500, 0, 1500, 0, 0, 0, 0, 0)
p.terminate(); p.wait()
time.sleep(2)
# Ground truth and the EKF both from the onboard log, where each has its own timestamp.
log = sorted(glob.glob(os.path.join(run, "logs", "*.BIN")), key=os.path.getmtime)[-1]
mlog = mavutil.mavlink_connection(log)
sim, kf = [], []
while True:
    msg = mlog.recv_match(type=["SIM", "XKF1"])
    if msg is None:
        break
    if msg.get_type() == "SIM":
        sim.append((msg.TimeUS * 1e-6, (msg.Lat - LAT0) * 111320.0,
                    (msg.Lng - LNG0) * 111320.0 * np.cos(np.radians(LAT0)), msg.Yaw))
    elif msg.C == 0:
        kf.append((msg.TimeUS * 1e-6, msg.PN, msg.PE))
sim, kf = np.array(sim), np.array(kf)
t0 = armed_at = kf[0, 0]
t = kf[:, 0]
truth = np.c_[np.interp(t, sim[:, 0], sim[:, 1]), np.interp(t, sim[:, 0], sim[:, 2])]
yaw = np.interp(t, sim[:, 0], np.unwrap(np.radians(sim[:, 3])))
ekf = kf[:, 1:]
moving = np.where(np.linalg.norm(truth - truth[0], axis=1) > 0.005)[0]
start = max(0, moving[0] - 200) if len(moving) else 0     # from a little before it first moves
t, truth, ekf, yaw = t[start:] - t[start], truth[start:] - truth[start], ekf[start:] - ekf[start], yaw[start:]
np.savez(out, t=t, truth=truth, ekf=ekf, yaw=yaw, yaw_cd=yaw_cd, gain=GAIN)
err = np.linalg.norm(truth - ekf, axis=1)
print("samples", len(err), "max error %.3f m, final %.3f m, distance %.2f m" % (err.max(), err[-1], np.abs(truth[:, 0]).max()))
