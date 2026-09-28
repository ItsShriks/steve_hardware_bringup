#!/usr/bin/env python3
"""
Wrist RealSense D405 (colour + aligned depth) for Steve.

The camera is bound by its serial number from robot_config.yaml (cameras.wrist_d405_serial),
so it does not matter which USB port it is on or whether the pan-tilt L515 enumerates first.
The camera frames come from the URDF (wrist_camera_* links), so the driver publishes no TF.

    ros2 launch steve_hardware_bringup wrist_camera.launch.py
    ros2 launch steve_hardware_bringup wrist_camera.launch.py serial_no:=_123456789012
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

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


def rs_serial(serial):
    """realsense2_camera serial_no argument ('' = any camera; '_' keeps digits a string)."""
    return f"_{serial}" if str(serial or "").strip() else "''"


def generate_launch_description():
    serial = LaunchConfiguration("serial_no")
    return LaunchDescription([
        DeclareLaunchArgument("serial_no", default_value=rs_serial(ROBOT_CFG["cameras"].get("wrist_d405_serial")),
                              description="D405 serial as _<digits> (default: robot_config.yaml)"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                get_package_share_directory("realsense2_camera"), "launch", "rs_launch.py")),
            launch_arguments={
                # topics /wrist_camera/wrist_camera/..., frames wrist_camera_* as in the URDF
                "camera_namespace": "wrist_camera",
                "camera_name": "wrist_camera",
                "serial_no": serial,
                "device_type": "d405",
                "publish_tf": "false",
                "enable_color": "true",
                "enable_depth": "true",
                "align_depth.enable": "true",
                "rgb_camera.color_profile": "640x480x30",
                "depth_module.depth_profile": "640x480x30",
                "initial_reset": "true",
                "wait_for_device_timeout": "10.0",
            }.items(),
        ),
    ])
