import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
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

    # --- CONFIGURATION ---
    # Stable udev names from robot_config.yaml (steve_doctor --udev creates the rules)
    LIDAR_1_PORT = str(ROBOT_CFG['devices']['lidar_1'])
    LIDAR_2_PORT = str(ROBOT_CFG['devices']['lidar_2'])
    # ---------------------

    # LiDAR 1 - Front Right (usually neo-s300-1)
    lidar_1_node = Node(
        package='sick_scan_xd',
        executable='sick_generic_caller',
        name='sick_s300_lidar_1',
        output='screen',
        parameters=[{
            'scanner_type': 'sick_s300',
            'port': LIDAR_1_PORT,
            'hostname': '127.0.0.1',  # Dummy IP required by the driver logic
            'frame_id': 'lidar_1_link',
            'range_min': 0.1,
            'range_max': 30.0,
            'use_binary_protocol': True,
        }],
        remappings=[
            ('scan', '/lidar_1/scan'),  # Remapping to match your topic list
        ]
    )

    # LiDAR 2 - Back Left (usually neo-s300-2)
    lidar_2_node = Node(
        package='sick_scan_xd',
        executable='sick_generic_caller',
        name='sick_s300_lidar_2',
        output='screen',
        parameters=[{
            'scanner_type': 'sick_s300',
            'port': LIDAR_2_PORT,
            'hostname': '127.0.0.1',  # Dummy IP required by the driver logic
            'frame_id': 'lidar_2_link',
            'range_min': 0.1,
            'range_max': 30.0,
            'use_binary_protocol': True,
        }],
        remappings=[
            ('scan', '/lidar_2/scan'), # Remapping to match your topic list
        ]
    )

    return LaunchDescription([
        lidar_1_node,
        lidar_2_node
    ])
