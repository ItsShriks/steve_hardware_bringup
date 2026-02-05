#!/bin/bash
# Get RealSense L515 USB Port ID for hardcoding in launch files

echo "========================================="
echo "RealSense L515 USB Port Identifier"
echo "========================================="
echo ""

# Find the L515 device
DEVICE_INFO=$(lsusb | grep "8086:0b64")

if [ -z "$DEVICE_INFO" ]; then
    echo "❌ L515 camera not found on USB bus"
    echo "   Make sure the camera is plugged in"
    exit 1
fi

echo "✓ Found L515 camera:"
echo "  $DEVICE_INFO"
echo ""

# Extract bus and device numbers
BUS=$(echo "$DEVICE_INFO" | awk '{print $2}')
DEV=$(echo "$DEVICE_INFO" | awk '{print substr($4,1,3)}')

echo "USB Location:"
echo "  Bus: $BUS"
echo "  Device: $DEV"
echo ""

# Get the USB port ID using udevadm
DEVICE_PATH="/dev/bus/usb/$BUS/$DEV"
USB_PORT_ID=$(udevadm info --query=property --name="$DEVICE_PATH" | grep "ID_PATH=" | cut -d'=' -f2 | grep -oP 'usb-\K[^:]+')

if [ -z "$USB_PORT_ID" ]; then
    # Alternative method using sysfs
    USB_PORT_ID=$(udevadm info --query=path --name="$DEVICE_PATH" | grep -oP '\d+-\d+(\.\d+)*$')
fi

echo "========================================="
echo "USB Port ID: $USB_PORT_ID"
echo "========================================="
echo ""

echo "To hardcode this in your launch file, add this parameter:"
echo ""
echo "  usb_port_id='$USB_PORT_ID'"
echo ""
echo "Example launch command:"
echo "  ros2 launch steve_hardware_bringup hardware_bringup.launch.py \\"
echo "    usb_port_id:='$USB_PORT_ID'"
echo ""
echo "Or edit pan_tilt.launch.py to set the default value."
echo ""
