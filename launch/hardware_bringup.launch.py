#!/usr/bin/env python3
"""
Main Hardware Bringup Launch File
Launches all hardware components for the Steve robot
"""

import os
from pathlib import Path

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.launch_context import LaunchContext
from launch.launch_description_sources import PythonLaunchDescriptionSource
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


def execution_stage(
    context: LaunchContext,
    robot_namespace,
    arm_type,
    robot_ip,
    enable_camera,
    enable_pan_tilt,
):

    arm_typ = str(arm_type.perform(context))
    
    # Normalize booleans to lowercase string for xacro
    enable_cam = str(enable_camera.perform(context)).lower()
    enable_pt = str(enable_pan_tilt.perform(context)).lower()

    rp_ns = ""
    if robot_namespace.perform(context) != "/":
        rp_ns = robot_namespace.perform(context) + "/"

    launches = []
    pkg_share = get_package_share_directory("steve_hardware_bringup")

    # Process URDF with xacro (use main URDF from steve_simulation directly)
    # The wrapper mmo_700_real.urdf.xacro doesn't properly instantiate the robot
    neo_sim_pkg = get_package_share_directory("steve_simulation")
    urdf_file = os.path.join(neo_sim_pkg, "robots", "mmo_700", "mmo_700.urdf.xacro")

    if not os.path.exists(urdf_file):
        raise FileNotFoundError(
            f"URDF xacro file not found at {urdf_file}. "
            "Please ensure steve_simulation package is installed"
        )

    # Process xacro with appropriate arguments for real robot
    robot_description_content = xacro.process_file(
        urdf_file,
        mappings={
            "use_gazebo": "false",
            "arm_type": arm_typ,
            "include_wrist_camera": enable_cam,
            "include_depth_camera": "false",
            # the tower is always in the description (an obstacle for TF / RViz / MoveIt / WBC);
            # enable_pan_tilt only switches its motors + camera
            "include_pan_tilt": "true",
            # robotiq_2f_85 adds the gripper links/TF (no gripper ros2_control here)
            "arm_tool": LaunchConfiguration("arm_tool").perform(context),
            "gripper_hw": "none",
        },
    ).toxml()

    # Start robot state publisher
    start_robot_state_publisher_cmd = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="steve_robot_state_publisher",
        output="screen",
        namespace=robot_namespace,
        parameters=[
            {"robot_description": robot_description_content, "frame_prefix": rp_ns}
        ],
    )

    launches.append(start_robot_state_publisher_cmd)

    # 1. Robot Base (Relayboard + Kinematics)
    robot_base = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, "launch", "robot_base.launch.py")
        ),
        launch_arguments={"namespace": robot_namespace}.items(),
    )
    launches.append(robot_base)

    # 2. LiDAR Sensors
    lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, "launch", "lidar.launch.py")
        ),
        launch_arguments={"namespace": robot_namespace}.items(),
    )
    launches.append(lidar)

    # 3. Teleop (off for WBC tests: neo_teleop2 publishes /cmd_vel continuously and
    #    would override the controller's base commands)
    if LaunchConfiguration("enable_joystick").perform(context).lower() == "true":
        teleop = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_share, "launch", "teleop.launch.py")
            ),
            launch_arguments={"namespace": robot_namespace}.items(),
        )
        launches.append(teleop)

    # 4. UR5e Arm
    if arm_typ in ["ur5", "ur10", "ur5e", "ur10e"]:
        ur_arm = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_share, "launch", "ur5e_arm.launch.py")
            ),
            launch_arguments={
                "ur_type": arm_typ,
                "robot_ip": robot_ip,
                "tf_prefix": arm_typ,
                "use_tool_communication": "true",
            }.items(),
        )
        launches.append(ur_arm)

        # PLAY External Control + keep the trajectory controller active (no power-on, no motion)
        if LaunchConfiguration("ur_autostart").perform(context).lower() == "true":
            launches.append(Node(
                package="steve_hardware_bringup",
                executable="ur_autostart",
                name="ur_autostart",
                output="screen",
                parameters=[{"robot_ip": robot_ip.perform(context)}],
            ))

        # Sole publisher to forward_velocity_controller: zero velocity if the commanding
        # script stops sending (respawned, so the arm is never left with a stale velocity)
        launches.append(Node(
            package="steve_hardware_bringup",
            executable="arm_velocity_watchdog",
            name="arm_velocity_watchdog",
            output="screen",
            respawn=True,
            respawn_delay=0.5,
        ))

    # Table model in RViz (MarkerArray /table_probe/markers, odom): the latest `table_probe`
    # result, reloaded whenever it is measured again (table_viz:= '' disables it)
    table_viz = LaunchConfiguration("table_viz").perform(context)
    if table_viz:
        launches.append(Node(
            package="steve_wbc",
            executable="table_probe",
            name="table_viz",
            output="screen",
            arguments=["--show", table_viz],
            respawn=True,
            respawn_delay=5.0,
        ))

    # 5. Pan-Tilt Unit
    if enable_pt == "true" or enable_pt == "True":
        pan_tilt = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_share, "launch", "pan_tilt.launch.py")
            ),
            launch_arguments={
                "namespace": robot_namespace,
                "enable_camera": enable_camera,
            }.items(),
        )
        launches.append(pan_tilt)
    else:
        # motors off: publish the tower joints at their rest angles (complete TF / robot state)
        launches.append(Node(
            package="steve_hardware_bringup",
            executable="pan_tilt_static_state",
            name="pan_tilt_static_state",
            output="screen",
        ))

    # 6. Wrist camera (D415/D405, model + serial from robot_config.yaml)
    if LaunchConfiguration("enable_wrist_camera").perform(context).lower() == "true":
        launches.append(IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(pkg_share, "launch", "wrist_camera.launch.py"))))

    # Relaying lidar data to /scan topic
    relay_topic_lidar1 = Node(
        package="topic_tools",
        executable="relay",
        name="steve_relay_lidar1",
        namespace=robot_namespace,
        output="screen",
        parameters=[
            {
                "input_topic": robot_namespace.perform(context)
                + "lidar_1/scan_filtered",
                "output_topic": robot_namespace.perform(context) + "scan",
            }
        ],
    )

    relay_topic_lidar2 = Node(
        package="topic_tools",
        executable="relay",
        name="steve_relay_lidar2",
        namespace=robot_namespace,
        output="screen",
        parameters=[
            {
                "input_topic": robot_namespace.perform(context)
                + "lidar_2/scan_filtered",
                "output_topic": robot_namespace.perform(context) + "scan",
            }
        ],
    )

    launches.append(relay_topic_lidar1)
    launches.append(relay_topic_lidar2)

    return launches


def generate_launch_description():
    # Launch configurations
    robot_namespace = LaunchConfiguration("robot_namespace")
    arm_type = LaunchConfiguration("arm_type")
    robot_ip = LaunchConfiguration("robot_ip")
    enable_camera = LaunchConfiguration("enable_camera")
    enable_pan_tilt = LaunchConfiguration("enable_pan_tilt")

    context_arguments = [
        robot_namespace,
        arm_type,
        robot_ip,
        enable_camera,
        enable_pan_tilt,
    ]

    # Declare the launch arguments
    declare_namespace_cmd = DeclareLaunchArgument(
        "robot_namespace",
        default_value="",
        description="Top-level namespace for the robot",
    )

    declare_arm_cmd = DeclareLaunchArgument(
        "arm_type",
        default_value="ur5e",
        description="Arm type - Options: ur5, ur5e, ur10, ur10e",
    )

    declare_robot_ip_cmd = DeclareLaunchArgument(
        "robot_ip",
        default_value=str(ROBOT_CFG["network"]["ur_robot_ip"]),  # robot_config.yaml
        description="IP address of the UR arm",
    )

    declare_camera_cmd = DeclareLaunchArgument(
        "enable_camera",
        default_value="false",  # pan-tilt tower (motors + L515) not in use for now
        description="Enable RealSense L515 camera - Options: true/false",
    )

    declare_wrist_camera_cmd = DeclareLaunchArgument(
        "enable_wrist_camera",
        default_value="true",
        description="Enable the wrist RealSense (model + serial from robot_config.yaml) - Options: true/false",
    )

    declare_pan_tilt_cmd = DeclareLaunchArgument(
        "enable_pan_tilt",
        default_value="false",  # pan-tilt tower (motors + L515) not in use for now
        description="Enable pan-tilt motors - Options: true/false",
    )

    declare_joystick_cmd = DeclareLaunchArgument(
        "enable_joystick",
        default_value="true",
        description="Joystick teleop (joy + neo_teleop2) - false for WBC / MoveIt base tests",
    )

    declare_table_viz_cmd = DeclareLaunchArgument(
        "table_viz",
        default_value="lab_table",
        description="table model shown in RViz (steve_wbc config/tables/<name>.yaml, reloaded on "
                    "change); '' = off",
    )

    declare_ur_autostart_cmd = DeclareLaunchArgument(
        "ur_autostart",
        default_value="true",
        description="PLAY the External Control program when the arm is powered on and keep "
                    "scaled_joint_trajectory_controller active (never powers on or moves the arm)",
    )

    # Opaque function for configuring all hardware
    opq_function = OpaqueFunction(function=execution_stage, args=context_arguments)

    declare_arm_tool_cmd = DeclareLaunchArgument(
        "arm_tool",
        default_value="none",
        description="End effector in the robot description: none or robotiq_2f_85",
    )

    ld = LaunchDescription()
    ld.add_action(declare_arm_tool_cmd)
    ld.add_action(declare_namespace_cmd)
    ld.add_action(declare_arm_cmd)
    ld.add_action(declare_robot_ip_cmd)
    ld.add_action(declare_camera_cmd)
    ld.add_action(declare_pan_tilt_cmd)
    ld.add_action(declare_wrist_camera_cmd)
    ld.add_action(declare_joystick_cmd)
    ld.add_action(declare_ur_autostart_cmd)
    ld.add_action(declare_table_viz_cmd)
    ld.add_action(opq_function)

    return ld
