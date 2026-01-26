# Raspberry Pi - Data Collection & Camera Control

This folder contains all Raspberry Pi code for the thesis project's MQTT-based data collection system.

## 🎯 What's Inside

### Main System Files
- **`data_collector.py`** - Main service that receives MQTT data and controls camera
- **`thesis-data-collector.service`** - Systemd service for auto-start
- **`setup_system.sh`** - Complete installation script
- **`setup_autologin.sh`** - Enable auto-login on boot

### Documentation
- **`QUICK_START.md`** - 10-minute setup guide ⚡
- **`MQTT_SETUP_GUIDE.md`** - Complete documentation 📖
- **`FIRST_TIME_SETUP.md`** - Initial Pi setup
- **`SSH_SETUP.md`** - SSH configuration
- **`RUN_TESTS.md`** - Hardware testing guide

### Test Scripts
- **`camera_test.py`** - Test Camera Module 3
- **`camera_test.sh`** - Shell-based camera test
- **`led_test.py`** - Test GPIO LED control
- **`Connect-RaspberryPi.ps1`** - Windows connection helper

## 🚀 Quick Start

### 1. Run Setup Script
```bash
cd ~/Thesis-Edge-AI/RaspberryPi
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

## 📊 System Features

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
- ✅ Logging for debugging

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
│   ├── capture_20260126_121500.jpg
│   └── ...
└── data_collector.log
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
python3 camera_test.py
python3 led_test.py
```

## 🌐 MQTT Topics

The system listens to:
- `sensors/master/data` - Master node data
- `sensors/node1/data` - Node 1 data  
- `sensors/node2/data` - Node 2 data

Add more nodes by subscribing to additional topics in `data_collector.py`.

## 📈 CSV Data Format

Each CSV contains:
```csv
timestamp,temperature,humidity,tvoc,eco2,mq3_ppm
2026-01-26 12:00:00,22.5,45.2,150,400,0.5
2026-01-26 12:15:00,22.7,44.8,155,410,0.6
```

## 🔍 Troubleshooting

**Service won't start?**
```bash
journalctl -u thesis-data-collector -n 50
```

**No MQTT messages?**
```bash
sudo systemctl status mosquitto
```

**Camera not working?**
```bash
python3 camera_test.py
```

**LED not working?**
```bash
python3 led_test.py
```

See **MQTT_SETUP_GUIDE.md** for detailed troubleshooting.

## 📚 Related Documentation

- See `../ESP32/src/Node_MQTT.cpp` for ESP32 MQTT client code
- See `../ESP32/platformio.ini` for ESP32 build configuration

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

## 📫 Getting Started

**New to this project?** Start here:
1. Read [QUICK_START.md](QUICK_START.md) for rapid setup
2. Review [MQTT_SETUP_GUIDE.md](MQTT_SETUP_GUIDE.md) for complete details
3. Test hardware with [RUN_TESTS.md](RUN_TESTS.md)
