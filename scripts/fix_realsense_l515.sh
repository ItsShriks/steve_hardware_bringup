#!/bin/bash
# RealSense L515 Firmware Access Fix
# This script fixes the common issue where the L515 is detected via USB but SDK cannot communicate

echo "========================================="
echo "RealSense L515 Firmware Access Fix"
echo "========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "⚠ Please do NOT run this script as root"
    echo "Run it as your normal user, it will ask for sudo when needed"
    exit 1
fi

# 1. Ensure user is in plugdev group
echo "1. Checking user groups..."
if groups $USER | grep -q plugdev; then
    echo "   ✓ User is in plugdev group"
else
    echo "   Adding user to plugdev group..."
    sudo usermod -a -G plugdev $USER
    echo "   ⚠ You will need to LOG OUT and LOG BACK IN for group changes to take effect"
fi
echo ""

# 2. Reset USB device
echo "2. Resetting USB device..."
DEVICE_PATH=$(lsusb | grep "8086:0b64" | awk '{print "/dev/bus/usb/"$2"/"substr($4,1,3)}')
if [ -n "$DEVICE_PATH" ]; then
    echo "   Found device at: $DEVICE_PATH"
    # Unbind and rebind the device
    BUS=$(lsusb | grep "8086:0b64" | awk '{print $2}')
    DEV=$(lsusb | grep "8086:0b64" | awk '{print substr($4,1,3)}')
    
    # Use usbreset if available, otherwise use the bind/unbind method
    if command -v usbreset &> /dev/null; then
        sudo usbreset "$DEVICE_PATH"
        echo "   ✓ Device reset using usbreset"
    else
        echo "   Attempting manual USB reset..."
        # This is a softer approach
        echo "   Please unplug and replug the camera USB cable"
    fi
else
    echo "   ⚠ L515 device not found on USB bus"
fi
echo ""

# 3. Update udev rules specifically for L515
echo "3. Updating udev rules for L515..."
UDEV_RULE_FILE="/etc/udev/rules.d/99-realsense-libusb.rules"

# Check if the L515-specific rule exists
if sudo grep -q "0b64" "$UDEV_RULE_FILE" 2>/dev/null; then
    echo "   ✓ L515 rule already exists in udev"
else
    echo "   Adding L515-specific udev rule..."
    echo '# Intel RealSense L515' | sudo tee -a "$UDEV_RULE_FILE" > /dev/null
    echo 'SUBSYSTEMS=="usb", ATTRS{idVendor}=="8086", ATTRS{idProduct}=="0b64", MODE:="0666", GROUP:="plugdev"' | sudo tee -a "$UDEV_RULE_FILE" > /dev/null
    echo "   ✓ L515 rule added"
fi
echo ""

# 4. Reload udev rules
echo "4. Reloading udev rules..."
sudo udevadm control --reload-rules
sudo udevadm trigger
echo "   ✓ udev rules reloaded"
echo ""

# 5. Check for conflicting processes
echo "5. Checking for conflicting processes..."
CONFLICTING_PROCS=$(ps aux | grep -E "(realsense-viewer|rs-enumerate)" | grep -v grep)
if [ -n "$CONFLICTING_PROCS" ]; then
    echo "   ⚠ Found processes that might interfere:"
    echo "$CONFLICTING_PROCS"
    echo "   Consider killing these processes"
else
    echo "   ✓ No conflicting processes found"
fi
echo ""

# 6. Test device detection
echo "6. Testing device detection..."
sleep 2  # Give udev time to apply rules

if command -v rs-enumerate-devices &> /dev/null; then
    echo "   Running rs-enumerate-devices..."
    rs-enumerate-devices 2>&1 | head -n 20
else
    echo "   ⚠ rs-enumerate-devices not available"
fi
echo ""

echo "========================================="
echo "Fix Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. If you were added to plugdev group, LOG OUT and LOG BACK IN"
echo "2. Unplug and replug the camera USB cable"
echo "3. Run: rs-enumerate-devices"
echo "4. If still not working, try a different USB 3.0 port"
echo "5. Launch ROS 2 camera node: ros2 launch steve_hardware_bringup hardware_bringup.launch.py"
echo ""
