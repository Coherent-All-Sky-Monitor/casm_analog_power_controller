#!/bin/bash
# CASM Analog Power Controller - Pi Server Startup Script
# Automatically activates virtual environment and starts the server

set -e

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found"
    echo "   Run ./setup_pi.sh first to set up the environment"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Start the server
echo "Starting Pi server..."
echo ""
python3 run_pi_server.py

