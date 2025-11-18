#!/bin/bash
# Export Python packages from Docker container for offline Pi installation

set -e

echo "============================================================"
echo "📦 Exporting Python packages for offline Pi installation"
echo "============================================================"
echo ""

# Check if Docker is running
if ! docker ps &> /dev/null; then
    echo "❌ Error: Docker is not running"
    echo "   Start Docker Desktop and try again"
    exit 1
fi

# Create packages directory
mkdir -p pi_packages
rm -rf pi_packages/*

echo "📥 Downloading all required packages and dependencies..."
echo ""

# Download all packages to local directory
pip3 download \
    -d pi_packages \
    flask==3.0.3 \
    werkzeug==3.0.3 \
    pyyaml==6.0.1 \
    requests==2.31.0 \
    SM8relind \
    smbus2

echo ""
echo "✅ Packages exported to: pi_packages/"
echo ""
echo "Package count: $(ls -1 pi_packages | wc -l)"
echo "Total size: $(du -sh pi_packages | cut -f1)"
echo ""
echo "============================================================"
echo "Next steps:"
echo "============================================================"
echo ""
echo "1. Transfer packages to Pi:"
echo "   scp -r pi_packages casm@192.168.1.2:~/"
echo ""
echo "2. On Pi, install from local packages:"
echo "   cd ~/casm_analog_power_controller"
echo "   ./setup_pi_offline.sh"
echo ""

