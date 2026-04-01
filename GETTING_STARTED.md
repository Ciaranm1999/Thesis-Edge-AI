# Getting Started with Thesis-Edge-AI

Quick guide to get the multi-node environmental monitoring system up and running.

## System Overview

This project consists of:
- **3 ESP32 nodes** (1 Master + 2 Slaves) with environmental sensors
- **Raspberry Pi** hub for data collection and camera capture
- **UART communication** from ESP32 Master to Pi
- **Hourly camera capture** synchronized with sensor data

## Quick Start (5 minutes)

### Prerequisites
- ESP32 nodes already programmed and tested
- Raspberry Pi setup complete (see [docs/RASPBERRY_PI_SETUP_COMPLETE.md](docs/RASPBERRY_PI_SETUP_COMPLETE.md))
- Laptop with SSH and PowerShell

### 1. Connect Hardware
Wire ESP32 Master to Raspberry Pi:
```
ESP32 GPIO17 (TX2)  →  Pi Pin 10 (GPIO15/RX)
ESP32 GPIO16 (RX2)  →  Pi Pin 8 (GPIO14/TX)
ESP32 GND           →  Pi GND (Pin 6/9/14)
```

### 2. Power On System
```bash
# Connect to Pi via SSH
ssh edgeai@172.20.10.3  # Password: 1234
```

### 3. Start Data Collection
The data collector runs automatically on boot. To manually start a new batch:

**On your laptop:**
```powershell
# Connect both laptop and Pi to your iPhone hotspot
powershell -ExecutionPolicy Bypass -File .\RaspberryPi\scripts\Start-Batch2.ps1
```

This will:
- Deploy the latest data collector
- Start batch collection
- Save data to `~/thesis_data/sensor_data/batch2/`
- Capture images to `~/thesis_data/images/batch2/`

### 4. Monitor (Optional)
```bash
# Watch live log
ssh edgeai@172.20.10.3 'tail -f ~/thesis_data/uart_data_collector.log'
```

### 5. Download Data
```powershell
# Download batch data from Pi to laptop
cd RaspberryPi\scripts
.\Download-BatchData.ps1 -BatchName "batch2"
```

See [RaspberryPi/docs/guides/DOWNLOAD_BATCH_DATA.md](RaspberryPi/docs/guides/DOWNLOAD_BATCH_DATA.md) for detailed download instructions.

## First Time Setup

If this is your first time setting up the system, follow:
1. **ESP32:** [ESP32/README.md](ESP32/README.md)
2. **Raspberry Pi:** [RaspberryPi/docs/setup/FIRST_TIME_SETUP.md](RaspberryPi/docs/setup/FIRST_TIME_SETUP.md)
3. **UART Wiring:** [RaspberryPi/docs/setup/UART_SETUP_GUIDE.md](RaspberryPi/docs/setup/UART_SETUP_GUIDE.md)

## Data Format

**CSV:** `~/thesis_data/sensor_data/batchX/unified_sensor_data.csv`
```csv
timestamp,cycle_number,master_temp,master_hum,master_tvoc,master_eco2,master_mq3_ppm,
node1_temp,node1_hum,node1_tvoc,node1_eco2,node1_mq3_ppm,
node2_temp,node2_hum,node2_tvoc,node2_eco2,node2_mq3_ppm
```

**Images:** `~/thesis_data/images/batchX/capture_YYYYMMDD_HHMMSS.jpg`

## Analyzing Data

Use the Jupyter notebooks in `RaspberryPi/analysis/`:
- **batch_analysis.ipynb** - Sensor data visualization and statistics
- **energy_analysis.ipynb** - Power consumption analysis

## Troubleshooting

**No data appearing?**
- Check ESP32 nodes are powered and blinking
- Verify UART wiring (TX→RX, RX→TX)
- Check log: `tail -f ~/thesis_data/uart_data_collector.log`

**Can't SSH to Pi?**
- Ensure both devices on same network (or hotspot)
- Try: `ssh edgeai@172.20.10.3` (hotspot IP)
- Check Pi is powered (green LED solid, red LED blinking)

**Images not capturing?**
- Camera captures hourly (check log for "Captured:" message)
- LED should flash when capturing
- Check `~/thesis_data/images/batchX/` directory

## Documentation

- **Main README:** Project overview
- **Setup Guides:** [RaspberryPi/docs/setup/](RaspberryPi/docs/setup/)
- **Usage Guides:** [RaspberryPi/docs/guides/](RaspberryPi/docs/guides/)
- **Your Configuration:** [docs/RASPBERRY_PI_SETUP_COMPLETE.md](docs/RASPBERRY_PI_SETUP_COMPLETE.md)

## Support

For issues or questions, check:
1. Relevant documentation in `docs/`
2. Log files on the Pi
3. GitHub issues

---

**Current Branch:** RaspPI (active development)  
**Stable Branch:** main

Happy monitoring! 🍓📊
