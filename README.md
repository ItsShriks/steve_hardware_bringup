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
- `enable_camera:=true` (default: false) — pan-tilt L515
- `enable_pan_tilt:=true` (default: false) — pan-tilt motors
- `enable_wrist_camera:=true` (default: true) — wrist D405 (`wrist_camera.launch.py`)
- `enable_joystick:=true` (default: true) — `false` for WBC tests: `neo_teleop2` publishes
  `/cmd_vel` continuously and would override the controller's base commands
- `ur_autostart:=true` (default: true) — `ur_autostart` node keeps the arm ready: powers it on and
  releases the brakes (`ur_power_on`, default true; the joints click and may move ~1 mm), starts the
  control script (headless: `resend_robot_program`, else PLAY on External Control) and
  re-activates `scaled_joint_trajectory_controller` after every script start. Only with safety
  NORMAL and the pendant in **Remote Control** (once: Settings → System → Remote Control → Enable,
  then Local → Remote at the top right). A protective stop or EM stop is never cleared
  automatically: release / clear it at the pendant, the arm then comes back by itself.
  Never sends a motion.
- `ur_headless:=true` (default: true) — UR driver in headless mode: it sends the control script
  itself, no program on the pendant. `false`: the External Control program (URCap).
- `ur_power_on:=false` — leave power-on and brake release to the pendant.
- `arm_tool:=camera|robotiq_2f_85|none` — end effector in the robot description/TF: `camera` (default:
  the D415 on a post under the flange, links `gripper_camera_mount/_post/_body`; its optical frame is the
  calibrated TF from steve_wbc `gripper_camera.launch.py`), `robotiq_2f_85` (gripper) or `none` (bare flange).
  MoveIt (`steve_manipulation`) and the WBC need it; set it in `ROS_AUTOSTART.sh`.

`steve_manipulation` and `steve_wbc` launch files detect this running bringup (they look for
`/controller_manager`) and do **not** start a second UR driver (`launch_bringup:=auto`).

---

## Robot Configuration (`config/robot_config.yaml`)

Everything that can differ between robots, labs and re-wirings is in **one file**; all launch
files (this package, `steve_manipulation`, `steve_wbc`) take their defaults from it, so after a
change nothing else has to be edited. A launch argument still overrides.

| Section | Keys |
|---|---|
| `network` | `ur_robot_ip` (UR5e controller), `ur_reverse_ip` (this PC on the UR subnet, `""` = automatic) |
| `devices` | `relayboard`, `lidar_1`, `lidar_2` — stable udev names (not `/dev/ttyUSBx`) |
| `cameras` | `pan_tilt_l515_serial`, `wrist_d405_serial` — RealSense cameras bound by serial number, independent of USB ports and enumeration order (`""` = first camera found) |

```bash
export STEVE_ROBOT_CONFIG=/path/to/other_robot.yaml     # another file
export STEVE_UR_ROBOT_IP=192.168.1.50                   # one value, no edit (STEVE_<KEY> or STEVE_<SECTION>_<KEY>)
```

## Setup Check (`steve_doctor`)

```bash
ros2 run steve_hardware_bringup steve_doctor                 # network, serial devices, cameras
ros2 run steve_hardware_bringup steve_doctor --ros           # + are the robot topics alive?
ros2 run steve_hardware_bringup steve_doctor --write-config  # store the detected camera serials
```

* **Network**: this PC's addresses, whether one is on the UR subnet, ping + dashboard (29999) /
  RTDE (30004) ports, and from the UR dashboard the robot mode, whether the *External Control*
  program is playing and remote control; the host IP the URCap must use.
* **Serial devices**: each configured name exists and which USB device (vendor, product,
  serial) it is; all `ttyUSB*` / `ttyACM*` with their identities.
* **Cameras**: connected RealSense models and serials vs. the config.
* **ROS** (`--ros`): `/joint_states`, `/odom`, `/emergency_stop_state` (and its state), both
  filtered scans and both cameras publishing; `scaled_joint_trajectory_controller` active.

Every problem comes with a hint what to do.

**Stable device names (udev).** Plug the devices in, look up their `/dev/ttyUSBx` in the
`steve_doctor` list, then:

```bash
ros2 run steve_hardware_bringup steve_doctor --udev neo-relayboard=/dev/ttyUSB0 \
    neo-s300-1=/dev/ttyUSB1 neo-s300-2=/dev/ttyUSB2
sudo cp 99-steve.rules /etc/udev/rules.d/ && sudo udevadm control --reload && sudo udevadm trigger
```

The rules match the USB vendor/product/serial number (or, for devices without a serial, the
physical USB port — keep those on the same port).

## Safety (EM stop and scanner field)

`neo_relayboard_v2-2` publishes `/emergency_stop_state` (EM-stop buttons, S300 protective field
`scanner_stop`). The base driver stops on an EM stop. The scanner stop was taken out of the
latched EM stop (see "MODIFIED (Steve)" in `NeoRelayBoardNode.cpp`) so the drives are not
disabled and re-initialised on every field violation; the red protective field must still cut
motor power in hardware. The motion scripts (`steve_wbc` controllers, `steve_manipulation`
manipulator) subscribe to `/emergency_stop_state` and stop **base and arm** while an EM stop is
active or the scanner field is red — see `steve_manipulation/safety_stop.py`.

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
export ROS_DOMAIN_ID=74 RMW_IMPLEMENTATION=rmw_fastrtps_cpp FASTRTPS_DEFAULT_PROFILES_FILE=~/.ros/fastdds_steve.xml
ros2 daemon stop   # the daemon keeps old settings
rviz2              # RobotModel: topic /robot_description, Fixed Frame odom
```

## Logs (workspace default)

`env-hooks/steve_logging.sh.in` is sourced with `install/setup.bash` and makes, for this workspace:

* every node started by `ros2 launch` print to the screen **and** to log files
  (`OVERRIDE_LAUNCH_PROCESS_OUTPUT=full`: `launch.log`, `<node>-stdout.log`, `<node>-stderr.log`);
* every `ros2 launch <pkg> <file>` keep its logs in **`~/ros_logs/<launch file>_<date>_<time>/`** (the
  nodes' ROS log files + the launch's own folder), `~/ros_logs/latest` → the newest run.

```bash
ls ~/ros_logs/latest/                              # newest run
export OVERRIDE_LAUNCH_PROCESS_OUTPUT=screen       # this terminal: screen only
export ROS_LOG_DIR=~/.ros/log                      # this terminal: ROS's default log location
```

The second part is a shell function `ros2` (interactive shells that sourced the workspace);
`timeout ros2 launch ...`, `sudo` or other programs start the `ros2` binary directly and log to
ROS's default location (`~/.ros/log`) — with the full output (part 1) all the same.

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
| UR5e controller | `network.ur_robot_ip` in `config/robot_config.yaml` (check: `steve_doctor`) |

**SSH Access:**
```bash
ssh neobotix@10.7.4.213
```

For more details on network setup, see the main [workspace README](../../README.md).

---

### Acknowledgements
- **Rohit Menon** - For mentorship and technical guidance on Neobotix platforms.
- **Prof. Maren Bennewitz** - Head of the Humanoid Robots Lab, University of Bonn.