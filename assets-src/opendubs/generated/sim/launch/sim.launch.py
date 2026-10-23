"""OpenDubs lidar / SLAM / Nav2 replay in Gazebo Harmonic.

Runs Eric's robot description, his lidar merger (eric/lidar_merger.py, unmodified)
and slam_toolbox with his parameters (eric/slam_toolbox_params.yaml), with Nav2 on
top, against a simulated lab room. Only the simulator side is new: the world, the
Gazebo extensions in urdf/opendubs_gz.urdf.xacro, the bridge, and Nav2's params.

    ros2 launch sim.launch.py            (from this folder, with ROS 2 Jazzy sourced)
"""
import os

from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import subprocess
import tempfile
import xml.etree.ElementTree as ET

import xacro

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SIM_TIME = {'use_sim_time': True}


def gazebo_model(urdf):
    """Eric's URDF converted for Gazebo, with the robot's own visuals hidden from its
    lidars: the sim draws his frame as one solid box, where the real frame is open
    rails the RPLIDARs mostly see through."""
    with tempfile.NamedTemporaryFile('w', suffix='.urdf', delete=False) as f:
        f.write(urdf)
    sdf = ET.fromstring(subprocess.run(['gz', 'sdf', '-p', f.name], capture_output=True, text=True, check=True).stdout)
    for visual in sdf.iter('visual'):
        ET.SubElement(visual, 'visibility_flags').text = '2'
    for lidar in sdf.iter('lidar'):
        ET.SubElement(lidar, 'visibility_mask').text = '1'
    path = os.path.join(tempfile.gettempdir(), 'opendubs_gz.sdf')
    ET.ElementTree(sdf).write(path)
    return path


def generate_launch_description():
    robot_description = xacro.process_file(os.path.join(ROOT, 'urdf', 'opendubs_gz.urdf.xacro')).toxml()

    gazebo = ExecuteProcess(
        cmd=['gz', 'sim', '-s', '-r', '--headless-rendering', os.path.join(ROOT, 'worlds', 'lab.sdf')],
        output='screen')

    state_publisher = Node(
        package='robot_state_publisher', executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description}, SIM_TIME])

    spawn = Node(
        package='ros_gz_sim', executable='create',
        arguments=['-file', gazebo_model(robot_description), '-name', 'opendubs',
                   '-x', '-3.6', '-y', '1.6', '-z', '0.06', '-Y', '0.0'])

    bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/scan_front@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/scan_back@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/odom_tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            '/overhead/image@sensor_msgs/msg/Image[gz.msgs.Image',
        ],
        remappings=[('/odom_tf', '/tf')],
        parameters=[SIM_TIME])

    # Eric's merger, with the parameters from his robot_params.yaml
    merger = ExecuteProcess(
        cmd=['python3', '-c',
             'import runpy, sys; sys.argv = ["lidar_merger"] + sys.argv[1:]; '
             f'runpy.run_path("{os.path.join(ROOT, "eric", "lidar_merger.py")}", run_name="lidar_merger")["main"]()',
             '--ros-args', '-r', '__node:=lidar_merger_node',
             '-r', 'scan_input1:=scan_front', '-r', 'scan_input2:=scan_back',
             '-p', 'target_frame:=base_link', '-p', 'scan_output:=/scan', '-p', 'min_range:=0.2',
             '-p', 'use_sim_time:=true'],
        output='screen')

    slam = Node(
        package='slam_toolbox', executable='async_slam_toolbox_node', name='slam_toolbox',
        parameters=[os.path.join(ROOT, 'eric', 'slam_toolbox_params.yaml'), SIM_TIME],
        output='screen')
    slam_lifecycle = Node(
        package='nav2_lifecycle_manager', executable='lifecycle_manager', name='lifecycle_manager_slam',
        parameters=[{'autostart': True, 'node_names': ['slam_toolbox'], 'bond_timeout': 0.0}, SIM_TIME])

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('nav2_bringup'), 'launch', 'navigation_launch.py')),
        launch_arguments={'use_sim_time': 'true',
                          'params_file': os.path.join(ROOT, 'config', 'nav2_params.yaml')}.items())

    return LaunchDescription([
        gazebo, state_publisher, bridge,
        TimerAction(period=4.0, actions=[spawn]),
        TimerAction(period=8.0, actions=[merger, slam, slam_lifecycle]),
        TimerAction(period=14.0, actions=[nav2]),
    ])
