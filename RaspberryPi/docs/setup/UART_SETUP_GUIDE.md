# UART Connection Setup Guide

## Hardware Wiring

### Pin Connections

**ESP32 Master → Raspberry Pi:**

| ESP32 Pin | Function | → | Raspberry Pi Pin | Function |
|-----------|----------|---|------------------|----------|
| GPIO17    | TX2      | → | Pin 10 (GPIO15)  | RXD      |
| GPIO16    | RX2      | → | Pin 8 (GPIO14)   | TXD      |
| GND       | Ground   | → | Pin 6/9/14/etc   | GND      |

### Physical Layout
```
Raspberry Pi GPIO Header (facing pins):
    3V3  (1) (2)  5V
  GPIO2  (3) (4)  5V
  GPIO3  (5) (6)  GND  ← ESP32 GND
  GPIO4  (7) (8)  GPIO14 (TXD) ← ESP32 GPIO16 (RX2)
    GND  (9) (10) GPIO15 (RXD) ← ESP32 GPIO17 (TX2)
```

---

## Raspberry Pi Configuration

### 1. Disable Serial Console

The serial console must be disabled to use the UART for data communication.

**Edit cmdline.txt:**
```bash
sudo nano /boot/cmdline.txt
```

Remove any references to `console=serial0,115200` or `console=ttyAMA0,115200`.

**Example:**
- **Before:** `console=serial0,115200 console=tty1 root=...`
- **After:** `console=tty1 root=...`

**Save and exit** (Ctrl+X, Y, Enter)

### 2. Enable UART in config.txt

```bash
sudo nano /boot/config.txt
```

Add these lines at the bottom:
```
# Enable UART for ESP32 communication
enable_uart=1
dtoverlay=disable-bt
```

**Save and exit**

### 3. Disable Bluetooth Service (Pi 3/4 only)

```bash
sudo systemctl disable hciuart
```

### 4. Reboot

```bash
sudo reboot
```

### 5. Verify UART is Available

After reboot:
```bash
ls -l /dev/ttyAMA0
```

Should show:
```
crw-rw---- 1 root dialout ... /dev/ttyAMA0
```

Add your user to dialout group:
```bash
sudo usermod -a -G dialout $USER
```

Log out and back in for group changes to take effect.

---

## Data Collector Installation

### 1. Install Dependencies

```bash
sudo apt update
sudo apt install python3-serial python3-picamera2 python3-rpi.gpio
```

### 2. Test UART Connection

```bash
# Monitor incoming data
cat /dev/ttyAMA0
```

You should see JSON data arriving every 15 minutes (when ESP32 wakes up).

### 3. Install Data Collector Service

```bash
cd ~/Thesis-Edge-AI/RaspberryPi/scripts

# Test manually first
python3 uart_data_collector.py
```

**Expected Output:**
```
==============================================================
  Thesis UART Data Collection Service Starting
==============================================================
Data directory: /home/edgeai/thesis_data/sensor_data
Image directory: /home/edgeai/thesis_data/images
✓ Serial port opened successfully
Waiting for data from ESP32...
```

### 4. Create Systemd Service

Create service file:
```bash
sudo nano /etc/systemd/system/thesis-uart-collector.service
```

Paste this content:
```ini
[Unit]
Description=Thesis UART Data Collection Service
After=network.target

[Service]
Type=simple
User=edgeai
WorkingDirectory=/home/edgeai/Thesis-Edge-AI/RaspberryPi/scripts
ExecStart=/usr/bin/python3 /home/edgeai/Thesis-Edge-AI/RaspberryPi/scripts/uart_data_collector.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable thesis-uart-collector.service
sudo systemctl start thesis-uart-collector.service
```

**Check status:**
```bash
sudo systemctl status thesis-uart-collector.service
```

**View logs:**
```bash
sudo journalctl -u thesis-uart-collector.service -f
```

---

## Data Format

### Unified CSV Output

All data is saved to: `~/thesis_data/sensor_data/unified_sensor_data.csv`

**Format:**
```csv
timestamp,cycle_number,master_temp,master_hum,master_tvoc,master_eco2,master_mq3_ppm,node1_temp,node1_hum,node1_tvoc,node1_eco2,node1_mq3_ppm,node2_temp,node2_hum,node2_tvoc,node2_eco2,node2_mq3_ppm
2026-02-05 12:00:00,42,22.5,45.2,150,400,0.5,22.3,46.1,148,395,0.48,22.6,45.8,152,402,0.52
2026-02-05 12:15:00,43,22.7,44.8,155,410,0.6,22.5,45.9,150,398,0.50,22.8,45.2,156,405,0.55
```

Each row contains:
- Complete snapshot of all 3 nodes at one time
- Perfect for ML model training
- Easy to load into pandas/numpy

---

## Troubleshooting

### No Data Received

1. **Check wiring:**
   - ESP32 TX → Pi RX
   - ESP32 RX → Pi TX
   - Common ground

2. **Check serial port:**
   ```bash
   ls -l /dev/ttyAMA0
   cat /dev/ttyAMA0
   ```

3. **Check ESP32 is sending:**
   - Connect ESP32 to computer via USB
   - Open Serial Monitor at 115200 baud
   - Should see "Data sent to Raspberry Pi" message

### Permission Denied

```bash
sudo usermod -a -G dialout $USER
# Log out and back in
```

### Service Won't Start

```bash
# Check logs
sudo journalctl -u thesis-uart-collector.service -n 50

# Test manually
python3 ~/Thesis-Edge-AI/RaspberryPi/scripts/uart_data_collector.py
```

### Data Not Saving

```bash
# Check directory permissions
ls -la ~/thesis_data/sensor_data/

# Check disk space
df -h
```

---

## Testing

### Complete System Test

1. **Power up ESP32 Master** (nodes can be off initially)
2. **Wait for ESP32 warmup** (~45 seconds)
3. **Check Pi logs:**
   ```bash
   tail -f ~/thesis_data/uart_data_collector.log
   ```
4. **Verify CSV created:**
   ```bash
   ls -lh ~/thesis_data/sensor_data/unified_sensor_data.csv
   cat ~/thesis_data/sensor_data/unified_sensor_data.csv
   ```

### Expected Cycle Behavior

Every 15 minutes:
1. ESP32 Master wakes up
2. Sensors warm up (45 seconds)
3. Listens for Node1 and Node2 (90 seconds)
4. Sends JSON data via UART to Pi
5. Pi saves to CSV
6. ESP32 goes to sleep

---

## Data Analysis

### Load Data in Python

```python
import pandas as pd

# Load unified data
df = pd.read_csv('~/thesis_data/sensor_data/unified_sensor_data.csv')

# Convert timestamp to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Set as index
df.set_index('timestamp', inplace=True)

# Now ready for ML!
print(df.head())
print(df.describe())
```

### Quick Stats

```bash
# Count rows
wc -l ~/thesis_data/sensor_data/unified_sensor_data.csv

# View latest entry
tail -n 1 ~/thesis_data/sensor_data/unified_sensor_data.csv
```
