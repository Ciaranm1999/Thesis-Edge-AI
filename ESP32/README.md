# ESP32 Projects - VS Code + PlatformIO Setup

✅ **Successfully configured for VS Code with PlatformIO!**

## Quick Start Guide

### 1. Open Project in VS Code
- Open this `ESP32` folder in VS Code
- PlatformIO will automatically detect the `platformio.ini` file
- Libraries will be downloaded automatically on first build

### 2. Select Which Program to Build/Upload

Edit `platformio.ini` and change the `default_envs` line to one of:
- `node_main` - Main sensor node (default)
- `master_node` - Master node that collects data
- `voc_dht_test` - VOC/DHT sensor test code
- `mq3_calibration` - MQ3 sensor calibration
- `mac_address` - Read ESP32 MAC address

Example:
```ini
[platformio]
default_envs = master_node  ; Change this line
```

### 3. Build and Upload

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
├── platformio.ini      # PlatformIO configuration
├── src/                # Source code (.cpp files)
│   ├── Node_Main.cpp
│   ├── Master_Node_Main.cpp
│   ├── VOC_DHT_print_code.cpp
│   ├── MQ3_Calibration_Code.cpp
│   └── MacAddress.cpp
├── include/            # Header files (if needed)
├── lib/                # Custom libraries (auto-created)
├── .pio/               # PlatformIO build files (auto-created)
└── README.md           # This file
```

## Available Programs

| Environment | File | Description |
|------------|------|-------------|
| `node_main` | Node_Main.cpp | Sensor node with deep sleep & ESP-NOW |
| `master_node` | Master_Node_Main.cpp | Master node receiving ESP-NOW data |
| `voc_dht_test` | VOC_DHT_print_code.cpp | VOC & DHT22 sensor test |
| `mq3_calibration` | MQ3_Calibration_Code.cpp | MQ3 alcohol sensor calibration |
| `mac_address` | MacAddress.cpp | Read ESP32 MAC address |

## Required Hardware

- **ESP32 Development Board**
- **DHT22** Temperature/Humidity Sensor (GPIO 4)
- **SGP30** VOC/CO2 Sensor (I2C: SDA=21, SCL=22)
- **MQ3** Alcohol/Gas Sensor (ADC: GPIO 34)
- **USB cable** for programming

## Installed Libraries

All libraries are automatically managed by PlatformIO:
- DHT sensor library (Adafruit)
- Adafruit SGP30 Sensor
- Adafruit Unified Sensor
- Adafruit BusIO

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
- Update MAC addresses in the code
- Use `mac_address` environment to find your ESP32's MAC
- Ensure all ESP32s are on the same WiFi channel
- Check ESP-NOW is initialized before sending

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
