#!/bin/bash
# CASM Analog Power Controller - Pi Setup Script
# Run this on Pi with internet connection (shared from laptop via Ethernet)

set -e

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

# Check internet connectivity
echo "📋 Checking internet connection..."
if ! ping -c 1 -W 2 pypi.org &> /dev/null; then
    echo "⚠️  Warning: Cannot reach PyPI (pypi.org)"
    echo ""
    echo "Make sure your laptop is sharing internet via Ethernet:"
    echo "  1. On macOS: System Settings → Sharing → Internet Sharing"
    echo "     Share: Wi-Fi, To computers using: Ethernet"
    echo "  2. On Pi, check internet: ping pypi.org"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Internet connection detected"
fi
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

# Activate virtual environment and install from PyPI
echo "📦 Installing Python dependencies from PyPI..."
echo "   (This will download packages from the internet)"
echo ""

source venv/bin/activate
if pip install -r requirements.txt; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Error: Failed to install dependencies"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check internet: ping pypi.org"
    echo "  2. Check DNS: cat /etc/resolv.conf"
    echo "  3. Try manual install: pip install flask"
    echo ""
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
echo "✅ Setup complete!"
echo "============================================================"
echo ""
echo "✅ Virtual environment ready"
echo "✅ All dependencies installed"
echo "✅ Same package versions as Docker main server"
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
