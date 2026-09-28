"""
Loader for robot_config.yaml, used by the launch files of all Steve packages:

    import os, sys
    from ament_index_python.packages import get_package_share_directory
    sys.path.insert(0, os.path.join(get_package_share_directory("steve_hardware_bringup"), "config"))
    from steve_config import robot_config
    ip = robot_config()["network"]["ur_robot_ip"]

Precedence: launch argument > environment variable STEVE_<SECTION>_<KEY> (e.g.
STEVE_NETWORK_UR_ROBOT_IP; the section may be left out: STEVE_UR_ROBOT_IP) > the file given by
STEVE_ROBOT_CONFIG > robot_config.yaml next to this module.
"""

import os

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))


def config_path():
    return os.environ.get("STEVE_ROBOT_CONFIG") or os.path.join(HERE, "robot_config.yaml")


def robot_config():
    with open(config_path()) as f:
        cfg = yaml.safe_load(f) or {}
    for section, values in cfg.items():
        if not isinstance(values, dict):
            continue
        for key in values:
            for var in (f"STEVE_{section}_{key}".upper(), f"STEVE_{key}".upper()):
                if var in os.environ:
                    values[key] = os.environ[var]
                    break
    return cfg
