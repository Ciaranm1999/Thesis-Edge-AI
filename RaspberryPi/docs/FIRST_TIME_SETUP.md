# First Time SSH Connection - Setup Commands

## Run these commands once you're connected to the Pi

### 1. Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Required Packages
```bash
# Install Python GPIO library
sudo apt install -y python3-rpi.gpio python3-pip

# Install camera libraries (picamera2 is pre-installed on latest Raspberry Pi OS)
sudo apt install -y python3-picamera2

# Install other useful tools
sudo apt install -y git vim
```

### 3. Enable Camera
```bash
sudo raspi-config
# Navigate to: Interface Options -> Camera -> Enable
# Then reboot: sudo reboot
```

### 4. Test Camera (after reboot)
```bash
# List cameras
libcamera-hello --list-cameras

# 5 second preview test
libcamera-hello -t 5000

# Capture test image
libcamera-still -o test.jpg
```

### 5. Upload Test Scripts to Pi
On your **Windows PC**, run:
```powershell
cd "c:\Users\cmahe\OneDrive\Desktop\SSE Masters\Block 3\Smart Systems Project\Thesis-Edge-AI\RaspberryPi"

# Copy camera test scripts
scp camera_test.sh edge@192.168.2.84:~/
scp camera_test.py edge@192.168.2.84:~/

# Copy LED test script
scp led_test.py edge@192.168.2.84:~/
```

### 6. Run Tests on Pi
Back on the **Raspberry Pi SSH session**:

```bash
# Make scripts executable
chmod +x camera_test.sh

# Test camera with bash script
./camera_test.sh

# Test camera with Python
python3 camera_test.py

# Test LED (requires LED connected to GPIO17)
python3 led_test.py
```

### 7. View Results
Download captured images to your PC:
```powershell
# On Windows PC
scp edge@192.168.2.84:~/camera_tests/*.jpg .
```

## LED Wiring for Test
```
Raspberry Pi GPIO17 (Pin 11)
    |
    ├── 220Ω Resistor
    |
    ├── LED Anode (+, longer leg)
    |
    ├── LED Cathode (-, shorter leg)
    |
    └── GND (Pin 6, 9, 14, 20, 25, 30, 34, or 39)
```

## Troubleshooting

### Camera not detected
```bash
# Check if camera interface is enabled
vcgencmd get_camera

# Should show: supported=1 detected=1

# If not, enable camera and reboot
sudo raspi-config
```

### Permission errors with GPIO
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Reboot for changes to take effect
sudo reboot
```

### Python package issues
```bash
# Update pip
pip3 install --upgrade pip

# Reinstall packages
pip3 install --upgrade picamera2 RPi.GPIO
```
