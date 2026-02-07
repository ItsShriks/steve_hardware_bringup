#!/usr/bin/env python3
"""
Localization and Navigation Launch File for Steve Robot
Supports both real hardware and simulation modes

NOTE: For hardware mode, assumes hardware_bringup.launch.py is already running
      (e.g., as a background cron job on robot startup)
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchContext, LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def launch_setup(context: LaunchContext, use_sim_time_arg, world_arg, map_arg):
    """Setup function to dynamically compute map path based on world selection"""
    launch_actions = []

    use_sim_time = use_sim_time_arg.perform(context)
    world = world_arg.perform(context)
    map_path = map_arg.perform(context)

    # If map is not explicitly provided and in simulation mode, derive it from world name
    if map_path == "" and use_sim_time == "true":
        # Extract world name if it's a built-in world
        if world in ["neo_workshop", "neo_track1", "small_house"]:
            world_name = world
        else:
            # For custom world paths, try to extract the base name
            world_name = os.path.splitext(os.path.basename(world))[0]

        # Construct map path
        map_path = os.path.join(
            get_package_share_directory("steve_simulation"),
            "maps",
            f"{world_name}.yaml",
        )
        print(f"[INFO] Auto-detected map file: {map_path}")

    # Simulation mode: Launch Gazebo simulation
    simulation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("steve_simulation"),
                "launch",
                "simulation.launch.py",
            )
        ),
        launch_arguments={
            "my_robot": "mmo_700",
            "world": world,
            "use_sim_time": "true",
            "arm_type": "ur5e",
            "include_pan_tilt": "true",
            "use_rviz": "false",  # Disable simulation RViz, use navigation RViz instead
        }.items(),
        condition=IfCondition(use_sim_time_arg),
    )

    # Localization (AMCL + Map Server) - always launched
    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("steve_navigation"),
                "launch",
                "localization_amcl.launch.py",
            )
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "map": map_path,
            "params_file": os.path.join(
                get_package_share_directory("steve_navigation"),
                "config",
                "localization.yaml",
            ),
        }.items(),
    )

    # Navigation (Nav2) - always launched with RViz
    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("steve_navigation"),
                "launch",
                "navigation_neo.launch.py",
            )
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "params_file": os.path.join(
                get_package_share_directory("steve_navigation"),
                "config",
                "navigation.yaml",
            ),
            "use_rviz": "true",  # Enable RViz for visualization
        }.items(),
    )

    launch_actions.append(simulation_launch)
    launch_actions.append(localization_launch)
    launch_actions.append(navigation_launch)

    return launch_actions


def generate_launch_description():
    ld = LaunchDescription()

    # Declare launch arguments
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="Use simulation time (true) or real hardware (false)",
    )

    declare_world_cmd = DeclareLaunchArgument(
        "world",
        default_value="small_house",
        description="World to load in Gazebo (only used when use_sim_time:=true). "
        'Available: "neo_workshop", "neo_track1", "small_house", or full path to .world file',
    )

    declare_map_cmd = DeclareLaunchArgument(
        "map",
        default_value=os.path.join(
            get_package_share_directory("steve_simulation"), "maps", "hrsl.yaml"
        ),
        description="Full path to map yaml file to load. "
        "If empty and use_sim_time:=true, will auto-detect based on world name. "
        "For hardware mode, defaults to hrsl.yaml.",
    )

    use_sim_time_arg = LaunchConfiguration("use_sim_time")
    world_arg = LaunchConfiguration("world")
    map_arg = LaunchConfiguration("map")

    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_world_cmd)
    ld.add_action(declare_map_cmd)

    # Use OpaqueFunction to dynamically compute map path
    ld.add_action(
        OpaqueFunction(
            function=launch_setup, args=[use_sim_time_arg, world_arg, map_arg]
        )
    )

    return ld
