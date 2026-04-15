# Thesis-Edge-AI

Multi-node environmental monitoring system with on-device ML inference, built for MSc research comparing TinyML frameworks on ESP32 hardware for autonomous mould detection in post-harvest cold chain logistics.

**Thesis:** *Energy Profiling of TinyML Frameworks for Autonomous Mould Detection on Disconnected Microcontroller Nodes*
**Author:** Ciaran Maher — MSc Smart Systems Engineering — Hanze University of Applied Sciences

## Overview

Three ESP32 nodes collect temperature, humidity, TVOC, eCO2, and ethanol sensor readings every 15 minutes via ESP-NOW. The master node forwards data to a Raspberry Pi over UART, where it is logged to CSV and paired with hourly camera images for mould-onset labelling. An offline ML training pipeline produces models that are deployed back to the ESP32 for on-device inference and training, with energy profiled using a Nordic PPK2.

The research compares four TinyML configurations for binary mould-risk classification:

| Configuration | Framework | Description |
|---|---|---|
| Inference only | TF Lite Micro (INT8) | Pre-trained frozen model |
| Inference only | AIfES (float32) | Pre-trained frozen model |
| Output-layer adaptation | TinyOL | Fine-tunes final layer on-device |
| Full on-device training | AIfES | Trains all weights from scratch on-device |

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
                                   │  Raspberry Pi 5  │
                                   │  Data logging    │
                                   │  Camera labelling│
                                   └──────────────────┘
```

## Repository Structure

```
Thesis-Edge-AI/
├── ESP32/
│   ├── src/
│   │   ├── aifes_inference.cpp          # AIfES float32 inference benchmark
│   │   ├── aifes_training_benchmark.cpp # AIfES full on-device training benchmark
│   │   ├── tflm_inference.cpp           # TF Lite Micro INT8 inference benchmark
│   │   └── tinyol_benchmark.cpp         # TinyOL output-layer adaptation benchmark
│   ├── IDE_ESP_Files/                   # Arduino IDE versions of node firmware
│   └── platformio.ini
│
├── RaspberryPi/
│   ├── scripts/
│   │   ├── uart_data_collector.py       # Main data collection service
│   │   ├── web_dashboard.py             # Live data visualisation
│   │   └── Download-BatchData.ps1       # Data download from Pi to local
│   └── analysis/
│       ├── batch_analysis.ipynb         # Per-batch sensor and onset analysis
│       └── energy_analysis.ipynb        # PPK2 CPU frequency energy profiling
│
├── ML_Training/
│   ├── data_preparation/
│   │   ├── prepare_dataset.py           # Dataset split and export
│   │   └── output/                      # train/test CSVs and dataset stats
│   ├── model_training/
│   │   ├── train_model.py               # Trains TFLM and AIfES inference models
│   │   └── train_tinyol_backbone.py     # Trains weakened TinyOL backbone
│   ├── esp32_datasets/
│   │   ├── combined_training_dataset.h  # Full training corpus for AIfES (Batches 1-4)
│   │   ├── held_out_dataset.h           # Held-out test set (Batch 5, 332 samples)
│   │   ├── aifes_weights.h              # AIfES weight arrays
│   │   ├── tflm_model.h                 # TFLM flatbuffer model
│   │   └── tinyol_weights.h             # TinyOL backbone weights
│   ├── ppk2_results/                    # PPK2 energy trace plots and raw CSVs
│   └── energy_analysis.ipynb            # ML framework energy benchmarking
│
├── ThesisReport/
│   └── Report/                          # LaTeX source for the full thesis
│       ├── main.tex
│       ├── references.bib
│       ├── ipb.cls
│       ├── chapters/
│       └── images/
│
├── generate_thesis_figures.py           # Generates all thesis figures from data
└── README.md
```

## Hardware

**ESP32 nodes (x3)**
- ESP32 development board
- DHT22 (temperature / relative humidity)
- Adafruit SGP30 (TVOC / eCO2)
- MQ3 (ethanol vapour), with resistive voltage divider
- Powered at 3.3 V via PPK2 during energy experiments

**Raspberry Pi hub**
- Raspberry Pi 5
- Camera Module 3 (12 MP, autofocus) for hourly ground-truth images
- UART from ESP32 master on GPIO15

**Energy measurement**
- Nordic Power Profiler Kit 2 (PPK2) — acts as both regulated 3.3 V supply and precision current logger

## ESP32 Wiring

| ESP32 Master | Raspberry Pi |
|---|---|
| GPIO17 (TX2) | Pin 10 (GPIO15 / RX) |
| GPIO16 (RX2) | Pin 8 (GPIO14 / TX) |
| GND | Pin 6 / 9 / 14 |

## Quick Start

**1. Flash firmware**

Open the `ESP32/` folder in PlatformIO. Update the MAC addresses in the slave firmware to match your hardware, then flash the master and slave firmware to the three nodes.

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
.\Download-BatchData.ps1 -BatchName "batch5"
```

Data is saved to `RaspberryPi/RaspberryPiData/<batch>/` with subdirectories for `sensor_data/`, `images/`, and `logs/`.

## ML Pipeline

1. Run `ML_Training/data_preparation/prepare_dataset.py` to split the five experimental batches into train/test CSVs and export ESP32 header files.
2. Run `ML_Training/model_training/train_model.py` to train the TFLM and AIfES inference models and export `aifes_weights.h` and `tflm_model.h`.
3. Run `ML_Training/model_training/train_tinyol_backbone.py` to train the weakened TinyOL backbone and export `tinyol_weights.h`.
4. Flash the relevant firmware from `ESP32/src/` and connect the PPK2 to record energy traces.
5. Analyse energy results in `ML_Training/energy_analysis.ipynb`.

## Key Results

| Configuration | Accuracy | Energy per operation |
|---|---|---|
| TF Lite Micro (INT8 inference) | 93.7% | 8.9 µJ |
| AIfES (float32 inference) | 94.0% | 6.3 µJ |
| TinyOL (output-layer update) | 86.1% | 1.8 µJ |
| AIfES (full on-device training, per step) | 77.1% | 194.8 µJ |

Battery lifetime on a 10,000 mAh cell: ~16 hours (current prototype with MQ3 heater). Projected 4.2 days with MEMS gas sensor replacement and SGP30 duty-gating.

## Status

| Component | State |
|---|---|
| ESP-NOW mesh (3 nodes) | Done |
| UART to Raspberry Pi | Done |
| Data collection service | Done |
| Camera ground-truth labelling | Done |
| 5-batch experimental dataset | Done |
| ML training pipeline | Done |
| AIfES / TFLM / TinyOL firmware | Done |
| Energy benchmarking (PPK2) | Done |
| Thesis write-up | Done |

---

Ciaran Maher — MSc Smart Systems Engineering — Hanze University of Applied Sciences
