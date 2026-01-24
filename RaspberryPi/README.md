# Raspberry Pi - Camera Module 3 & Edge AI

This directory contains code and setup instructions for the Raspberry Pi component of the Thesis Edge AI project.

## Hardware
- **Raspberry Pi** (Model 3/4/5)
- **Camera Module 3** (12MP, autofocus)
- **LEDs** for status indication

## Quick Start

### 1. SSH Setup
See [SSH_SETUP.md](SSH_SETUP.md) for detailed instructions on:
- Enabling SSH on Raspberry Pi
- Finding Pi's IP address
- Connecting from Windows
- Setting up SSH keys

### 2. Quick Connect
Use the PowerShell script:
```powershell
.\Connect-RaspberryPi.ps1
```

Or manually:
```powershell
ssh pi@<RASPBERRY_PI_IP>
# Default password: raspberry
```

## Project Structure
```
RaspberryPi/
├── SSH_SETUP.md              # SSH setup guide
├── Connect-RaspberryPi.ps1   # Connection helper script
├── camera/                   # Camera module scripts
├── led_test/                 # LED test code
└── README.md                 # This file
```

## Next Steps
1. ✅ Set up SSH connection
2. ⬜ Test camera module 3
3. ⬜ Test LED control
4. ⬜ Integrate with Edge AI model
5. ⬜ Connect with ESP32 sensor network

## Useful Commands

### System Information
```bash
# Check Raspberry Pi model
cat /proc/cpuinfo | grep Model

# Check OS version
cat /etc/os-release

# Check available storage
df -h

# Check memory
free -h
```

### Camera Commands
```bash
# List camera devices
libcamera-hello --list-cameras

# Test camera (5 second preview)
libcamera-hello -t 5000

# Capture still image
libcamera-still -o test.jpg
```

### GPIO/LED Commands
```bash
# Install GPIO library
sudo apt install python3-rpi.gpio

# Test GPIO
pinout
```

## Troubleshooting

### Cannot SSH
- Check Pi is powered on and connected to network
- Verify SSH is enabled (create `ssh` file in boot partition)
- Confirm IP address with router or monitor

### Camera Not Detected
- Check ribbon cable connection
- Enable camera in raspi-config
- Update firmware: `sudo apt update && sudo apt upgrade`

### GPIO/LED Issues
- Check wiring and resistors
- Verify GPIO pin numbers (BCM vs BOARD numbering)
- Ensure Python GPIO library is installed

---

**Status:** 🟡 SSH Setup in Progress
