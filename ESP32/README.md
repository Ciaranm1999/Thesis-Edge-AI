# ESP32 Sensor Network - PlatformIO Project

✅ **Multi-node environmental monitoring system with ESP-NOW and UART**

## System Overview

This project implements a 3-node ESP32 sensor network:
- **Master Node:** Collects data from 2 slave nodes via ESP-NOW, sends unified data to Raspberry Pi via UART
- **Slave Nodes (x2):** Collect sensor data and transmit to master via ESP-NOW
- All nodes operate on synchronized 15-minute cycles with deep sleep

## Quick Start Guide

### 1. Open Project in VS Code
- Open this `ESP32` folder in VS Code
- PlatformIO will automatically detect the `platformio.ini` file
- Libraries will be downloaded automatically on first build

### 2. Select Which Program to Build/Upload

Edit `platformio.ini` and change the `default_envs` line to one of:
- `master_node` - **Master node with UART output (PRIMARY)**
- `node_main` - Slave sensor node
- `voc_dht_test` - VOC/DHT sensor test code
- `mq3_calibration` - MQ3 sensor calibration
- `mac_address` - Read ESP32 MAC address

Example:
```ini
[platformio]
default_envs = master_node  ; Upload master code
```

### 3. Update MAC Addresses

**IMPORTANT:** Update MAC addresses in the code to match your hardware.

**Get MAC addresses:**
```ini
[platformio]
default_envs = mac_address  ; Read MAC from each ESP32
```

Upload to each ESP32 and note the MAC address from serial monitor.

**Update in code:**

[src/Master_Node_Main.cpp](src/Master_Node_Main.cpp):
```cpp
uint8_t node1Mac[] = { 0xE0, 0x8C, 0xFE, 0x2D, 0xD8, 0x60 }; // YOUR NODE 1 MAC
uint8_t node2Mac[] = { 0x7C, 0x9E, 0xBD, 0x45, 0x2A, 0xB4 }; // YOUR NODE 2 MAC
```

[src/Node_Main.cpp](src/Node_Main.cpp):
```cpp
uint8_t masterMac[] = {0xCC, 0xDB, 0xA7, 0x98, 0xD2, 0xD0}; // YOUR MASTER MAC
```

### 4. Build and Upload

**Using PlatformIO Toolbar** (bottom of VS Code):
- ✓ (checkmark) - Build project
- → (arrow) - Upload to ESP32
- 🔌 (plug) - Open Serial Monitor
- 🗑️ (trash) - Clean build files

**Using Command Palette** (Ctrl+Shift+P or Cmd+Shift+P):
- Type "PlatformIO: Build"
- Type "PlatformIO: Upload"
- Type "PlatformIO: Serial Monitor"

**Using Terminal**:
```bash
# Build default environment
pio run

# Build specific environment
pio run -e master_node

# Upload to ESP32
pio run --target upload

# Open serial monitor
pio device monitor

# Build and upload
pio run --target upload && pio device monitor
```

### 4. Connect Your ESP32
- Plug in ESP32 via USB
- PlatformIO will auto-detect the COM port
- If it doesn't, add to platformio.ini:
  ```ini
  [env:node_main]
  upload_port = COM3  ; Change to your port
  monitor_port = COM3
  ```

## Project Structure

```
ESP32/
├── platformio.ini          # PlatformIO configuration
├── src/                    # Source code (.cpp files)
│   ├── Master_Node_Main.cpp    # Master with UART output (PRIMARY)
│   ├── Node_Main.cpp           # Slave node code
│   ├── VOC_DHT_print_code.cpp  # Sensor testing
│   ├── MQ3_Calibration_Code.cpp
│   └── MacAddress.cpp
├── overnight_analysis/     # Stability testing data
│   ├── OVERNIGHT_STABILITY_SUMMARY.md
│   ├── analyze_overnight_data.py
│   └── *.png (charts)
├── include/                # Header files
├── .pio/                   # PlatformIO build files (auto-created)
└── README.md               # This file
```

## Available Programs

| Environment | File | Description |
|------------|------|-------------|
| `master_node` | Master_Node_Main.cpp | **Master: ESP-NOW + UART to Pi** |
| `node_main` | Node_Main.cpp | Slave node with deep sleep & ESP-NOW |
| `voc_dht_test` | VOC_DHT_print_code.cpp | VOC & DHT22 sensor test |
| `mq3_calibration` | MQ3_Calibration_Code.cpp | MQ3 alcohol sensor calibration |
| `mac_address` | MacAddress.cpp | Read ESP32 MAC address |

## Hardware Connections

### All ESP32 Nodes
- **DHT22:** GPIO 4
- **SGP30:** I2C (SDA=GPIO21, SCL=GPIO22)
- **MQ3:** ADC GPIO 34 (with voltage divider: 56kΩ + 100kΩ)

### Master Node UART (to Raspberry Pi)
- **TX2 (GPIO17)** → Pi RX (Pin 10, GPIO15)
- **RX2 (GPIO16)** → Pi TX (Pin 8, GPIO14)
- **GND** → Pi GND

## System Operation

### 15-Minute Cycle
1. **Wake from deep sleep**
2. **SGP30 warmup** (45 seconds)
3. **Listen for slave nodes** (90 seconds max)
4. **Send unified data via UART** (master only)
5. **Deep sleep** until next cycle

### Power Consumption
- Active: ~100mA (during warmup/listen)
- Deep sleep: ~10µA
- Average: ~15mA over 15-minute cycle

## Overnight Stability Testing

Complete overnight test results available in [overnight_analysis/](overnight_analysis/)

**Key Findings:**
- ✅ 97.9% node synchronization success
- ✅ Average sync offset: 6.8ms
- ✅ Zero data loss over 12+ hours
- ✅ Stable 15-minute cycle timing

## Required Hardware

- **ESP32 Development Board** (x3)
- **DHT22** Temperature/Humidity Sensor
- **SGP30** VOC/CO2 Sensor (I2C)
- **MQ3** Alcohol/Gas Sensor
- Resistors for MQ3 voltage divider (56kΩ, 100kΩ)
- **USB cable** for programming

## Installed Libraries

All libraries are automatically managed by PlatformIO:
- DHT sensor library (Adafruit)
- Adafruit SGP30 Sensor
- Adafruit Unified Sensor
- Adafruit BusIO
- ArduinoJson (for UART data formatting)

## Troubleshooting

### Libraries Not Found
- PlatformIO automatically downloads libraries on first build
- Wait for "Installing dependencies..." to complete
- Check `.pio/libdeps/` folder to verify installation

### Port Not Found
- Check Device Manager (Windows) or `ls /dev/tty*` (Linux/Mac)
- Install CH340/CP2102 USB drivers if needed
- Try different USB cable (must support data, not just power)
- Add `upload_port = COM3` to your environment in platformio.ini

### Upload Failed
- Hold **BOOT** button on ESP32 while uploading
- Verify board selection: `board = esp32dev`
- Close other programs using the serial port (Arduino IDE, serial monitors)
- Try lower upload speed: `upload_speed = 115200`

### ESP-NOW Issues
- Update MAC addresses in the code (see Quick Start section)
- Use `mac_address` environment to find your ESP32's MAC
- Ensure all ESP32s are powered and in range
- Check serial monitor for "ESP-NOW packet received" messages

### UART Data Not Received by Pi
- Verify wiring: ESP32 TX → Pi RX
- Check serial console disabled on Pi (`/boot/cmdline.txt`)
- Test UART on Pi: `cat /dev/ttyAMA0`
- Check baud rate matches (115200)

### Build Errors
```bash
# Clean build
pio run --target clean

# Update platform
pio pkg update

# Rebuild
pio run
```

## Switching from Arduino IDE

✅ **Advantages of PlatformIO:**
- **Better IntelliSense** - Full code completion
- **Integrated workflow** - Build, upload, monitor in one place
- **Library management** - Automatic dependency resolution
- **Multiple configs** - Switch between projects easily
- **Professional debugging** - Hardware debugging support
- **Version control** - Git-friendly structure

## Workflow Tips

1. **Finding MAC Address:**
   ```bash
   # Set default to mac_address
   pio run -e mac_address --target upload
   pio device monitor
   ```

2. **Deploy to 3 ESP32s:**
   ```bash
   # Upload master code
   pio run -e master_node --target upload
   
   # Disconnect, connect Node 1
   pio run -e node_main --target upload
   
   # Disconnect, connect Node 2
   pio run -e node_main --target upload
   ```

3. **Monitor Master with UART connected:**
   - USB serial monitor shows debug output
   - UART2 (GPIO16/17) sends data to Pi simultaneously

2. **Calibrating MQ3:**
   ```bash
   pio run -e mq3_calibration --target upload
   pio device monitor
   ```

3. **Testing Sensors:**
   ```bash
   pio run -e voc_dht_test --target upload
   pio device monitor
   ```

4. **Deploying Nodes:**
   - Upload `node_main` to sensor nodes
   - Upload `master_node` to master/receiver

## Additional Resources

- **PlatformIO Docs:** https://docs.platformio.org/
- **ESP32 Arduino Core:** https://docs.espressif.com/projects/arduino-esp32/
- **ESP-NOW Guide:** https://randomnerdtutorials.com/esp-now-esp32-arduino-ide/

## Next Steps

1. ✅ Project structure created
2. ✅ Libraries configured
3. ⬜ Update MAC addresses in code
4. ⬜ Calibrate MQ3 sensors
5. ⬜ Test individual sensors
6. ⬜ Deploy to hardware
