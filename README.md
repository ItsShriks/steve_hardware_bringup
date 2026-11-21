# steve_hardware_bringup

**Hardware Initialization Package** for the Steve Butler robot.

This package manages the startup and coordination of all physical robot components. It relies on drivers provided by **`steve_essentials`**.

## Overview

The robot is designed for **hands-off startup**:
1. **Power On**: Turn the key switch to ON.
2. **Auto-Start**: The system automatically runs `ROS_AUTOSTART.sh` on boot.
3. **Initialization**:
   - **Base**: MMO-700 omnidirectional platform.
   - **Arm**: UR5e with Robotiq gripper.
   - **Sensors**: LiDARs, RealSense L515, IMU.
   - **Input**: Logitech joystick.

---

## Automatic Bringup (`ROS_AUTOSTART.sh`)

The robot is configured to automatically launch the hardware drivers safely inside a `screen` session on boot.

**To monitor the startup process:**
```bash
screen -r bringup
```

**To detach from the session:**
Press `Ctrl + A`, then `D`.

**Logs are available at:**
```bash
tail -f /home/neobotix/ros_logs/bringup.log
```

---

## Manual Launch (Development)

If you need to stop the automatic session and run drivers manually for debugging:

1. **Stop the auto-session:**
   ```bash
   screen -S bringup -X quit
   ```

2. **Launch drivers manually:**
   ```bash
   ros2 launch steve_hardware_bringup hardware_bringup.launch.py
   ```

**Optional Arguments:**
- `arm_type:=ur5e` (default: ur5e)
- `enable_camera:=true` (default: true)
- `enable_joystick:=true` (default: true)

---

## Remote PC (RViz etc. over Wi-Fi)

Multicast discovery is blocked on the lab Wi-Fi, and its access points drop fragmented UDP
packets — so a PC saw no topics, or small ones (`/odom`) but never `/robot_description` or images.

* **Robot:** `config/fastdds_steve.xml` (exported as `FASTRTPS_DEFAULT_PROFILES_FILE` in `~/.bashrc`
  and `~/ROS_AUTOSTART.sh`): UDP datagrams ≤ 1400 B, shared memory inside the robot.
* **PC:** `config/fastdds_remote_pc.xml` → copy to `~/.ros/fastdds_steve.xml`: unicast discovery to
  10.7.4.213 (one locator per robot participant) **and to 127.0.0.1** — without it the PC's own
  nodes (a camera driver on the PC, RViz, the WBC) never discover each other, as multicast is off —
  the same 1400 B limit, and a 16 MB shared-memory segment for camera images on the PC.
  Over Ethernet replace `10.7.4.213` by the robot's wired address.

```bash
source /opt/ros/humble/setup.bash && source ~/steve_ros2_ws/install/setup.bash
export ROS_DOMAIN_ID=69 RMW_IMPLEMENTATION=rmw_fastrtps_cpp FASTRTPS_DEFAULT_PROFILES_FILE=~/.ros/fastdds_steve.xml
ros2 daemon stop   # the daemon keeps old settings
rviz2              # RobotModel: topic /robot_description, Fixed Frame odom
```

## Hardware Dependencies

All hardware drivers are now consolidated in **`steve_essentials`**. This package (`steve_hardware_bringup`) orchestrates their launch.

- **Base Drivers**: `neo_relayboard_v2-2`, `neo_kinematics_omnidrive2`
- **Sensors**: `neo_sick_s300-2`, `realsense-ros`
- **Teleop**: `neo_teleop2`, `joy`

---

## Network Configuration

| Component | Value |
|---|---|
| Robot IP | `10.7.4.213` |
| Ethernet Port | `192.168.60.90` |
| Username | `neobotix` |

**SSH Access:**
```bash
ssh neobotix@10.7.4.213
```

For more details on network setup, see the main [workspace README](../../README.md).

---

### Acknowledgements
- **Rohit Menon** - For mentorship and technical guidance on Neobotix platforms.
- **Prof. Maren Bennewitz** - Head of the Humanoid Robots Lab, University of Bonn.