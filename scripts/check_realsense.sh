#!/bin/bash
# RealSense Camera Detection Diagnostic Script

echo "========================================="
echo "RealSense Camera Detection Diagnostics"
echo "========================================="
echo ""

# Check if realsense-viewer is installed
echo "1. Checking RealSense SDK installation..."
if command -v realsense-viewer &> /dev/null; then
    echo "   ✓ RealSense SDK is installed"
    rs-enumerate-devices --compact 2>/dev/null || echo "   ⚠ rs-enumerate-devices not found"
else
    echo "   ✗ RealSense SDK not found. Install with: sudo apt install librealsense2-utils"
fi
echo ""

# Check USB devices
echo "2. Checking USB devices..."
if command -v lsusb &> /dev/null; then
    echo "   Intel RealSense devices:"
    lsusb | grep -i "Intel" || echo "   ⚠ No Intel devices found"
else
    echo "   ⚠ lsusb command not available"
fi
echo ""

# Check video devices
echo "3. Checking video devices..."
if [ -d "/dev" ]; then
    VIDEO_DEVICES=$(ls /dev/video* 2>/dev/null)
    if [ -n "$VIDEO_DEVICES" ]; then
        echo "   Available video devices:"
        ls -l /dev/video* 2>/dev/null
    else
        echo "   ⚠ No video devices found in /dev"
    fi
else
    echo "   ⚠ Cannot access /dev directory"
fi
echo ""

# Check USB permissions
echo "4. Checking USB permissions..."
if [ -f "/etc/udev/rules.d/99-realsense-libusb.rules" ]; then
    echo "   ✓ RealSense udev rules found"
else
    echo "   ✗ RealSense udev rules NOT found"
    echo "   → Install with: sudo cp /usr/local/etc/udev/rules.d/99-realsense-libusb.rules /etc/udev/rules.d/"
    echo "   → Then reload: sudo udevadm control --reload-rules && sudo udevadm trigger"
fi
echo ""

# Try to enumerate RealSense devices
echo "5. Enumerating RealSense devices..."
if command -v rs-enumerate-devices &> /dev/null; then
    rs-enumerate-devices 2>&1 | head -n 50
else
    echo "   ⚠ rs-enumerate-devices not available"
    echo "   Install RealSense SDK: sudo apt install librealsense2-utils librealsense2-dev"
fi
echo ""

# Check ROS 2 RealSense package
echo "6. Checking ROS 2 RealSense package..."
if command -v ros2 &> /dev/null; then
    if ros2 pkg list | grep -q "realsense2_camera"; then
        echo "   ✓ realsense2_camera package found"
    else
        echo "   ✗ realsense2_camera package NOT found"
    fi
else
    echo "   ⚠ ROS 2 not sourced or not available"
fi
echo ""

echo "========================================="
echo "Diagnostic complete!"
echo "========================================="
