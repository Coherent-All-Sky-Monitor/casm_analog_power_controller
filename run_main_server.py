#!/usr/bin/env python3
"""
Startup script for CASM Analog Power Controller (Main Server)

This script runs the main Flask server that routes requests to individual
Raspberry Pis. This server does NOT control hardware directly - it acts
as a coordinator and unified interface.
"""

from main_server import create_app, CONFIG, RASPBERRY_PIS

if __name__ == '__main__':
    app = create_app()
    
    print("=" * 60)
    print("🚀 CASM Analog Power Controller - MAIN SERVER")
    print("=" * 60)
    print("📡 Server running on: http://0.0.0.0:5000")
    print("🌐 Access locally at: http://localhost:5000")
    print(f"🔌 Configured Raspberry Pis: {len(RASPBERRY_PIS)}")
    print()
    
    for pi_id, pi_data in RASPBERRY_PIS.items():
        ip = pi_data.get('ip_address')
        port = pi_data.get('port', 5001)
        chassis = pi_data.get('chassis', [])
        print(f"   • {pi_id}: {ip}:{port} -> Chassis {chassis}")
    
    print()
    print("⚡ This server routes requests to individual Pis")
    print("🔍 Status monitoring enabled")
    print("=" * 60)
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )

