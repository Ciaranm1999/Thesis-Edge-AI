# Raspberry Pi OS Lite Setup Guide for MQTT System

This guide walks you through setting up a fresh Raspberry Pi OS Lite installation for the MQTT-based sensor data collection system.

## 📋 What You Need

- Raspberry Pi (Model 3/4/5)
- MicroSD card (16GB+)
- Camera Module 3
- WiFi network credentials
- Windows PC with SD card reader

---

## Part 1: Flash Raspberry Pi OS Lite

### Step 1: Download Raspberry Pi Imager
1. Download from: https://www.raspberrypi.com/software/
2. Install and open Raspberry Pi Imager

### Step 2: Configure and Flash
1. **Choose Device**: Select your Raspberry Pi model
2. **Choose OS**: 
   - Click "Raspberry Pi OS (other)"
   - Select **"Raspberry Pi OS Lite (64-bit)"** (no desktop)
3. **Choose Storage**: Select your SD card
4. **Configure Settings** (click gear icon or "Edit Settings"):
   - ✅ **Set hostname**: `raspberrypi` (or your choice)
   - ✅ **Enable SSH**: Use password authentication
   - ✅ **Set username**: `edgeai` (or your choice)
   - ✅ **Set password**: Choose a secure password
   - ✅ **Configure WiFi**:
     - SSID: Your WiFi network name
     - Password: Your WiFi password
     - Country: Your country code (e.g., NL)
   - ✅ **Set locale settings**: Your timezone and keyboard layout
5. Click **"Save"**
6. Click **"Write"** and wait for completion

### Step 3: First Boot
1. Insert SD card into Raspberry Pi
2. Connect power
3. Wait ~2 minutes for first boot and WiFi connection

---

## Part 2: Find Your Pi and Connect

### Step 1: Find IP Address

#### Option A: Check Router
- Log into your router admin page
- Look for device named "raspberrypi" or "edgeai"

#### Option B: Use Network Scanner
```powershell
# Install Advanced IP Scanner (free)
# Download: https://www.advanced-ip-scanner.com/
# Scan your network and look for Raspberry Pi
```

#### Option C: Use hostname (may not work on all networks)
```powershell
# Try connecting directly with hostname
ssh edgeai@raspberrypi.local
```

### Step 2: Connect via SSH
```powershell
# Replace with your Pi's actual IP address
ssh edgeai@192.168.1.XXX

# Enter your password when prompted
# First time: type "yes" to accept fingerprint
```

---

## Part 3: Initial Pi Setup

### Step 1: Update System
```bash
# This is important - don't skip!
sudo apt update && sudo apt upgrade -y

# This may take 5-10 minutes on first boot
```

### Step 2: Enable Camera Interface
```bash
# Open Raspberry Pi config
sudo raspi-config

# Navigate using arrow keys:
# 3. Interface Options
#    -> I1 Legacy Camera -> No (use new stack)
# Finish and reboot

sudo reboot
```

Wait 1 minute, then reconnect:
```powershell
ssh edgeai@192.168.1.XXX
```

### Step 3: Install Required Packages
```bash
# Install Python and camera libraries
sudo apt install -y python3-pip python3-picamera2 python3-rpi.gpio

# Install Git
sudo apt install -y git

# Install Mosquitto MQTT broker
sudo apt install -y mosquitto mosquitto-clients

# Enable and start Mosquitto
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

### Step 4: Verify Camera
```bash
# List connected cameras
libcamera-hello --list-cameras

# Should show: Available cameras:
# 0 : imx708 [4608x2592] (/base/soc/i2c0mux/i2c@1/imx708@1a)

# Quick 5-second preview test (if you have display connected)
# libcamera-hello -t 5000

# Capture test image
libcamera-still -o ~/test.jpg
```

---

## Part 4: Deploy Your Code

### Step 1: Copy Files from Windows PC
```powershell
# From your Windows PC PowerShell:
cd "C:\Users\cmahe\OneDrive\Desktop\SSE Masters\Thesis\Code\Thesis-Edge-AI"

# Copy entire RaspberryPi folder to Pi
scp -r RaspberryPi edgeai@192.168.1.XXX:~/Thesis-Edge-AI/
```

### Step 2: Run Setup Script
Back in your SSH session on the Pi:

```bash
cd ~/Thesis-Edge-AI/RaspberryPi/scripts

# Make script executable
chmod +x setup_system.sh

# Run setup (installs dependencies, creates directories, installs service)
./setup_system.sh
```

This script will:
- ✅ Install Python MQTT library (paho-mqtt)
- ✅ Create data directories (`~/thesis_data/`)
- ✅ Install systemd service for auto-start
- ✅ Enable service to start on boot

### Step 3: Enable Auto-Login (Optional but Recommended)
```bash
cd ~/Thesis-Edge-AI/RaspberryPi/scripts
chmod +x setup_autologin.sh
./setup_autologin.sh

# Reboot to apply
sudo reboot
```

---

## Part 5: Start the System

After reboot (wait 1 min), reconnect:
```powershell
ssh edgeai@192.168.1.XXX
```

### Check Service Status
```bash
# Check if service is running
sudo systemctl status thesis-data-collector

# Should show: Active: active (running)
```

### View Live Logs
```bash
# Watch logs in real-time
journalctl -u thesis-data-collector -f

# Or view log file
tail -f ~/thesis_data/data_collector.log
```

### Test MQTT Broker
```bash
# Subscribe to all sensor topics
mosquitto_sub -h localhost -t "sensors/#" -v

# You should see messages when ESP32s send data
```

---

## Part 6: Configure ESP32 Nodes

### Step 1: Update ESP32 Code
On your Windows PC, edit the ESP32 code:

**File:** `ESP32/src/Node_MQTT.cpp`

```cpp
// WiFi Configuration
const char* WIFI_SSID = "YOUR_WIFI_NAME";      // Your WiFi SSID
const char* WIFI_PASSWORD = "YOUR_WIFI_PASS";  // Your WiFi password

// MQTT Configuration
const char* MQTT_BROKER = "192.168.1.XXX";     // Your Pi's IP address
const int   MQTT_PORT = 1883;
const char* MQTT_TOPIC = "sensors/node1/data"; // node1, node2, master, etc.
```

### Step 2: Upload to ESP32
```powershell
# In VS Code terminal, in ESP32 folder
cd "C:\Users\cmahe\OneDrive\Desktop\SSE Masters\Thesis\Code\Thesis-Edge-AI\ESP32"

# Upload to ESP32
pio run -e esp32_mqtt --target upload

# Monitor serial output
pio device monitor
```

You should see:
```
Connecting to WiFi...
Connected to WiFi
Connected to MQTT broker
Reading sensors...
Data sent to MQTT
Entering deep sleep...
```

### Step 3: Verify Data Collection
On Raspberry Pi:
```bash
# Watch for incoming messages
mosquitto_sub -h localhost -t "sensors/#" -v

# Check saved data files
ls -lh ~/thesis_data/sensor_data/
cat ~/thesis_data/sensor_data/sensor_data_YYYY-MM-DD.csv
```

---

## 🎯 Verification Checklist

- [ ] SSH connection works
- [ ] Camera detected by `libcamera-hello --list-cameras`
- [ ] Mosquitto MQTT broker running: `sudo systemctl status mosquitto`
- [ ] Data collector service running: `sudo systemctl status thesis-data-collector`
- [ ] Can see MQTT messages: `mosquitto_sub -h localhost -t "sensors/#" -v`
- [ ] ESP32 connects and sends data
- [ ] CSV files created in `~/thesis_data/sensor_data/`
- [ ] Images captured in `~/thesis_data/images/`

---

## 🔧 Useful Commands

### Service Management
```bash
sudo systemctl start thesis-data-collector    # Start service
sudo systemctl stop thesis-data-collector     # Stop service
sudo systemctl restart thesis-data-collector  # Restart service
sudo systemctl status thesis-data-collector   # Check status
```

### View Logs
```bash
journalctl -u thesis-data-collector -f        # Live systemd logs
tail -f ~/thesis_data/data_collector.log      # Live application logs
cat ~/thesis_data/data_collector.log | grep ERROR  # Show errors
```

### MQTT Testing
```bash
# Subscribe to all sensor topics
mosquitto_sub -h localhost -t "sensors/#" -v

# Publish test message
mosquitto_pub -h localhost -t "sensors/test" -m "Hello MQTT"
```

### Check Disk Space
```bash
df -h                          # Overall disk usage
du -h ~/thesis_data/ | tail -1 # Data folder size
```

### Network Info
```bash
hostname -I                    # Show IP address
ip a                          # Detailed network info
ping google.com               # Test internet connection
```

---

## 🐛 Troubleshooting

### Camera Not Detected
```bash
# Check camera connection
vcgencmd get_camera

# Should show: supported=1 detected=1

# If not, check physical connection and reboot
sudo reboot
```

### Service Won't Start
```bash
# Check detailed error
journalctl -u thesis-data-collector -n 50

# Check Python dependencies
pip3 list | grep -i "paho\|picamera"

# Manually test the script
cd ~/Thesis-Edge-AI/RaspberryPi/scripts
python3 data_collector.py
```

### ESP32 Can't Connect to MQTT
1. Verify Pi's IP address: `hostname -I`
2. Check Mosquitto is running: `sudo systemctl status mosquitto`
3. Test from ESP32 network (ping from another device)
4. Check WiFi credentials in ESP32 code
5. Check firewall: `sudo ufw status` (should be inactive by default)

### No Data Being Saved
```bash
# Check if directory exists and is writable
ls -la ~/thesis_data/sensor_data/

# Check service logs
journalctl -u thesis-data-collector -f

# Test MQTT subscription
mosquitto_sub -h localhost -t "sensors/#" -v
```

---

## 📱 Accessing Data from Your Laptop

You have a web dashboard to view data remotely! See:
- [SETUP_AND_DATA_GUIDE.md](../SETUP_AND_DATA_GUIDE.md)

Or manually copy files:
```powershell
# From Windows PC
scp -r edgeai@192.168.1.XXX:~/thesis_data/ ./thesis_data_backup/
```

---

## 🔄 Future: Switching to Wired Connection

When you're ready to switch from MQTT to wired (UART/Serial) connection:
1. Connect ESP32 TX → Pi RX, ESP32 RX → Pi TX, GND → GND
2. Modify ESP32 code to send data over Serial instead of MQTT
3. Modify Pi code to read from `/dev/serial0` instead of MQTT
4. Update in `data_collector.py` (we can help with this when ready)

This will be more energy-efficient and reliable for your final system!

---

## 📚 Additional Documentation

- **Quick Start**: [QUICK_START.md](QUICK_START.md)
- **Complete MQTT Guide**: [MQTT_SETUP_GUIDE.md](MQTT_SETUP_GUIDE.md)
- **SSH Setup**: [SSH_SETUP.md](SSH_SETUP.md)
- **Hardware Tests**: [RUN_TESTS.md](RUN_TESTS.md)

---

## ✨ Summary

You now have:
1. ✅ Raspberry Pi OS Lite installed and configured
2. ✅ SSH access working
3. ✅ Camera enabled and tested
4. ✅ MQTT broker running
5. ✅ Data collection service auto-starting on boot
6. ✅ ESP32 nodes sending data every 15 minutes
7. ✅ All data saved to CSV files
8. ✅ Images captured every 15 minutes

Your system is ready to collect data 24/7! When you're ready to move to wired connection, we can help you modify the code.
