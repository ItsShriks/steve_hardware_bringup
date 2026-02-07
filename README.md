# steve_hardware_bringup

Hardware initialization and driver management for the **Steve Butler** robot.  
This package is responsible for the **automatic startup and coordination of all robot hardware**, including the base platform, UR5e arm, cameras, and sensors.

All components are launched automatically on robot boot — **no manual bringup required**.

---

## Overview

This package provides:

- **Automatic hardware bringup** via `ROS_AUTOSTART.sh` on system boot
- **UR5e arm integration** with automatic connection and control
- **Sensor initialization**, including LiDARs, RealSense cameras, and IMU
- **Base platform drivers** for the Neobotix MMO-700 omnidirectional base
- **Joystick teleoperation** support

The system is designed for **hands-off startup**: once powered on, the robot initializes itself and becomes ready for operation.

---

## Robot Startup Procedure

### 1. Power On the Robot

1. Turn the **key switch** to the **ON** position  
   - The robot will start in **Emergency Stop mode**

2. Power on the **UR control panel**
   - Press the power button
   - Wait until the panel fully boots

3. When prompted with **“TURN KEY →”**, turn the key again  
   - The base platform will initialize
   - The wheels may rotate briefly during this process

---

### 2. Initialize the UR5e Arm

1. On the UR panel, click the **bottom-left icon** to open the initialization screen
2. Press **ON** to power the arm
3. Press **START** to release the brakes
4. Press **Exit** to return to the main screen
5. Press the **Play** button and select **Robot Program**

This enables **remote control via ROS 2**.  
The arm automatically connects to the ROS 2 driver launched by `ROS_AUTOSTART.sh`.

> **Note**  
> The ROS 2 arm driver is started automatically at boot.  
> If the arm does not connect, see the [Troubleshooting](#troubleshooting) section.

---

## Robot Communication

### Network Configuration

| Component | Value |
|---------|-------|
| Robot IP | `10.7.4.213` |
| Ethernet Port | `192.168.60.90` (DHCP) |
| Username | `neobotix` |
| Password | `neobotix` |

---

### SSH Access

```bash
ssh neobotix@10.7.4.213
```

With X11 forwarding:
```bash
ssh -X neobotix@10.7.4.213
```
---
### VS Code Remote Access
	1.	Install Remote – SSH
	2.	Press F1 → Remote-SSH: Add New SSH Host
	3.	Enter:
```bash
ssh neobotix@10.7.4.213
```
	4.	Connect to the host
	5.	Open the workspace:
    ```bash
    ~/steve_ros2_ws
    ```
---

### Automatic Bringup System

```~/ROS_AUTOSTART.sh```

```bash
#!/bin/bash

source /opt/ros/humble/setup.bash
source ~/steve_ros2_ws/install/setup.bash

export ROS_DOMAIN_ID=74
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

if screen -list | grep -q "bringup"; then
    echo "Bringup already running."
    exit 0
fi

sleep 2

screen -S bringup -L \
  -Logfile "/home/neobotix/ros_logs/bringup.log" \
  -dm bash -c \
  "source ~/steve_ros2_ws/install/setup.bash && \
   ros2 launch steve_hardware_bringup hardware_bringup.launch.py"

echo "Hardware bringup started."
```
---

### Launched Components
	•	MMO-700 base drivers (CAN, motors, IMU)
	•	UR5e arm (ros2_control, reverse interface)
	•	Dual LiDAR sensors
	•	RealSense L515 camera (pan-tilt)
	•	Logitech joystick controller

---
### Monitoring Bringup
```bash
screen -ls
screen -r bringup
```
Detach with:
```bash
Ctrl + A → D
```

Logs:
```bash
tail -f /home/neobotix/ros_logs/bringup.log
```

---

### Manual Launch Development
```bash
source ~/steve_ros2_ws/install/setup.bash
ros2 launch steve_hardware_bringup hardware_bringup.launch.py
```
Optional arguments:
	•	arm_type:=ur5e
	•	enable_camera:=true
	•	enable_joystick:=true
	•	imu_enable:=true

### Joystick Teleoperation

Enabled automatically on startup.

Controls:
	•	Hold LB + Left Stick → Translate robot
	•	Hold LB + Right Stick → Rotate robot

Manual launch:

```bash
ros2 launch steve_hardware_bringup teleop.launch.py
```
---

### Shutdown Procedures

UR5e Arm
	1.	Press Stop
	2.	Select OFF
	3.	Menu → Shutdown Robot

Robot Base
	1.	Turn key to OFF
	2.	Hold until shutdown completes

⸻

Battery Charging
	1.	Connect charger (right side)
	2.	Charger switch OFF
	3.	Plug into wall
	4.	Switch ON
	5.	Do not charge overnight

---

### Documentation
	•	Neobotix: https://neobotix-docs.de/ros/index.html
	•	UR5e: https://www.universal-robots.com/
	•	ROS 2 Humble: https://docs.ros.org/en/humble/

---

### Contributors
- **Shrikar Nakhye** - [GitHub](https://github.com/Itsshriks) | [Email](mailto:nakhyeshrikar@icloud.com)
- **Pratik Adhikari** - [GitHub](https://github.com/pratik-adhikari) | [Email](mailto:pratikadhikari.de@gmail.com)
- **Riddhesh More** - [GitHub](https://github.com/RiddheshMore) | [Email](mailto:riddheshmore311@gmail.com)
---