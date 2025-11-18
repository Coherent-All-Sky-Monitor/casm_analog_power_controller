#!/bin/bash
# CASM Analog Power Controller - Pi Setup Script
# Run this script on each Raspberry Pi after transferring the repo via SCP

set -e  # Exit on any error

echo "============================================================"
echo "🚀 CASM Analog Power Controller - Pi Setup"
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

# Install dependencies
echo "📦 Installing Python dependencies..."
echo "   (This may take a few minutes on first run)"
echo ""

# Try with --break-system-packages first (for Bookworm)
if pip3 install -r requirements.txt --break-system-packages 2>/dev/null; then
    echo "✅ Dependencies installed successfully"
elif pip3 install -r requirements.txt 2>/dev/null; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Error: Failed to install dependencies"
    echo "   Try manually: pip3 install -r requirements.txt --break-system-packages"
    exit 1
fi
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

# Test hardware (optional)
echo "🔌 Testing relay HAT detection..."
if command -v i2cdetect &> /dev/null; then
    echo "   Scanning I2C bus..."
    HATS_FOUND=$(i2cdetect -y 1 2>/dev/null | grep -E "38|39|3a|3b|3c|3d|3e|3f" | wc -l)
    if [ "$HATS_FOUND" -gt 0 ]; then
        echo "✅ Found $HATS_FOUND relay HAT(s) on I2C bus"
    else
        echo "⚠️  No relay HATs detected (this is OK if not yet connected)"
    fi
else
    echo "⚠️  i2cdetect not found (install with: sudo apt install i2c-tools)"
fi
echo ""

# All done!
echo "============================================================"
echo "✅ Setup complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Verify configuration in main_config.yaml matches this Pi"
echo "  2. Connect relay HATs to I2C bus"
echo "  3. Start the server:"
echo ""
echo "     python3 run_pi_server.py"
echo ""
echo "  4. Or set up as systemd service for auto-start on boot"
echo ""

