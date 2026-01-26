#!/bin/bash
# Setup Auto-Login for Raspberry Pi
# This enables the system to boot directly to the desktop without login prompt

set -e

echo "=========================================="
echo "  Raspberry Pi Auto-Login Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo "Please run as normal user (not root/sudo)"
   exit 1
fi

echo "This will configure your Raspberry Pi to auto-login as user: $USER"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "Setting up auto-login..."

# Method 1: Using raspi-config (non-interactive)
echo "Configuring auto-login via raspi-config..."
sudo raspi-config nonint do_boot_behaviour B4  # B4 = Desktop with auto-login

echo ""
echo "=========================================="
echo "  Auto-Login Configuration Complete!"
echo "=========================================="
echo ""
echo "The system will now boot directly to the desktop as user: $USER"
echo ""
echo "To revert this change, run:"
echo "  sudo raspi-config"
echo "  Select: System Options -> Boot / Auto Login -> Desktop (requires login)"
echo ""
echo "Please reboot for changes to take effect:"
echo "  sudo reboot"
echo ""
