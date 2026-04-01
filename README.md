# Thesis-Edge-AI

## Multi-Node Environmental Monitoring System with Edge AI

This repository contains the complete implementation of a distributed sensor network for environmental monitoring, combining ESP32 nodes with Raspberry Pi for data collection and edge AI processing.

## System Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Node 1    │    │   Node 2    │    │   Master    │
│   ESP32     │    │   ESP32     │    │   ESP32     │
│  (Sensors)  │    │  (Sensors)  │    │  (Sensors)  │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                   │
       └──────ESP-NOW─────┴───────ESP-NOW────┤
                                              │
                                        UART (GPIO16/17)
                                              │
                                              ▼
                                   ┌──────────────────┐
                                   │  Raspberry Pi    │
                                   │  - Data Storage  │
                                   │  - Camera        │
                                   │  - Edge AI       │
                                   └──────────────────┘
```

## Features

### ESP32 Network
- ✅ **3-Node Configuration:** 1 Master + 2 Slave nodes
- ✅ **ESP-NOW Communication:** Low-power wireless between nodes
- ✅ **Synchronized Data Collection:** All nodes wake on 15-minute cycle
- ✅ **Power Efficient:** Deep sleep between cycles (~10µA)
- ✅ **Multi-Sensor:** DHT22 (temp/humidity), SGP30 (TVOC/eCO2), MQ3 (alcohol)

### Raspberry Pi Hub
- ✅ **UART Data Reception:** Direct serial from ESP32 Master
- ✅ **Unified Data Storage:** All 3 nodes in single CSV (ML-ready)
- ✅ **Camera Integration:** Synchronized image capture
- ✅ **Auto-Start Service:** Runs on boot
- ✅ **Edge AI Ready:** Platform for model inference

## Project Structure

```
Thesis-Edge-AI/
├── ESP32/                    # ESP32 firmware
│   ├── src/
│   │   ├── Master_Node_Main.cpp    # Master with UART output
│   │   └── Node_Main.cpp           # Slave node firmware
│   ├── overnight_analysis/         # Stability testing data
│   └── platformio.ini
│
├── RaspberryPi/              # Raspberry Pi code
│   ├── scripts/
│   │   ├── uart_data_collector.py  # Main data collector
│   │   └── web_dashboard.py        # Data visualization
│   ├── docs/
│   │   ├── UART_SETUP_GUIDE.md     # Wiring & configuration
│   │   └── SETUP_AND_DATA_GUIDE.md # System setup
│   └── tests/                      # Hardware tests
│
└── README.md
```

## Quick Start

### 1. ESP32 Setup
```bash
# Open in PlatformIO
# Upload Master_Node_Main.cpp to master ESP32
# Upload Node_Main.cpp to slave nodes
# Update MAC addresses in code to match your hardware
```

### 2. Wiring

**ESP32 Master → Raspberry Pi:**
| ESP32 Pin | → | Pi Pin | Function |
|-----------|---|--------|----------|
| GPIO17 (TX2) | → | Pin 10 (GPIO15) | Data |
| GPIO16 (RX2) | → | Pin 8 (GPIO14) | (unused) |
| GND | → | Pin 6/9/14 | Ground |

### 3. Raspberry Pi Setup
```bash
# Configure UART (disable serial console)
sudo nano /boot/cmdline.txt  # Remove console=serial0
sudo nano /boot/config.txt   # Add: enable_uart=1
sudo reboot

# Install data collector
cd ~/Thesis-Edge-AI/RaspberryPi/scripts
python3 uart_data_collector.py
```

See [RaspberryPi/docs/UART_SETUP_GUIDE.md](RaspberryPi/docs/UART_SETUP_GUIDE.md) for detailed instructions.

## Downloading Data from Raspberry Pi

Use the standardized batch download script to retrieve sensor data and images:

```powershell
cd RaspberryPi\scripts
.\Download-BatchData.ps1 -BatchName "batch2"
```

The script will:
- ✅ Download sensor CSV data for the specified batch
- ✅ Download all images for the batch  
- ✅ Organize data in the correct RaspberryPiData folder structure
- ✅ Verify download completeness

**For detailed instructions and troubleshooting:**
- 📖 [Full Download Guide](RaspberryPi/docs/guides/DOWNLOAD_BATCH_DATA.md)
- 🚀 [Quick Reference](RaspberryPi/DOWNLOAD_QUICK_REFERENCE.md)
- 📊 [Complete Workflow](RaspberryPi/BATCH_WORKFLOW.md)

The script will create three subdirectories:
- `sensor_data/` - CSV files with unified sensor readings
- `images/` - JPG images from camera captures
- `logs/` - System log files

## Starting Batch Data Collection

To start a new batch experiment (e.g., batch2, batch3):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Start-Batch2.ps1
```

This script will automatically:
- Deploy the updated data collector to the Pi
- Create batch-specific directories
- Start data collection in the background

Data will be saved to `~/thesis_data/sensor_data/batch2/` and `~/thesis_data/images/batch2/` on the Pi.

## Data Format

**Unified CSV:** `~/thesis_data/sensor_data/unified_sensor_data.csv`

```csv
timestamp,cycle_number,master_temp,master_hum,master_tvoc,master_eco2,master_mq3_ppm,node1_temp,node1_hum,node1_tvoc,node1_eco2,node1_mq3_ppm,node2_temp,node2_hum,node2_tvoc,node2_eco2,node2_mq3_ppm
2026-02-05 12:00:00,42,22.5,45.2,150,400,0.5,22.3,46.1,148,395,0.48,22.6,45.8,152,402,0.52
```

Perfect for ML training - each row is a complete system snapshot.

## Documentation

- **[ESP32/README.md](ESP32/README.md)** - Firmware details & overnight testing
- **[RaspberryPi/README.md](RaspberryPi/README.md)** - Pi setup & commands
- **[RaspberryPi/docs/UART_SETUP_GUIDE.md](RaspberryPi/docs/UART_SETUP_GUIDE.md)** - Complete wiring guide
- **[RaspberryPi/docs/SETUP_AND_DATA_GUIDE.md](RaspberryPi/docs/SETUP_AND_DATA_GUIDE.md)** - Data storage info

## Hardware Requirements

### ESP32 Nodes (x3)
- ESP32 Development Board
- DHT22 Temperature/Humidity Sensor
- Adafruit SGP30 TVOC/eCO2 Sensor
- MQ3 Alcohol Sensor
- Voltage divider circuit for MQ3
- 5V power supply

### Raspberry Pi
- Raspberry Pi 3/4/5
- Camera Module 3 (12MP)
- microSD card (16GB+)
- LED (GPIO17) for camera illumination

## Current Status

- ✅ ESP32 ESP-NOW mesh network
- ✅ UART communication to Raspberry Pi
- ✅ Unified CSV data format
- ✅ Overnight stability testing complete
- ✅ 15-minute cycle operation validated
- 🔄 Edge AI model training (in progress)
- 📝 Thesis writing (in progress)

## Future Work

- [ ] Edge AI inference on Raspberry Pi
- [ ] Real-time anomaly detection
- [ ] BLE Low Energy communication option
- [ ] Solar power integration
- [ ] Mobile app for monitoring

## License

Academic project - All rights reserved

## Author

Ciaran Mahon  
MSc Smart Systems Engineering  
Hanze University of Applied Sciences

---

**Branch:** `RaspPI` - Main development branch with UART implementation