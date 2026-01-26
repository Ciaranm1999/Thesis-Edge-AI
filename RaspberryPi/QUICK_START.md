# Quick Start Guide - MQTT Data Collection System

## 🚀 Quick Setup (10 minutes)

### On Raspberry Pi:
```bash
# 1. Copy files and run setup
cd ~/Thesis-Edge-AI/RaspberryPi
chmod +x setup_system.sh setup_autologin.sh
./setup_system.sh

# 2. Enable auto-login
./setup_autologin.sh

# 3. Reboot
sudo reboot
```

### On ESP32:
```cpp
// Edit ESP32/src/Node_MQTT.cpp:
const char* WIFI_SSID = "YOUR_WIFI";
const char* WIFI_PASSWORD = "YOUR_PASSWORD";
const char* MQTT_BROKER = "192.168.2.84";  // Pi's IP
const char* MQTT_TOPIC = "sensors/node1/data";
```

```bash
# Upload to ESP32
pio run -e node_mqtt --target upload
```

---

## 📊 What Happens?

1. **ESP32 wakes every 15 minutes**
   - Reads all sensors
   - Connects to WiFi
   - Publishes JSON to MQTT
   - Goes back to deep sleep

2. **Raspberry Pi runs continuously**
   - Receives MQTT messages
   - Saves to CSV files
   - Takes camera photo every 15 minutes (with LED)
   - Auto-starts on boot

---

## 🔍 Quick Checks

### Check if MQTT broker is running:
```bash
sudo systemctl status mosquitto
```

### Check if data collector is running:
```bash
sudo systemctl status thesis-data-collector
```

### Watch for incoming data:
```bash
mosquitto_sub -h localhost -t "sensors/#" -v
```

### View logs:
```bash
journalctl -u thesis-data-collector -f
```

### Check collected data:
```bash
ls -lh ~/thesis_data/sensor_data/
tail ~/thesis_data/sensor_data/node1_*.csv
```

---

## 🎯 Key Features

✅ **Independent Scheduling**: Camera/LED runs every 15 min regardless of ESP32 data  
✅ **Auto-Start**: Everything starts automatically on Pi boot  
✅ **Auto-Login**: No manual login needed  
✅ **Low Power**: ESP32 sleeps 99% of the time  
✅ **Scalable**: Add more nodes by changing MQTT topic  

---

## 📁 Data Location

```
~/thesis_data/
├── sensor_data/
│   ├── node1_20260126.csv
│   ├── node2_20260126.csv
│   └── master_20260126.csv
├── images/
│   ├── capture_20260126_120000.jpg
│   └── ...
└── data_collector.log
```

---

## 🔧 Common Commands

```bash
# Restart service
sudo systemctl restart thesis-data-collector

# View live logs
journalctl -u thesis-data-collector -f

# Test MQTT
mosquitto_sub -h localhost -t "sensors/#" -v

# Check camera
python3 ~/Thesis-Edge-AI/RaspberryPi/camera_test.py

# Check LED
python3 ~/Thesis-Edge-AI/RaspberryPi/led_test.py
```

---

## ⚡ Power Consumption

| Component | Power | Battery Life (2000mAh) |
|-----------|-------|------------------------|
| ESP32 (MQTT) | ~300mAh/day | ~6-7 days |
| Raspberry Pi | ~3W continuous | Must be plugged in |

---

## 🎓 For Your Thesis

**Key Points:**
- ESP32 uses WiFi+MQTT for flexibility
- Independent camera scheduling ensures data collection continues
- System runs autonomously after initial setup
- Future branches can implement BLE or UART for even lower power

**Next Steps:**
- Collect baseline data for 24-48 hours
- Implement edge AI models for anomaly detection
- Create BLE/UART branch for ultra-low power comparison

---

See **MQTT_SETUP_GUIDE.md** for complete documentation.
