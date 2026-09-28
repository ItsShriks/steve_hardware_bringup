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
- `enable_camera:=true` (default: true) — pan-tilt L515
- `enable_wrist_camera:=true` (default: true) — wrist D405 (`wrist_camera.launch.py`)
- `enable_joystick:=true` (default: true)
- `arm_tool:=robotiq_2f_85` — adds the gripper to the robot description/TF (default `none`).
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