# How to Hardcode USB Port ID for RealSense L515

## Why Hardcode?
Hardcoding the USB port ensures:
- ✓ Camera always connects to the same physical USB port
- ✓ Faster detection (no auto-discovery needed)
- ✓ More reliable in production environments
- ✓ Prevents conflicts if multiple cameras are present

## Step-by-Step Instructions

### Step 1: Find Your USB Port ID

On the robot, run:
```bash
cd ~/steve_ros2_ws/src/steve_hardware_bringup
bash scripts/get_camera_usb_port.sh
```

**Example output:**
```
=========================================
USB Port ID: 2-3.4
=========================================
```

Copy the USB Port ID (e.g., `2-3.4`)

### Step 2: Edit the Launch File

Open `pan_tilt.launch.py` and find line 44:

**Before:**
```python
declare_usb_port_cmd = DeclareLaunchArgument(
    'usb_port_id',
    default_value="''",  # ← Change this line
    description='USB port ID of the RealSense camera (leave empty to auto-detect)'
)
```

**After (replace `2-3.4` with YOUR actual USB port ID):**
```python
declare_usb_port_cmd = DeclareLaunchArgument(
    'usb_port_id',
    default_value="'2-3.4'",  # ← Hardcoded USB port
    description='USB port ID of the RealSense camera (hardcoded to specific port)'
)
```

**Important:** Keep the single quotes inside the double quotes: `"'2-3.4'"`

### Step 3: Test

```bash
ros2 launch steve_hardware_bringup hardware_bringup.launch.py
```

The camera will now always use the hardcoded USB port.

## Alternative: Use Serial Number Instead

If you prefer to identify by serial number (more flexible if you change USB ports):

### Step 1: Get Serial Number
```bash
rs-enumerate-devices | grep "Serial Number"
```

**Example output:**
```
Serial Number: f0123456789
```

### Step 2: Edit Launch File (line 38)

**Change:**
```python
declare_serial_no_cmd = DeclareLaunchArgument(
    'camera_serial_no',
    default_value="'f0123456789'",  # ← Your serial number
    description='Serial number of the RealSense camera'
)
```

## Which Method to Use?

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **USB Port ID** | Fastest detection, ensures physical port | Must use same USB port | Fixed robot setup |
| **Serial Number** | Can change USB ports freely | Slightly slower detection | Development/testing |

## Verification

After hardcoding, verify it's working:

```bash
# Launch the camera
ros2 launch steve_hardware_bringup hardware_bringup.launch.py

# In another terminal, check topics
ros2 topic list | grep pan_tilt_camera

# Should see:
# /pan_tilt_camera/color/image_raw
# /pan_tilt_camera/depth/image_rect_raw
# etc.
```

## Troubleshooting

**If camera not detected after hardcoding:**
1. Verify the USB port ID is correct: `bash scripts/get_camera_usb_port.sh`
2. Make sure camera is plugged into the SAME physical USB port
3. Check for typos in the launch file (quotes are important!)
4. Try using serial number method instead

**To temporarily override hardcoded value:**
```bash
ros2 launch steve_hardware_bringup hardware_bringup.launch.py usb_port_id:="''"
```
