#!/bin/bash
# Setup script for Thesis Data Collection System
# Run this on the Raspberry Pi to install all dependencies

set -e  # Exit on error

echo "=========================================="
echo "  Thesis Data Collection System Setup"
echo "=========================================="
echo ""

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "Warning: This script is designed for Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Step 1: Updating system packages..."
sudo apt-get update

echo ""
echo "Step 2: Installing MQTT broker (Mosquitto)..."
sudo apt-get install -y mosquitto mosquitto-clients

echo ""
echo "Step 3: Installing Python dependencies..."
sudo apt-get install -y python3-pip python3-rpi.gpio python3-picamera2

echo ""
echo "Step 4: Installing Python MQTT client..."
pip3 install paho-mqtt --break-system-packages

echo ""
echo "Step 5: Enabling Mosquitto service..."
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
echo "✓ Mosquitto broker running"

echo ""
echo "Step 6: Testing MQTT broker..."
if mosquitto_pub -h localhost -t "test" -m "test" 2>/dev/null; then
    echo "✓ MQTT broker is working"
else
    echo "✗ MQTT broker test failed"
    exit 1
fi

echo ""
echo "Step 7: Creating project directories..."
mkdir -p ~/thesis_data/sensor_data
mkdir -p ~/thesis_data/images
echo "✓ Directories created"

echo ""
echo "Step 8: Installing systemd service..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
sudo cp "$SCRIPT_DIR/../services/thesis-data-collector.service" /etc/systemd/system/
sudo systemctl daemon-reload
echo "✓ Service installed"

echo ""
echo "Step 9: Enabling data collector service..."
sudo systemctl enable thesis-data-collector.service
echo "✓ Service will start on boot"

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start the service: sudo systemctl start thesis-data-collector"
echo "2. Check status: sudo systemctl status thesis-data-collector"
echo "3. View logs: journalctl -u thesis-data-collector -f"
echo ""
echo "Data will be saved to:"
echo "  - Sensor data: ~/thesis_data/sensor_data/"
echo "  - Images: ~/thesis_data/images/"
echo "  - Logs: ~/thesis_data/data_collector.log"
echo ""
echo "To enable auto-login, run: ./setup_autologin.sh"
echo ""
