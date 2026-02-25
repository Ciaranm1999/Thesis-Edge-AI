# Migration Guide - Updated Folder Structure

## What Changed?

The RaspberryPi folder has been reorganized for better maintainability:

### Old Structure → New Structure

```
OLD:                              NEW:
RaspberryPi/                      RaspberryPi/
├── data_collector.py        →    ├── scripts/
├── camera_test.py           →    │   ├── data_collector.py
├── led_test.py              →    │   ├── setup_system.sh
├── camera_test.sh           →    │   ├── setup_autologin.sh
├── setup_system.sh          →    │   └── Connect-RaspberryPi.ps1
├── setup_autologin.sh       →    ├── tests/
├── Connect-RaspberryPi.ps1  →    │   ├── camera_test.py
├── thesis-data...service    →    │   ├── camera_test.sh
├── MQTT_SETUP_GUIDE.md      →    │   └── led_test.py
├── QUICK_START.md           →    ├── services/
├── README_MQTT.md           →    │   └── thesis-data-collector.service
├── FIRST_TIME_SETUP.md      →    ├── docs/
├── RUN_TESTS.md             →    │   ├── MQTT_SETUP_GUIDE.md
├── SSH_SETUP.md             →    │   ├── QUICK_START.md
└── README.md                     │   ├── README_MQTT.md
                                  │   ├── FIRST_TIME_SETUP.md
                                  │   ├── RUN_TESTS.md
                                  │   └── SSH_SETUP.md
                                  ├── config/
                                  │   └── paho-mqtt-stubs.pyi
                                  ├── pyrightconfig.json
                                  ├── camera_images/
                                  └── README.md
```

## What You Need to Update

### If You've Already Set Up the System:

**On Raspberry Pi:**

1. Pull the latest changes:
```bash
cd ~/Thesis-Edge-AI
git pull origin RaspPI
```

2. The systemd service needs to be updated:
```bash
cd ~/Thesis-Edge-AI/RaspberryPi/scripts
sudo cp ../services/thesis-data-collector.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart thesis-data-collector
```

3. Verify it's working:
```bash
sudo systemctl status thesis-data-collector
```

### If You're Setting Up Fresh:

Nothing special needed! Just follow the [docs/QUICK_START.md](docs/QUICK_START.md) as usual.

The setup scripts automatically reference the new paths.

## Updated Commands

### Test Scripts
```bash
# OLD: python3 camera_test.py
# NEW:
cd ~/Thesis-Edge-AI/RaspberryPi/tests
python3 camera_test.py

# OLD: python3 led_test.py
# NEW:
cd ~/Thesis-Edge-AI/RaspberryPi/tests
python3 led_test.py
```

### Setup Scripts
```bash
# OLD: ./setup_system.sh
# NEW:
cd ~/Thesis-Edge-AI/RaspberryPi/scripts
./setup_system.sh

# OLD: ./setup_autologin.sh
# NEW:
cd ~/Thesis-Edge-AI/RaspberryPi/scripts
./setup_autologin.sh
```

### Documentation
```bash
# All docs now in docs/ folder
cat ~/Thesis-Edge-AI/RaspberryPi/docs/QUICK_START.md
cat ~/Thesis-Edge-AI/RaspberryPi/docs/MQTT_SETUP_GUIDE.md
```

## What Was Fixed?

✅ **Import Errors Resolved**: Added `pyrightconfig.json` to suppress IDE warnings for Raspberry Pi-specific libraries (paho-mqtt, picamera2, RPi.GPIO)

✅ **Better Organization**: Files are now logically grouped by purpose

✅ **Updated Paths**: All scripts and services now reference the correct new paths

✅ **Type Checking**: Added proper type stubs for better IDE support

## Questions?

See [docs/MQTT_SETUP_GUIDE.md](docs/MQTT_SETUP_GUIDE.md) for complete documentation.
