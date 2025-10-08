#!/usr/bin/env python3
"""
Startup script for CASM Analog Power Controller (Simulation Mode)

This script runs the Flask application in simulation mode without
requiring physical hardware. Useful for testing and development.
"""

from simulation import create_app

if __name__ == '__main__':
    app = create_app()
    print("=" * 60)
    print("🧪 CASM Analog Power Controller - SIMULATION MODE")
    print("=" * 60)
    print("📡 Server running on: http://0.0.0.0:5001")
    print("🌐 Access locally at: http://localhost:5001")
    print("🔌 Simulating 6 stacks × 8 relays = 48 total relays")
    print("⚠️  NO HARDWARE - This is SIMULATION mode")
    print("=" * 60)
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True
    )
