#!/usr/bin/env python3
"""
Robot Base Launch File
Launches relayboard and kinematics nodes for MPO-700 base platform
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# Robot-specific defaults (IPs, devices, camera serials): steve_hardware_bringup/config/robot_config.yaml
import sys as _sys
_sys.path.insert(0, os.path.join(get_package_share_directory("steve_hardware_bringup"), "config"))
try:
    from steve_config import robot_config  # noqa: E402
    ROBOT_CFG = robot_config()
except Exception as _e:  # the config must never break the bringup: built-in defaults
    print(f"[WARN] robot_config.yaml not loaded ({_e}) - using built-in defaults. Rebuild: "
          "colcon build --symlink-install --packages-select steve_hardware_bringup")
    ROBOT_CFG = {"network": {"ur_robot_ip": "192.168.1.102", "ur_reverse_ip": ""},
                 "devices": {"relayboard": "/dev/neo-relayboard", "lidar_1": "/dev/neo-s300-1",
                             "lidar_2": "/dev/neo-s300-2"},
                 "cameras": {"pan_tilt_l515_serial": "", "wrist_d405_serial": ""}}



def generate_launch_description():
    pkg_share = get_package_share_directory('steve_hardware_bringup')

    # Launch configurations
    robot_namespace = LaunchConfiguration('namespace', default='')

    # Configuration files
    relayboard_config = os.path.join(pkg_share, 'config', 'relayboard_v2.yaml')
    kinematics_config = os.path.join(pkg_share, 'config', 'kinematics.yaml')
    socket_config = os.path.join(pkg_share, 'config', 'socket.yaml')

    # Declare launch arguments
    declare_namespace_cmd = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Top-level namespace for robot base'
    )

    # Relayboard node
    relayboard_node = Node(
        package='neo_relayboard_v2-2',
        executable='neo_relayboard_node',
        name='steve_relayboard_node',
        namespace=robot_namespace,
        output='screen',
        parameters=[relayboard_config, {'port': str(ROBOT_CFG['devices']['relayboard'])}]
    )

    # Kinematics node
    kinematics_node = Node(
        package='neo_kinematics_omnidrive2',
        executable='neo_omnidrive_node',
        name='steve_omnidrive_node',
        namespace=robot_namespace,
        output='screen',
        parameters=[kinematics_config]
    )

    # SocketCAN node
    socketcan_node = Node(
        package='neo_kinematics_omnidrive2',
        executable='neo_omnidrive_socketcan_node',
        name='steve_omnidrive_socketcan_node',
        namespace=robot_namespace,
        output='screen',
        parameters=[socket_config]
    )

    ld = LaunchDescription()
    ld.add_action(declare_namespace_cmd)
    ld.add_action(relayboard_node)
    ld.add_action(kinematics_node)
    ld.add_action(socketcan_node)

    return ld
