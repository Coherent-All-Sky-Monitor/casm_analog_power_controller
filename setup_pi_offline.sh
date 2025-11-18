#!/bin/bash
# CASM Analog Power Controller - Pi Offline Setup Script
# Run this script on Pi after transferring packages via export_packages.sh

set -e

echo "============================================================"
echo "🚀 CASM Analog Power Controller - Pi Offline Setup"
echo "============================================================"
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Python version
echo "📋 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Python $REQUIRED_VERSION or higher required (found $PYTHON_VERSION)"
    exit 1
fi
echo "✅ Python $PYTHON_VERSION detected"
echo ""

# Check if I2C is enabled
echo "📋 Checking I2C interface..."
if ! ls /dev/i2c-* 1> /dev/null 2>&1; then
    echo "⚠️  Warning: I2C interface not detected"
    echo "   Enable it with: sudo raspi-config → Interface Options → I2C"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ I2C interface detected"
fi
echo ""

# Check if packages directory exists
if [ ! -d "$HOME/pi_packages" ]; then
    echo "❌ Error: Package directory not found: ~/pi_packages"
    echo ""
    echo "Please run these commands on your laptop first:"
    echo "  1. cd ~/Desktop/casm_analog_power_controller"
    echo "  2. ./export_packages.sh"
    echo "  3. scp -r pi_packages casm@192.168.1.2:~/"
    echo ""
    exit 1
fi

echo "✅ Found offline package cache: ~/pi_packages"
echo "   Package count: $(ls -1 ~/pi_packages | wc -l)"
echo ""

# Create virtual environment
echo "📦 Setting up Python virtual environment..."
if [ -d "venv" ]; then
    echo "   Virtual environment already exists, using existing one"
else
    echo "   Creating new virtual environment..."
    if ! python3 -m venv venv; then
        echo "❌ Error: Failed to create virtual environment"
        echo "   Install venv with: sudo apt install python3-venv"
        exit 1
    fi
    echo "✅ Virtual environment created"
fi
echo ""

# Activate virtual environment and install from local packages
echo "📦 Installing Python dependencies from offline cache..."
echo "   (Installing from local files - no internet needed!)"
echo ""

source venv/bin/activate
if pip install --no-index --find-links ~/pi_packages -r requirements.txt; then
    echo "✅ Dependencies installed successfully from offline cache"
else
    echo "❌ Error: Failed to install dependencies"
    deactivate
    exit 1
fi
deactivate
echo ""

# Detect Pi configuration
echo "🔍 Detecting Pi configuration..."
PI_IP=$(hostname -I | awk '{print $1}')
echo "   Detected IP: $PI_IP"

# Check if IP is in main_config.yaml
if grep -q "$PI_IP" main_config.yaml; then
    PI_ID=$(grep -B 1 "$PI_IP" main_config.yaml | grep -E "^\s+pi_[0-9]:" | sed 's/://g' | xargs)
    echo "✅ Found configuration: $PI_ID"
else
    echo "⚠️  Warning: IP $PI_IP not found in main_config.yaml"
    echo "   Make sure to update main_config.yaml with this Pi's IP"
fi
echo ""

# All done!
echo "============================================================"
echo "✅ Offline setup complete!"
echo "============================================================"
echo ""
echo "✅ All packages installed from local cache (no internet used)"
echo "✅ Virtual environment ready"
echo "✅ Same packages as Docker main server (100% consistent)"
echo ""
echo "Next steps:"
echo "  1. Connect relay HATs to I2C bus"
echo "  2. Start the server:"
echo ""
echo "     ./start_pi_server.sh"
echo ""
echo "  3. Or manually:"
echo ""
echo "     source venv/bin/activate"
echo "     python3 run_pi_server.py"
echo ""

