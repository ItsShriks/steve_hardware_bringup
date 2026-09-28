import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

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
    """
    Launch file for UR5e robotic arm
    Uses the official Universal Robots ROS2 driver
    """

    # Declare arguments
    robot_ip_arg = DeclareLaunchArgument(
        'robot_ip',
        default_value=str(ROBOT_CFG["network"]["ur_robot_ip"]),  # robot_config.yaml
        description='IP address of the UR5e robot'
    )

    use_fake_hardware_arg = DeclareLaunchArgument(
        'use_fake_hardware',
        default_value='false',
        description='Use fake hardware for testing without real robot'
    )

    # UR5e bringup from ur_robot_driver
    ur5e_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('ur_robot_driver'),
                'launch',
                'ur_control.launch.py'
            ])
        ]),
        launch_arguments={
            'ur_type': 'ur5e',
            'robot_ip': LaunchConfiguration('robot_ip'),
            'use_fake_hardware': LaunchConfiguration('use_fake_hardware'),
            'launch_rviz': 'false',
        }.items()
    )

    return LaunchDescription([
        robot_ip_arg,
        use_fake_hardware_arg,
        ur5e_bringup
    ])
