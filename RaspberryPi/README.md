# Raspberry Pi - Camera Module 3 & Edge AI

This directory contains code and setup instructions for the Raspberry Pi component of the Thesis Edge AI project.

## 📁 Project Structure

```
RaspberryPi/
├── scripts/              # Main scripts and utilities
│   ├── uart_data_collector.py  # Main UART data collection service
│   ├── data_collector.py       # Legacy MQTT collector (archived)
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
│   ├── UART_SETUP_GUIDE.md     # UART connection guide (PRIMARY) ⚡
│   ├── SETUP_AND_DATA_GUIDE.md # Data storage & system setup
│   ├── QUICK_START.md          # 10-minute setup guide
│   ├── FIRST_TIME_SETUP.md     # Initial Pi setup
│   ├── SSH_SETUP.md            # SSH configuration
│   ├── RUN_TESTS.md            # Hardware testing guide
│   └── archive_mqtt/           # Old MQTT documentation (for reference)
├── config/               # Configuration files
│   └── pyrightconfig.json      # Python type checking config
└── camera_images/        # Test image output directory

```

## Hardware
- **Raspberry Pi** (Model 3/4/5)
- **Camera Module 3** (12MP, autofocus)
- **LEDs** for status indication
- **UART Connection to ESP32** (GPIO14/15)

## 🚀 Quick Start

### 1. Configure UART (One-Time Setup)
See [docs/UART_SETUP_GUIDE.md](docs/UART_SETUP_GUIDE.md) for detailed wiring and configuration.

**Quick version:**
```bash
# Disable serial console
sudo nano /boot/cmdline.txt  # Remove console=serial0,115200
sudo nano /boot/config.txt   # Add: enable_uart=1

# Reboot
sudo reboot
```

### 2. Install UART Data Collector
```bash
cd ~/Thesis-Edge-AI/RaspberryPi/scripts

# Test manually first
python3 uart_data_collector.py

# Install as service
sudo cp ../services/thesis-uart-collector.service /etc/systemd/system/
sudo systemctl enable thesis-uart-collector
sudo systemctl start thesis-uart-collector
```

### 3. Verify Everything Works
```bash
# Check service
sudo systemctl status thesis-uart-collector

# View logs
tail -f ~/thesis_data/uart_data_collector.log

# Check collected data
ls -lh ~/thesis_data/sensor_data/
cat ~/thesis_data/sensor_data/unified_sensor_data.csv
```

## 🔧 Common Commands

```bash
# Service management
sudo systemctl start thesis-uart-collector
sudo systemctl stop thesis-uart-collector
sudo systemctl restart thesis-uart-collector
sudo systemctl status thesis-uart-collector

# View logs
journalctl -u thesis-uart-collector -f
tail -f ~/thesis_data/uart_data_collector.log

# Monitor UART directly
cat /dev/ttyAMA0

# Test hardware
cd ~/Thesis-Edge-AI/RaspberryPi/tests
python3 camera_test.py
python3 led_test.py
```

## 📚 Documentation

For detailed setup and usage instructions, see:
- **[docs/guides/DOWNLOAD_BATCH_DATA.md](docs/guides/DOWNLOAD_BATCH_DATA.md)** - Download data for analysis (⭐ START HERE for data retrieval)
- **[docs/UART_SETUP_GUIDE.md](docs/UART_SETUP_GUIDE.md)** - UART wiring & configuration (PRIMARY)
- **[docs/SETUP_AND_DATA_GUIDE.md](docs/SETUP_AND_DATA_GUIDE.md)** - Data storage format & locations
- **[docs/QUICK_START.md](docs/QUICK_START.md)** - Fast setup guide
- **[docs/RUN_TESTS.md](docs/RUN_TESTS.md)** - Hardware testing procedures

## 🎯 System Features

### Data Collection
- ✅ Receives sensor data from ESP32 Master via UART
- ✅ Saves all 3 nodes (master, node1, node2) to unified CSV format
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

## 📁 Data Storage

### On Raspberry Pi
All data saved to `~/thesis_data/`:
```
thesis_data/
├── sensor_data/
│   ├── Batch1/
│   │   └── unified_sensor_data.csv
│   ├── batch2/
│   │   └── unified_sensor_data.csv
│   └── batch3/
│       └── unified_sensor_data.csv
├── images/
│   ├── Batch1/
│   │   ├── capture_20260220_220602.jpg
│   │   └── ...
│   ├── batch2/
│   │   ├── capture_20260225_181409.jpg
│   │   └── ...
│   └── batch3/
│       └── ...
└── uart_data_collector.log
```

### On Local Machine (for Analysis)
Data downloaded to `RaspberryPi/RaspberryPiData/`:
```
RaspberryPiData/
├── images/
│   ├── Batch1/
│   ├── batch2/
│   └── batch3/
└── sensor_data/
    ├── Batch1/
    │   └── unified_sensor_data.csv
    ├── batch2/
    │   └── unified_sensor_data.csv
    └── batch3/
        └── unified_sensor_data.csv
```

**Unified CSV Format:**
```csv
timestamp,cycle_number,master_temp,master_hum,master_tvoc,master_eco2,master_mq3_ppm,node1_temp,node1_hum,node1_tvoc,node1_eco2,node1_mq3_ppm,node2_temp,node2_hum,node2_tvoc,node2_eco2,node2_mq3_ppm
2026-02-05 12:00:00,42,22.5,45.2,150,400,0.5,22.3,46.1,148,395,0.48,22.6,45.8,152,402,0.52
```

## 📥 Downloading Batch Data for Analysis

To download data from the Pi for analysis on your laptop:

### Quick Method (Automated Script)
```powershell
# From Windows PowerShell
cd RaspberryPi\scripts
.\Download-BatchData.ps1 -BatchName "batch3"
```

The script will:
- ✅ Connect to Pi via SSH
- ✅ Download sensor CSV data
- ✅ Download all batch images  
- ✅ Organize data in correct folder structure
- ✅ Show download summary

### Manual Method
See **[docs/guides/DOWNLOAD_BATCH_DATA.md](docs/guides/DOWNLOAD_BATCH_DATA.md)** for detailed manual download instructions.

**After downloading:**
1. Open `RaspberryPi/analysis/batch_analysis.ipynb` in Jupyter
2. Update `SINGLE_BATCH = "batch3"` to your batch name
3. Run all cells to generate analysis and plots

## 🎓 For Thesis

This system demonstrates:
- Direct serial communication (UART) between edge devices
- Autonomous data collection with minimal power consumption
- Unified data format optimized for ML model training
- Multi-sensor data fusion across distributed nodes
- Image capture synchronized with sensor readings

## 🛠️ Useful Commands

### System Info
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
