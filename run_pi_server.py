#!/usr/bin/env python3
"""
Startup script for CASM Analog Power Controller (Hardware Mode)

This script runs the Flask application with hardware control for the
Sequent Microsystems 16-relay boards.
"""

from hardware import create_app

if __name__ == '__main__':
    app = create_app()
    print("=" * 60)
    print("CASM Analog Power Controller - HARDWARE MODE")
    print("=" * 60)
    print("Server running on: http://0.0.0.0:5001")
    print("Access locally at: http://localhost:5001")
    print("Controlling 1 board × 8 relays = 8 total relays")
    print("CONNECTED TO REAL HARDWARE (8-relay boards)")
    print("Deployment: 2 Pis × 3 HATs each (6 HATs total)")
    print("=" * 60)
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True
    )
