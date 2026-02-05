#!/usr/bin/env python3
"""
SLAM Launch File for Steve Robot
Supports both real hardware and simulation modes
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # Launch configurations
    use_sim_time = LaunchConfiguration('use_sim_time')
    world = LaunchConfiguration('world')
    params_file = LaunchConfiguration('params_file')

    # Declare launch arguments
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time (true) or real hardware (false)'
    )

    declare_world_cmd = DeclareLaunchArgument(
        'world',
        default_value='small_house',
        description='World to load in Gazebo (only used when use_sim_time:=true). '
                    'Available: "neo_workshop", "neo_track1", "small_house", or full path to .world file'
    )

    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(
            get_package_share_directory('neo_nav2_bringup'),
            'config',
            'mapping.yaml'
        ),
        description='Full path to SLAM parameters file'
    )

    # Simulation mode: Launch Gazebo simulation
    simulation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('neo_simulation2'),
                'launch',
                'simulation.launch.py'
            )
        ),
        launch_arguments={
            'my_robot': 'mmo_700',
            'world': world,
            'use_sim_time': 'true',
            'arm_type': 'ur5e',
            'include_pan_tilt': 'true',
            'use_rviz': 'false'  # Disable simulation RViz
        }.items(),
        condition=IfCondition(use_sim_time)
    )

    # Hardware mode: Launch real robot hardware
    hardware_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('steve_hardware_bringup'),
                'launch',
                'hardware_bringup.launch.py'
            )
        ),
        launch_arguments={
            'robot_namespace': '',
            'arm_type': 'ur5e',
            'enable_camera': 'true',
            'enable_pan_tilt': 'true'
        }.items(),
        condition=UnlessCondition(use_sim_time)
    )

    # SLAM toolbox (always launched)
    mapping_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('neo_nav2_bringup'),
                'launch',
                'mapping.launch.py'
            )
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'param_file': params_file
        }.items()
    )

    ld = LaunchDescription()
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_world_cmd)
    ld.add_action(declare_params_file_cmd)
    ld.add_action(simulation_launch)
    ld.add_action(hardware_launch)
    ld.add_action(mapping_launch)

    return ld
