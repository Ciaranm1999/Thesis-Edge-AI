# 🎉 Raspberry Pi Setup Complete!

**Date:** February 7, 2026  
**Pi Username:** edgeai  
**Pi Password:** 1234  
**Pi IP:** 172.20.10.3 (via iPhone hotspot)

---

## ✅ What's Been Configured

### 1. **UART Communication** (ESP32 Master → Pi)
- ✅ UART enabled on GPIO14/15 (`/dev/ttyAMA0`)
- ✅ Serial console disabled (no interference with data)
- ✅ Baud rate: 115200
- ⚠️ **Changes applied after reboot**

**Wiring (when you connect ESP32):**
| ESP32 Master | → | Raspberry Pi |
|--------------|---|--------------|
| GPIO17 (TX2) | → | Pin 10 (GPIO15/RX) |
| GPIO16 (RX2) | → | Pin 8 (GPIO14/TX) |
| GND | → | Pin 6/9/14 (GND) |

### 2. **Camera Module 3**
- ✅ Detected: IMX708 (12MP, autofocus)
- ✅ Test image captured: `~/thesis_data/images/test_camera.jpg` (589KB)
- ✅ Ready for synchronized capture with sensor data

### 3. **Auto-Start Service**
- ✅ Service: `thesis-uart-collector`
- ✅ Enabled to run on boot
- ✅ Auto-restarts if crashes
- ✅ Logs to: `~/thesis_data/uart_data_collector.log`

### 4. **Data Storage**
- ✅ Sensor data: `~/thesis_data/sensor_data/unified_sensor_data.csv`
- ✅ Images: `~/thesis_data/images/`
- ✅ Logs: `~/thesis_data/uart_data_collector.log`

### 5. **Python Dependencies**
- ✅ pyserial (UART communication)
- ✅ picamera2 (Camera Module 3)
- ✅ RPi.GPIO (LED control on GPIO17)
- ✅ All scripts copied to `~/thesis/RaspberryPi/`

---

## 🔧 System Architecture

```
┌──────────────┐  ESP-NOW   ┌──────────────┐  ESP-NOW   ┌──────────────┐
│   Node 1     │◄──────────►│   Node 2     │◄──────────►│   Master     │
│   ESP32      │            │   ESP32      │            │   ESP32      │
│  (DHT22,     │            │  (DHT22,     │            │  (DHT22,     │
│   SGP30,     │            │   SGP30,     │            │   SGP30,     │
│   MQ3)       │            │   MQ3)       │            │   MQ3)       │
└──────────────┘            └──────────────┘            └──────┬───────┘
                                                               │
                                       UART (GPIO17→GPIO15, 115200 baud)
                                                               │
                                                               ▼
                                                    ┌──────────────────┐
                                                    │  Raspberry Pi 5  │
                                                    │  - Data Logger   │
                                                    │  - Camera        │
                                                    │  - Edge AI       │
                                                    └──────────────────┘
```

### How It Works:
1. **Every 15 minutes:** All 3 ESP32 nodes wake from deep sleep
2. **ESP-NOW:** Slave nodes send data wirelessly to Master
3. **UART:** Master aggregates all 3 nodes + sends via serial to Pi
4. **Pi receives:** Data saved to unified CSV (all 3 nodes in one file)
5. **Camera:** Pi captures synchronized image with LED indicator
6. **Deep sleep:** ESP32s sleep for power efficiency (~10µA)

---

## 🚀 Quick Commands

### SSH Connection
```powershell
# From your laptop
ssh edgeai@172.20.10.3
```

### Service Management
```bash
# Check service status
sudo systemctl status thesis-uart-collector

# View live logs
tail -f ~/thesis_data/uart_data_collector.log

# Restart service
sudo systemctl restart thesis-uart-collector

# Stop service
sudo systemctl stop thesis-uart-collector

# Start service
sudo systemctl start thesis-uart-collector
```

### Monitor UART Directly
```bash
# Raw UART output (for debugging)
cat /dev/ttyAMA0

# Or with timing
sudo minicom -D /dev/ttyAMA0 -b 115200
```

### Check Data
```bash
# View sensor data
cat ~/thesis_data/sensor_data/unified_sensor_data.csv

# View latest images
ls -lt ~/thesis_data/images/ | head

# Check disk usage
df -h ~/thesis_data/
```

### Camera Commands
```bash
# List cameras
rpicam-hello --list-cameras

# Capture test image
rpicam-still -o ~/test.jpg -t 2000

# Capture with autofocus
rpicam-still -o ~/test.jpg --autofocus-on-capture
```

---

## 📊 Data Format

**CSV Columns (unified_sensor_data.csv):**
```
timestamp,node_id,temperature_c,humidity_rh,tvoc_ppb,eco2_ppm,mq3_ppm,cycle_number
```

**Example:**
```csv
2026-02-07 23:00:15,master,22.5,45.3,150,450,0.123,1
2026-02-07 23:00:15,node1,21.8,48.1,145,440,0.110,1
2026-02-07 23:00:15,node2,22.1,46.7,148,445,0.115,1
2026-02-07 23:15:30,master,22.6,45.1,152,455,0.125,2
...
```

---

## ⚠️ Next Steps - When You Connect ESP32

1. **Wire ESP32 Master to Pi:**
   - ESP32 GPIO17 (TX) → Pi Pin 10
   - ESP32 GND → Pi Pin 6 (ground)

2. **Power on ESP32 Master:**
   - Service will automatically start receiving data
   - Check logs: `tail -f ~/thesis_data/uart_data_collector.log`

3. **Verify data flow:**
   ```bash
   # Should show new lines every 15 minutes
   tail -f ~/thesis_data/sensor_data/unified_sensor_data.csv
   ```

4. **Check images:**
   ```bash
   # Images captured every 30 minutes
   ls -lh ~/thesis_data/images/
   ```

---

## 🐛 Troubleshooting

### Service not receiving data
```bash
# Check UART device exists
ls -l /dev/ttyAMA0

# Test UART permissions
groups edgeai  # Should include 'dialout'

# Add to dialout group if needed
sudo usermod -a -G dialout edgeai
```

### Camera not working
```bash
# Check camera detection
rpicam-hello --list-cameras

# Check camera cable connection
vcgencmd get_camera
# Should show: supported=1 detected=1
```

### Service won't start
```bash
# Check service logs
journalctl -u thesis-uart-collector -n 50

# Check Python script directly
cd ~/thesis/RaspberryPi/scripts
python3 uart_data_collector.py
```

### Disk space issues
```bash
# Check available space
df -h ~/thesis_data/

# Clean old images (keep last 30 days)
find ~/thesis_data/images -type f -mtime +30 -delete
```

---

## 🔄 KPN Router WiFi Setup (For Permanent Connection)

**Current:** Using iPhone hotspot (temporary)  
**Future:** Once you get KPN working or USB WiFi adapter:

```bash
# Edit WiFi config
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf

# Add:
network={
    ssid="YOUR_KPN_NETWORK"
    psk="YOUR_PASSWORD"
    scan_ssid=1
    key_mgmt=WPA-PSK
}

# Restart networking
sudo wpa_cli -i wlan0 reconfigure
```

**Recommended:** Get a USB WiFi adapter (€10-15) to bypass Pi 5 + KPN router compatibility issues.

---

## 📈 System Performance

- **Power:** ESP32s: ~10µA in sleep, ~80mA active (15min cycle)
- **Data rate:** 1 reading every 15 minutes × 3 nodes = ~300 readings/day
- **Storage:** ~50KB CSV/day, ~20MB images/day
- **SD card:** 32GB = ~1600 days of operation

---

## ✅ What's Working RIGHT NOW

1. ✅ SSH connection from laptop
2. ✅ UART configured and ready for ESP32
3. ✅ Camera Module 3 tested and working
4. ✅ Auto-start service enabled
5. ✅ Data directories created
6. ✅ All scripts in place

**Status:** 🟢 **System Ready for ESP32 Connection!**

---

## 🎓 VS Code Remote Development (Optional)

Want to edit files on the Pi from VS Code?

1. Install **Remote - SSH** extension in VS Code
2. Press `F1` → **Remote-SSH: Connect to Host**
3. Enter: `edgeai@172.20.10.3`
4. Password: `1234`
5. Open folder: `/home/edgeai/thesis`

Now you can edit Python scripts directly on the Pi! 🚀

---

**Setup completed by:** GitHub Copilot  
**Questions?** Check logs or restart the service!
