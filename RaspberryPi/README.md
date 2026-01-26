# Raspberry Pi - Camera Module 3 & Edge AI

This directory contains code and setup instructions for the Raspberry Pi component of the Thesis Edge AI project.

## 📁 Project Structure

```
RaspberryPi/
├── scripts/              # Main scripts and utilities
│   ├── data_collector.py       # Main MQTT data collection service
│   ├── setup_system.sh         # System setup script
│   ├── setup_autologin.sh      # Auto-login configuration
│   └── Connect-RaspberryPi.ps1 # Windows connection helper
├── tests/                # Hardware test scripts
│   ├── camera_test.py          # Camera Module 3 test
│   ├── camera_test.sh          # Shell-based camera test
│   └── led_test.py             # GPIO LED test
├── services/             # Systemd service files
│   └── thesis-data-collector.service
├── docs/                 # Documentation
│   ├── QUICK_START.md          # 10-minute setup guide ⚡
│   ├── MQTT_SETUP_GUIDE.md     # Complete documentation 📖
│   ├── README_MQTT.md          # MQTT system overview
│   ├── FIRST_TIME_SETUP.md     # Initial Pi setup
│   ├── SSH_SETUP.md            # SSH configuration
│   └── RUN_TESTS.md            # Hardware testing guide
├── config/               # Configuration files
│   └── pyrightconfig.json      # Python type checking config
└── camera_images/        # Test image output directory

```

## Hardware
- **Raspberry Pi** (Model 3/4/5)
- **Camera Module 3** (12MP, autofocus)
- **LEDs** for status indication

## 🚀 Quick Start

### 1. Run Setup Script
```bash
cd ~/Thesis-Edge-AI/RaspberryPi/scripts
chmod +x setup_system.sh
./setup_system.sh
```

### 2. Enable Auto-Login
```bash
chmod +x setup_autologin.sh
./setup_autologin.sh
sudo reboot
```

### 3. Verify Everything Works
```bash
# Check service
sudo systemctl status thesis-data-collector

# Watch for MQTT messages
mosquitto_sub -h localhost -t "sensors/#" -v

# Check collected data
ls -lh ~/thesis_data/
```

## 🔧 Common Commands

```bash
# Service management
sudo systemctl start thesis-data-collector
sudo systemctl stop thesis-data-collector
sudo systemctl restart thesis-data-collector
sudo systemctl status thesis-data-collector

# View logs
journalctl -u thesis-data-collector -f
tail -f ~/thesis_data/data_collector.log

# Test MQTT
mosquitto_sub -h localhost -t "sensors/#" -v

# Test hardware
cd ~/Thesis-Edge-AI/RaspberryPi/tests
python3 camera_test.py
python3 led_test.py
```

## 📚 Documentation

For detailed setup and usage instructions, see:
- **[docs/QUICK_START.md](docs/QUICK_START.md)** - Fast setup guide
- **[docs/MQTT_SETUP_GUIDE.md](docs/MQTT_SETUP_GUIDE.md)** - Complete system documentation
- **[docs/README_MQTT.md](docs/README_MQTT.md)** - MQTT system overview
- **[docs/RUN_TESTS.md](docs/RUN_TESTS.md)** - Hardware testing procedures

## 🎯 System Features

### Data Collection
- ✅ Receives sensor data from ESP32 nodes via MQTT
- ✅ Saves data to daily CSV files
- ✅ Separate file for each node (master, node1, node2)
- ✅ Timestamped entries

### Camera Control
- ✅ Captures images every 15 minutes
- ✅ LED turns on during capture for consistent lighting
- ✅ Images saved with timestamps
- ✅ Runs independently of data reception

### Auto-Start
- ✅ Service starts automatically on boot
- ✅ Auto-login enabled for hands-free operation
- ✅ Reconnects to MQTT if connection lost
- ✅ Comprehensive logging for debugging

## 🌐 MQTT Topics

The system listens to:
- `sensors/master/data` - Master node data
- `sensors/node1/data` - Node 1 data  
- `sensors/node2/data` - Node 2 data

## 📁 Data Storage

All data saved to `~/thesis_data/`:
```
thesis_data/
├── sensor_data/
│   ├── master_20260126.csv
│   ├── node1_20260126.csv
│   └── node2_20260126.csv
├── images/
│   ├── capture_20260126_120000.jpg
│   └── ...
└── data_collector.log
```

## 🎓 For Thesis

This system demonstrates:
- Edge device communication protocols (MQTT)
- Autonomous data collection
- Power-efficient ESP32 operation (deep sleep)
- Multi-sensor data fusion
- Image capture for AI model training

Future branches will implement:
- BLE communication (ultra-low power)
- UART communication (lowest power)
- Edge AI inference on Raspberry Pi
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
