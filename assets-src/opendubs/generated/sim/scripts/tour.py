"""Drive the simulated OpenDubs through the room with Nav2 point-to-point goals while
slam_toolbox maps it, recording what the video needs at 5 Hz: the robot's pose in
the map, the two raw scans and Eric's merged scan, the map, and Nav2's plan.

usage: tour.py out.pkl
"""
import math
import pickle
import sys
import threading
import time

import numpy as np
import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from nav_msgs.msg import OccupancyGrid, Path
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import LaserScan
import tf2_ros

# Goals in the map frame (the map starts where the robot does: (-3.6, 1.6) in the world).
WORLD_START = (-3.6, 1.6)
GOALS_WORLD = [(-3.4, -2.4, -1.57), (-0.2, -2.6, 0.0), (2.2, -1.6, 0.6), (4.1, -0.6, 1.57),
               (3.6, 2.4, 3.14), (1.6, -0.4, -2.4), (-1.0, -2.4, 3.14), (-1.4, 1.6, 1.57)]


def to_map(x, y):
    return x - WORLD_START[0], y - WORLD_START[1]


class Recorder(Node):
    def __init__(self):
        super().__init__('tour_recorder', parameter_overrides=[rclpy.Parameter('use_sim_time', value=True)])
        self.tf = tf2_ros.Buffer()
        self.tfl = tf2_ros.TransformListener(self.tf, self)
        self.latest = {}
        map_qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.create_subscription(OccupancyGrid, '/map', lambda m: self.latest.__setitem__('map', m), map_qos)
        for topic in ('/scan', '/scan_front', '/scan_back'):
            self.create_subscription(LaserScan, topic, lambda m, t=topic: self.latest.__setitem__(t, m), 10)
        self.create_subscription(Path, '/plan', lambda m: self.latest.__setitem__('plan', m), 10)
        self.frames = []
        self.goal = None
        self.create_timer(0.2, self.snap)

    def pose(self, frame):
        try:
            t = self.tf.lookup_transform('map', frame, rclpy.time.Time())
        except Exception:
            return None
        q = t.transform.rotation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
        return (t.transform.translation.x, t.transform.translation.y, yaw)

    def scan_xy(self, topic, frame):
        m, p = self.latest.get(topic), self.pose(frame)
        if m is None or p is None:
            return None
        r = np.asarray(m.ranges)
        a = m.angle_min + np.arange(len(r)) * m.angle_increment
        ok = np.isfinite(r) & (r > m.range_min) & (r < m.range_max)
        x, y, th = p
        return np.c_[x + r[ok] * np.cos(a[ok] + th), y + r[ok] * np.sin(a[ok] + th)]

    def snap(self):
        base = self.pose('base_link')
        if base is None:
            return
        f = {'t': self.get_clock().now().nanoseconds / 1e9, 'pose': base, 'goal': self.goal,
             'merged': self.scan_xy('/scan', 'base_link'),
             'front': self.scan_xy('/scan_front', 'front_lidar_link'),
             'back': self.scan_xy('/scan_back', 'back_lidar_link')}
        plan = self.latest.get('plan')
        if plan is not None:
            f['plan'] = np.array([[p.pose.position.x, p.pose.position.y] for p in plan.poses])
        m = self.latest.get('map')
        if m is not None and (not self.frames or self.frames[-1].get('map_stamp') != m.header.stamp.sec + m.header.stamp.nanosec * 1e-9):
            f['map'] = (np.array(m.data, dtype=np.int8).reshape(m.info.height, m.info.width), m.info.resolution,
                        m.info.origin.position.x, m.info.origin.position.y)
        if m is not None:
            f['map_stamp'] = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        self.frames.append(f)


def main():
    rclpy.init()
    rec = Recorder()
    nav = BasicNavigator()
    spin = threading.Thread(target=rclpy.spin, args=(rec,), daemon=True)
    spin.start()
    nav.waitUntilNav2Active(localizer='slam_toolbox')
    results = []
    for gx, gy, gyaw in GOALS_WORLD:
        mx, my = to_map(gx, gy)
        goal = PoseStamped()
        goal.header.frame_id = 'map'
        goal.header.stamp = nav.get_clock().now().to_msg()
        goal.pose.position.x, goal.pose.position.y = mx, my
        goal.pose.orientation.z, goal.pose.orientation.w = math.sin(gyaw / 2), math.cos(gyaw / 2)
        rec.goal = (mx, my)
        nav.goToPose(goal)
        start = time.time()
        while not nav.isTaskComplete():
            time.sleep(0.2)
            if time.time() - start > 120:
                nav.cancelTask()
        res = nav.getResult()
        results.append(((gx, gy), str(res)))
        print('goal', (gx, gy), res, flush=True)
    time.sleep(2)
    pickle.dump({'frames': rec.frames, 'results': results, 'world_start': WORLD_START}, open(sys.argv[1], 'wb'))
    print('frames', len(rec.frames), 'succeeded', sum(r == str(TaskResult.SUCCEEDED) for _, r in results), '/', len(results))
    rclpy.shutdown()


if __name__ == '__main__':
    main()
