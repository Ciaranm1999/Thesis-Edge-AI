# Thesis-Edge-AI

Multi-node environmental monitoring system with on-device ML inference, built for MSc research comparing edge AI frameworks on ESP32 hardware.

## Overview

Three ESP32 nodes collect temperature, humidity, TVOC, eCO2, and alcohol sensor readings every 15 minutes via ESP-NOW. The master node forwards data to a Raspberry Pi over UART, where it is logged to CSV and paired with camera images. A separate ML training pipeline produces models that are deployed back to the ESP32 for on-device inference, with energy profiled using a Nordic PPK2.

The research focus is comparing AIfES, TensorFlow Lite Micro (TFLM), and TinyOL as inference frameworks for mould-risk prediction in agricultural and logistics contexts.

## System Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Node 1    │    │   Node 2    │    │   Master    │
│   ESP32     │    │   ESP32     │    │   ESP32     │
│  (Sensors)  │    │  (Sensors)  │    │  (Sensors)  │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                   │
       └──────ESP-NOW─────┴───────ESP-NOW─────┤
                                              │
                                        UART (GPIO16/17)
                                              │
                                              ▼
                                   ┌──────────────────┐
                                   │  Raspberry Pi    │
                                   │  Data Storage    │
                                   │  Camera          │
                                   │  Edge AI         │
                                   └──────────────────┘
```

## Repository Structure

```
Thesis-Edge-AI/
├── ESP32/
│   ├── src/
│   │   ├── Master_Node_Main.cpp     # Master node: sensor + UART output
│   │   ├── Node_Main.cpp            # Slave node firmware
│   │   ├── aifes_inference.cpp      # AIfES inference stub
│   │   └── tflm_inference.cpp       # TF Lite Micro inference stub
│   ├── include/
│   ├── lib/
│   └── platformio.ini
│
├── RaspberryPi/
│   ├── scripts/
│   │   ├── uart_data_collector.py   # Main data collection service
│   │   ├── web_dashboard.py         # Live data visualization
│   │   └── Download-BatchData.ps1   # Data download from Pi to local
│   ├── analysis/
│   │   ├── batch_analysis.ipynb     # Per-batch sensor analysis
│   │   └── energy_analysis.ipynb    # PPK2 energy profiling
│   └── docs/
│
├── ML_Training/
│   ├── data_preparation/
│   │   ├── prepare_dataset.py       # Dataset split and export
│   │   └── output/                  # train/test/held-out CSVs
│   ├── model_training/
│   │   └── train_model.py           # Model training and export
│   ├── esp32_datasets/
│   │   ├── mould_prediction_dataset.h  # Dataset header for ESP32
│   │   ├── aifes_weights.h             # AIfES weight arrays
│   │   └── tflm_model.h                # TFLM flatbuffer model
│   ├── ppk2_results/                # PPK2 inference energy traces
│   └── energy_analysis.ipynb        # Framework energy comparison
│
└── README.md
```

## Hardware

**ESP32 nodes (x3)**
- ESP32 development board
- DHT22 (temperature/humidity)
- Adafruit SGP30 (TVOC/eCO2)
- MQ3 (alcohol), with voltage divider
- 5V supply; deep sleep between cycles (~10 µA)

**Raspberry Pi hub**
- Raspberry Pi 5
- Camera Module 3 (12 MP, autofocus)
- LED illumination on GPIO17
- UART from ESP32 master on GPIO15

**Energy measurement**
- Nordic Power Profiler Kit 2 (PPK2)

## ESP32 Wiring

| ESP32 Master | Raspberry Pi |
|---|---|
| GPIO17 (TX2) | Pin 10 (GPIO15 / RX) |
| GPIO16 (RX2) | Pin 8 (GPIO14 / TX) |
| GND | Pin 6 / 9 / 14 |

## Quick Start

**1. Flash firmware**
Open the `ESP32/` folder in PlatformIO. Update the MAC addresses in `Node_Main.cpp` to match your hardware, then flash `Master_Node_Main.cpp` to the master node and `Node_Main.cpp` to both slaves.

**2. Configure Raspberry Pi UART**
```bash
# Disable serial console
sudo nano /boot/cmdline.txt   # remove: console=serial0,115200
sudo nano /boot/config.txt    # add: enable_uart=1
sudo reboot

# Run data collector
cd ~/Thesis-Edge-AI/RaspberryPi/scripts
python3 uart_data_collector.py
```

**3. Download data to local machine**
```powershell
cd RaspberryPi\scripts
.\Download-BatchData.ps1 -BatchName "batch2"
```

Data is saved to `RaspberryPi/RaspberryPiData/batch2/` with subdirectories for `sensor_data/`, `images/`, and `logs/`.

## Data Format

Sensor data is stored as a unified CSV where each row is a full system snapshot across all three nodes:

```
timestamp, cycle_number,
master_temp, master_hum, master_tvoc, master_eco2, master_mq3_ppm,
node1_temp, node1_hum, node1_tvoc, node1_eco2, node1_mq3_ppm,
node2_temp, node2_hum, node2_tvoc, node2_eco2, node2_mq3_ppm
```

## ML Pipeline

Training is done on the PC using `ML_Training/model_training/train_model.py`, which outputs weight arrays (`aifes_weights.h`) and a TFLM flatbuffer (`tflm_model.h`) ready to include directly in the ESP32 firmware. Energy profiling of each framework is done on-device with the PPK2, results saved to `ML_Training/ppk2_results/`.

See [ML_Training/ML_Notes.md](ML_Training/ML_Notes.md) for framework comparison notes.

## Documentation

- [RaspberryPi/README.md](RaspberryPi/README.md) — Pi setup and data collection commands
- [RaspberryPi/docs/guides/SETUP_AND_DATA_GUIDE.md](RaspberryPi/docs/guides/SETUP_AND_DATA_GUIDE.md) — Full wiring and configuration guide
- [RaspberryPi/docs/guides/DOWNLOAD_BATCH_DATA.md](RaspberryPi/docs/guides/DOWNLOAD_BATCH_DATA.md) — Data download reference
- [RaspberryPi/BATCH_WORKFLOW.md](RaspberryPi/BATCH_WORKFLOW.md) — Batch experiment workflow

## Status

| Component | State |
|---|---|
| ESP-NOW mesh (3 nodes) | Done |
| UART to Raspberry Pi | Done |
| Data collection service | Done |
| Camera integration | Done |
| Overnight stability testing | Done |
| ML training pipeline | Done |
| AIfES / TFLM inference stubs | In progress |
| Energy benchmarking (PPK2) | In progress |
| Thesis write-up | In progress |

---

Ciaran Maher — MSc Smart Systems Engineering — Hanze University of Applied Sciences
