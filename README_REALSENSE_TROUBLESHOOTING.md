# RealSense Camera Troubleshooting Guide

## ⚡ Quick Fix for L515 Firmware Access Issue

If your diagnostic shows the camera is **physically connected** (USB device detected) but the SDK reports **"No device detected"**, this is a firmware access issue. Follow these steps:

### Immediate Fix (Run on the robot):

```bash
cd ~/steve_ros2_ws/src/steve_hardware_bringup
bash scripts/fix_realsense_l515.sh
```

This script will:
1. ✓ Check and add you to the `plugdev` group
2. ✓ Add L515-specific udev rules
3. ✓ Reset the USB device
4. ✓ Test device detection

**After running the script:**
1. **Unplug and replug** the camera USB cable
2. If you were added to `plugdev` group: **Log out and log back in**
3. Test detection: `rs-enumerate-devices`
4. Launch camera: `ros2 launch steve_hardware_bringup hardware_bringup.launch.py`

---

## Problem
The RealSense L515 camera is not being detected when launching `hardware_bringup.launch.py`.

## Recent Changes
Updated `pan_tilt.launch.py` to include:
- `initial_reset: 'true'` - Forces camera reset on initialization
- `wait_for_device_timeout: '10.0'` - 10-second timeout for device detection
- `serial_no` and `usb_port_id` parameters for specific camera targeting
- `publish_tf: 'true'` - Ensures TF frames are published

## Diagnostic Steps

### 1. Run the Diagnostic Script
```bash
cd ~/neo_700/steve_ros2_ws/src/steve_hardware_bringup
./scripts/check_realsense.sh
```

This will check:
- RealSense SDK installation
- USB device enumeration
- Video device availability
- USB permissions
- ROS 2 package installation

### 2. Check for Connected Cameras
```bash
rs-enumerate-devices
```

Expected output should show your L515 camera with its serial number.

### 3. Test Camera Directly
```bash
# Launch just the camera node
ros2 launch realsense2_camera rs_launch.py device_type:=l515 initial_reset:=true
```

### 4. Check USB Permissions
If the camera is not detected, you may need to set up udev rules:

```bash
# Install RealSense SDK if not already installed
sudo apt install librealsense2-utils librealsense2-dev

# Copy udev rules
sudo cp /usr/local/etc/udev/rules.d/99-realsense-libusb.rules /etc/udev/rules.d/

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Reconnect the camera
```

### 5. Specify Camera by Serial Number
If you have multiple cameras or need to target a specific one:

```bash
# First, get the serial number
rs-enumerate-devices | grep "Serial Number"

# Then launch with the serial number
ros2 launch steve_hardware_bringup hardware_bringup.launch.py \
  enable_pan_tilt:=true \
  enable_camera:=true \
  camera_serial_no:='YOUR_SERIAL_NUMBER'
```

### 6. Check USB Port
If the camera keeps disconnecting or isn't detected:

```bash
# Find USB port ID
lsusb -t

# Launch with specific USB port
ros2 launch steve_hardware_bringup hardware_bringup.launch.py \
  enable_pan_tilt:=true \
  enable_camera:=true \
  usb_port_id:='X-X.X'  # Replace with actual port ID
```

## Common Issues and Solutions

### Issue 1: "No RealSense devices were found"
**Solution:**
- Ensure camera is physically connected
- Check USB cable (try a different one)
- Verify USB 3.0 port (L515 requires USB 3.0)
- Run diagnostic script to check permissions

### Issue 2: Camera detected but no image topics
**Solution:**
- Check if camera node is running: `ros2 node list | grep camera`
- Verify topics: `ros2 topic list | grep camera`
- Check for errors: `ros2 node info /pan_tilt_camera/pan_tilt_camera`

### Issue 3: "Device or resource busy"
**Solution:**
- Another process might be using the camera
- Kill any running realsense-viewer or camera processes
- Use `initial_reset:=true` parameter (already added)

### Issue 4: Timeout waiting for device
**Solution:**
- Increase timeout: modify `wait_for_device_timeout` in `pan_tilt.launch.py`
- Check if camera firmware is up to date
- Try unplugging and replugging the camera

## Launch File Parameters

The updated `pan_tilt.launch.py` now supports:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `namespace` | `''` | Top-level namespace |
| `enable_camera` | `'true'` | Enable/disable camera |
| `camera_serial_no` | `''` | Target specific camera by serial number |
| `usb_port_id` | `''` | Target specific USB port |

## Verification

After launching, verify the camera is working:

```bash
# Check if camera node is running
ros2 node list | grep pan_tilt_camera

# Check available topics
ros2 topic list | grep pan_tilt_camera

# View color image
ros2 run rqt_image_view rqt_image_view /pan_tilt_camera/color/image_raw

# View depth image
ros2 run rqt_image_view rqt_image_view /pan_tilt_camera/depth/image_rect_raw

# Check point cloud
ros2 topic echo /pan_tilt_camera/depth/color/points --once
```

## Additional Resources

- [RealSense ROS 2 Wrapper Documentation](https://github.com/IntelRealSense/realsense-ros)
- [L515 Product Page](https://www.intelrealsense.com/lidar-camera-l515/)
- [RealSense SDK Documentation](https://dev.intelrealsense.com/)
