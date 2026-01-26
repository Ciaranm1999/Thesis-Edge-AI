# MQTT Data Collection System Setup Guide

This guide explains how to set up the complete MQTT-based data collection system with ESP32 nodes and Raspberry Pi.

## System Architecture

```
ESP32 Nodes (Multiple)
    ↓ WiFi + MQTT
Raspberry Pi (MQTT Broker)
    ├── Receives sensor data
    ├── Saves to CSV files
    └── Captures images every 15 min (with LED)
```

## Features

- ✅ ESP32 nodes wake every 15 minutes, send data via MQTT, then deep sleep
- ✅ Raspberry Pi continuously listens for data and saves to CSV
- ✅ Camera captures images with LED every 15 minutes (independent of data reception)
- ✅ Auto-starts on boot (systemd service)
- ✅ Auto-login enabled for hands-free operation

---

## Part 1: Raspberry Pi Setup

### Step 1: Copy Files to Raspberry Pi

From your Windows machine, copy the RaspberryPi folder to the Pi:

```powershell
# From your Windows PC
scp -r "C:\Users\cmahe\OneDrive\Desktop\SSE Masters\Thesis\Code\Thesis-Edge-AI\RaspberryPi" edgeai@192.168.2.84:~/Thesis-Edge-AI/
```

### Step 2: Run Setup Script on Pi

SSH into your Raspberry Pi and run:

```bash
cd ~/Thesis-Edge-AI/RaspberryPi
chmod +x setup_system.sh
./setup_system.sh
```

This script will:
- Install Mosquitto MQTT broker
- Install Python dependencies (paho-mqtt, picamera2)
- Create data directories
- Install and enable systemd service

### Step 3: Enable Auto-Login

To make the Pi start automatically without login:

```bash
cd ~/Thesis-Edge-AI/RaspberryPi
chmod +x setup_autologin.sh
./setup_autologin.sh
```

Then reboot:
```bash
sudo reboot
```

### Step 4: Start the Data Collector Service

After reboot (or manually):

```bash
# Start the service
sudo systemctl start thesis-data-collector

# Check status
sudo systemctl status thesis-data-collector

# View live logs
journalctl -u thesis-data-collector -f
```

---

## Part 2: ESP32 Setup

### Step 1: Install Required Libraries

In PlatformIO, add to `platformio.ini`:

```ini
lib_deps = 
    adafruit/Adafruit Unified Sensor@^1.1.6
    adafruit/DHT sensor library@^1.4.4
    adafruit/Adafruit SGP30 Sensor@^2.0.0
    knolleary/PubSubClient@^2.8
    bblanchon/ArduinoJson@^6.21.3
```

### Step 2: Configure WiFi and MQTT Settings

Edit `ESP32/src/Node_MQTT.cpp`:

```cpp
// WiFi Configuration
const char* WIFI_SSID = "YOUR_WIFI_NAME";      // <-- CHANGE THIS
const char* WIFI_PASSWORD = "YOUR_WIFI_PASS";  // <-- CHANGE THIS

// MQTT Configuration
const char* MQTT_BROKER = "192.168.2.84";      // <-- Your Pi's IP address
const int   MQTT_PORT = 1883;
const char* MQTT_TOPIC = "sensors/node1/data"; // node1, node2, master, etc.
```

### Step 3: Update platformio.ini

Create a new environment for MQTT mode in `ESP32/platformio.ini`:

```ini
[env:esp32_mqtt]
platform = espressif32
board = esp32dev
framework = arduino
monitor_speed = 115200
build_src_filter = +<Node_MQTT.cpp>
lib_deps = 
    adafruit/Adafruit Unified Sensor@^1.1.6
    adafruit/DHT sensor library@^1.4.4
    adafruit/Adafruit SGP30 Sensor@^2.0.0
    knolleary/PubSubClient@^2.8
    bblanchon/ArduinoJson@^6.21.3
```

### Step 4: Upload to ESP32

```bash
pio run -e esp32_mqtt --target upload
pio device monitor
```

### Step 5: Configure Multiple Nodes

For each additional node:
1. Change `MQTT_TOPIC` to unique value: `"sensors/node2/data"`, etc.
2. Upload to that ESP32
3. Each node will send data to its own topic

---

## Part 3: System Operation

### Data Collection

**ESP32 Nodes:**
- Wake every 15 minutes
- Read sensors (DHT22, SGP30, MQ3)
- Connect to WiFi
- Publish JSON data to MQTT
- Deep sleep until next cycle

**Raspberry Pi:**
- Mosquitto broker receives MQTT messages
- Python script saves data to CSV files
- Independent timer triggers camera + LED every 15 minutes
- Everything runs automatically on boot

### Data Storage

Data is saved to:
```
~/thesis_data/
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

### CSV Format

Each CSV file contains:
```csv
timestamp,temperature,humidity,tvoc,eco2,mq3_ppm
2026-01-26 12:00:00,22.5,45.2,150,400,0.5
2026-01-26 12:15:00,22.7,44.8,155,410,0.6
```

---

## Part 4: Testing & Verification

### Test MQTT Broker

On the Raspberry Pi:

```bash
# Subscribe to all sensor topics
mosquitto_sub -h localhost -t "sensors/#" -v

# You should see messages like:
# sensors/node1/data {"temp":22.5,"hum":45.2,"tvoc":150,"eco2":400,"mq3_ppm":0.5}
```

### Test Manual Publish

```bash
# Manually publish test data
mosquitto_pub -h localhost -t "sensors/test/data" -m '{"temp":25.0,"hum":50.0,"tvoc":100,"eco2":400,"mq3_ppm":0.3}'
```

### Check Logs

```bash
# Service logs
journalctl -u thesis-data-collector -f

# Application log file
tail -f ~/thesis_data/data_collector.log

# MQTT broker logs
sudo journalctl -u mosquitto -f
```

### Verify Data Files

```bash
# List sensor data files
ls -lh ~/thesis_data/sensor_data/

# View latest data
tail ~/thesis_data/sensor_data/node1_*.csv

# List captured images
ls -lh ~/thesis_data/images/
```

---

## Part 5: Troubleshooting

### ESP32 Won't Connect to WiFi

- Check SSID and password in code
- Verify ESP32 is in range of WiFi
- Check serial monitor for error messages
- Ensure WiFi is 2.4GHz (ESP32 doesn't support 5GHz)

### ESP32 Can't Connect to MQTT

- Verify Raspberry Pi IP address
- Check Mosquitto is running: `sudo systemctl status mosquitto`
- Test from PC: `mosquitto_pub -h 192.168.2.84 -t test -m "hello"`
- Check firewall on Pi (usually not an issue)

### Camera Not Working

- Check camera ribbon cable connection
- Verify camera is enabled: `vcgencmd get_camera`
- Check logs: `journalctl -u thesis-data-collector -f`
- Test manually: `cd ~/Thesis-Edge-AI/RaspberryPi && python3 camera_test.py`

### LED Not Working

- Check GPIO17 connection
- Verify LED polarity (longer leg is +)
- Check resistor (220Ω recommended)
- Test manually: `python3 ~/Thesis-Edge-AI/RaspberryPi/led_test.py`

### Service Won't Start

```bash
# Check service status
sudo systemctl status thesis-data-collector

# Check for errors
journalctl -u thesis-data-collector -n 50

# Restart service
sudo systemctl restart thesis-data-collector
```

### No Data Being Saved

- Check MQTT messages are arriving: `mosquitto_sub -h localhost -t "sensors/#" -v`
- Verify directory permissions: `ls -la ~/thesis_data/`
- Check Python script logs: `tail -f ~/thesis_data/data_collector.log`

---

## Part 6: Useful Commands

### Service Management

```bash
# Start service
sudo systemctl start thesis-data-collector

# Stop service
sudo systemctl stop thesis-data-collector

# Restart service
sudo systemctl restart thesis-data-collector

# Check status
sudo systemctl status thesis-data-collector

# Enable auto-start on boot
sudo systemctl enable thesis-data-collector

# Disable auto-start
sudo systemctl disable thesis-data-collector
```

### View Logs

```bash
# Live service logs
journalctl -u thesis-data-collector -f

# Last 100 lines
journalctl -u thesis-data-collector -n 100

# Application log
tail -f ~/thesis_data/data_collector.log

# MQTT broker logs
sudo journalctl -u mosquitto -f
```

### MQTT Testing

```bash
# Subscribe to all topics
mosquitto_sub -h localhost -t "#" -v

# Subscribe to sensor topics only
mosquitto_sub -h localhost -t "sensors/#" -v

# Publish test message
mosquitto_pub -h localhost -t "sensors/test/data" -m '{"temp":25.0}'
```

---

## Part 7: Power Consumption Estimates

### ESP32 Node (per 15-minute cycle)
- Deep sleep: ~10μA × 900s = 2.5mAh
- Active (WiFi + sensors): ~150mA × 10s = 0.4mAh
- **Total per cycle: ~3mAh**
- **Daily consumption: ~300mAh**
- **Battery life (2000mAh): ~6-7 days**

### Raspberry Pi
- Idle with services: ~2.5-3W continuous
- Camera capture: +0.5W for ~1s every 15min
- **Daily consumption: ~60-75Wh**
- Must be powered continuously

---

## Part 8: Future Improvements

### BLE Branch (Ultra-Low Power)
- Replace WiFi with BLE
- Reduce ESP32 power to ~30mAh/day
- Extend battery life to months

### UART Branch (Lowest Power)
- Direct serial connection
- Reduce ESP32 power to ~5mAh/day
- Battery life of years

### Edge AI Integration
- Add TensorFlow Lite models on Pi
- Real-time anomaly detection
- Smart triggering of camera based on sensor thresholds

---

## Support

For issues or questions:
1. Check logs first
2. Verify hardware connections
3. Test components individually
4. Review this documentation

**Happy data collecting! 📊📸**
