# System Setup & Data Storage Guide

## 📸 Photo Timestamps

**Yes!** Every photo is automatically timestamped with the exact date and time when captured.

**Format:** `capture_YYYYMMDD_HHMMSS.jpg`

**Examples:**
- `capture_20260126_143000.jpg` → January 26, 2026 at 2:30:00 PM
- `capture_20260126_144500.jpg` → January 26, 2026 at 2:45:00 PM
- `capture_20260126_150000.jpg` → January 26, 2026 at 3:00:00 PM

---

## 💾 Where is Data Saved?

All data is saved on the **Raspberry Pi** at:

```
~/thesis_data/
├── sensor_data/                          # CSV files with sensor readings
│   ├── master_20260126.csv              # Master node data (today)
│   ├── node1_20260126.csv               # Node 1 data (today)
│   ├── node2_20260126.csv               # Node 2 data (today)
│   ├── master_20260127.csv              # Tomorrow's files...
│   └── ...
│
├── images/                               # Camera captures
│   ├── capture_20260126_120000.jpg      # 12:00:00 PM
│   ├── capture_20260126_121500.jpg      # 12:15:00 PM
│   ├── capture_20260126_123000.jpg      # 12:30:00 PM
│   └── ...
│
└── data_collector.log                    # System logs
```

**Full Path:** `/home/edgeai/thesis_data/`

### CSV File Format

Each CSV contains timestamped sensor data:
```csv
timestamp,temperature,humidity,tvoc,eco2,mq3_ppm
2026-01-26 12:00:00,22.5,45.2,150,400,0.5
2026-01-26 12:15:00,22.7,44.8,155,410,0.6
2026-01-26 12:30:00,22.6,45.0,152,405,0.55
```

---

## 🚀 Complete Setup Guide - Step by Step

### **START HERE:**

#### **Step 1: Read the Quick Start** 📖
File: `RaspberryPi/docs/QUICK_START.md`

This gives you a 10-minute overview of the entire system.

---

#### **Step 2: Copy Files to Raspberry Pi** 📁

From your Windows PC:
```powershell
# Copy the entire RaspberryPi folder to your Pi
scp -r "C:\Users\cmahe\OneDrive\Desktop\SSE Masters\Thesis\Code\Thesis-Edge-AI\RaspberryPi" edgeai@192.168.2.84:~/Thesis-Edge-AI/
```

Or use Git on the Pi:
```bash
# SSH into your Pi first
ssh edgeai@192.168.2.84

# Clone or pull the repository
cd ~
git clone https://github.com/Ciaranm1999/Thesis-Edge-AI.git
# OR if already cloned:
cd ~/Thesis-Edge-AI
git checkout RaspPI
git pull origin RaspPI
```

---

#### **Step 3: Run Setup Script on Raspberry Pi** ⚙️

```bash
# SSH into your Pi
ssh edgeai@192.168.2.84

# Navigate to scripts folder
cd ~/Thesis-Edge-AI/RaspberryPi/scripts

# Make scripts executable
chmod +x setup_system.sh
chmod +x setup_autologin.sh

# Run the main setup (installs MQTT broker, Python libs, creates service)
./setup_system.sh
```

This script will:
- ✅ Install Mosquitto MQTT broker
- ✅ Install Python dependencies (paho-mqtt, picamera2)
- ✅ Create data directories
- ✅ Install systemd service for auto-start

---

#### **Step 4: Enable Auto-Login** 🔓

```bash
# Still on the Pi
./setup_autologin.sh

# Reboot to apply changes
sudo reboot
```

After reboot, the Pi will:
- Auto-login without password
- Auto-start the data collector service
- Start collecting data immediately

---

#### **Step 5: Configure ESP32** 🔧

File to edit: `ESP32/src/Node_MQTT.cpp`

**Change these lines:**
```cpp
// Line 11-12: Your WiFi credentials
const char* WIFI_SSID = "YOUR_WIFI_SSID";      // <-- CHANGE THIS
const char* WIFI_PASSWORD = "YOUR_WIFI_PASS";  // <-- CHANGE THIS

// Line 15: Your Raspberry Pi's IP address
const char* MQTT_BROKER = "192.168.2.84";      // <-- CHANGE TO YOUR PI'S IP

// Line 17: Node identifier (change for each ESP32)
const char* MQTT_TOPIC = "sensors/node1/data"; // node1, node2, master, etc.
```

**Upload to ESP32:**
```bash
# In PlatformIO terminal
pio run -e node_mqtt --target upload
pio device monitor
```

---

#### **Step 6: Verify Everything Works** ✅

**On Raspberry Pi:**

```bash
# Check if service is running
sudo systemctl status thesis-data-collector

# Watch for incoming MQTT messages
mosquitto_sub -h localhost -t "sensors/#" -v

# Check collected data
ls -lh ~/thesis_data/sensor_data/
ls -lh ~/thesis_data/images/

# View logs
tail -f ~/thesis_data/data_collector.log
```

---

### **END HERE:** 🎉

Once everything is running:
- ESP32 wakes every 15 minutes, sends data, goes back to sleep
- Raspberry Pi saves data to CSV files
- Camera takes photos every 15 minutes with LED on
- Everything auto-starts on boot

---

## 📚 Documentation Files & Order

Read in this order:

1. **`docs/QUICK_START.md`** ⚡
   - 10-minute overview
   - START HERE!

2. **`docs/MQTT_SETUP_GUIDE.md`** 📖
   - Complete detailed guide (8 parts)
   - Troubleshooting
   - Power consumption info

3. **`docs/README_MQTT.md`**
   - System architecture
   - How MQTT communication works

4. **`docs/RUN_TESTS.md`**
   - How to test camera
   - How to test LED
   - Hardware verification

5. **`MIGRATION_GUIDE.md`**
   - Only if you already set up the old version
   - How to update to new folder structure

---

## 🔍 Quick Reference Commands

```bash
# Service Management
sudo systemctl start thesis-data-collector      # Start service
sudo systemctl stop thesis-data-collector       # Stop service
sudo systemctl restart thesis-data-collector    # Restart service
sudo systemctl status thesis-data-collector     # Check status

# View Logs
journalctl -u thesis-data-collector -f          # Live service logs
tail -f ~/thesis_data/data_collector.log        # Live app logs

# Test Hardware
cd ~/Thesis-Edge-AI/RaspberryPi/tests
python3 camera_test.py                          # Test camera
python3 led_test.py                             # Test LED

# View Data
ls -lh ~/thesis_data/sensor_data/               # List CSV files
tail ~/thesis_data/sensor_data/node1_*.csv      # View latest data
ls -lh ~/thesis_data/images/                    # List images
```

---

## 📊 What Happens Once Running?

### Every 15 Minutes:

**ESP32:**
1. Wakes from deep sleep
2. Reads all sensors (DHT22, SGP30, MQ3)
3. Connects to WiFi (2-3 seconds)
4. Publishes JSON data to MQTT broker on Pi
5. Goes back to deep sleep

**Raspberry Pi:**
1. Receives MQTT message
2. Saves to CSV file: `~/thesis_data/sensor_data/node1_YYYYMMDD.csv`
3. Camera captures photo with LED on
4. Saves image: `~/thesis_data/images/capture_YYYYMMDD_HHMMSS.jpg`

---

## 🆘 Having Issues?

See `docs/MQTT_SETUP_GUIDE.md` → **Part 5: Troubleshooting**

Or check:
- Service logs: `journalctl -u thesis-data-collector -f`
- Application log: `tail -f ~/thesis_data/data_collector.log`
- MQTT broker: `sudo systemctl status mosquitto`

---

## 💻 Getting Data to Your Laptop

### Option 1: Manual Copy (Quick & Easy)

From your Windows laptop:
```powershell
# Copy all data to your Desktop
scp -r edgeai@192.168.2.84:~/thesis_data "C:\Users\cmahe\Desktop\"

# Or just sensor data
scp -r edgeai@192.168.2.84:~/thesis_data/sensor_data "C:\Users\cmahe\Desktop\"

# Or just images
scp -r edgeai@192.168.2.84:~/thesis_data/images "C:\Users\cmahe\Desktop\"
```

### Option 2: Auto-Sync Script (Recommended)

Use the PowerShell sync script:
```powershell
# From Windows - in your project folder
cd "C:\Users\cmahe\OneDrive\Desktop\SSE Masters\Thesis\Code\Thesis-Edge-AI\RaspberryPi\scripts"

# Run the sync script
.\Sync-ThesisData.ps1
```

This will:
- Copy all CSV files to `C:\Users\cmahe\Desktop\thesis_data\sensor_data\`
- Copy all images to `C:\Users\cmahe\Desktop\thesis_data\images\`
- Copy logs
- Show summary of downloaded files

### Option 3: Web Dashboard (View in Browser)

**On Raspberry Pi:**
```bash
# Install Flask (one time)
pip3 install flask pandas --break-system-packages

# Run the dashboard
cd ~/Thesis-Edge-AI/RaspberryPi/scripts
python3 web_dashboard.py
```

**On Your Laptop:**
Open browser and go to: `http://192.168.2.84:5000`

You can now:
- ✅ View latest sensor readings in a table
- ✅ Browse and download CSV files
- ✅ View recent images
- ✅ Auto-refreshes every minute

---

## 📊 Future Dashboard Ideas

Once you have more data, you could create:
- Real-time graphs with Plotly/Chart.js
- Anomaly detection alerts
- Historical trends analysis
- Export to Excel with Python openpyxl
- Power BI or Tableau integration

---

**That's it! Start with `docs/QUICK_START.md` and follow the steps above.** 🚀
