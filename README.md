# CASM Analog Power Controller

A Flask-based web application for controlling Sequent Microsystems 16-relay boards on Raspberry Pi.

## 🎯 Project Structure

```
casm_analog_power_controller/
├── hardware/                     # Production code (Hardware control)
│   ├── __init__.py              # Flask app with SM16relind integration
│   ├── templates/
│   │   └── index.html           # Hardware controller UI
│   └── static/
│       └── style.css            # Styling
│
├── simulation/                   # Simulation code (Testing without hardware)
│   ├── __init__.py              # Flask app with simulated relays
│   ├── templates/
│   │   └── index.html           # Simulator UI
│   └── static/
│       └── style.css            # Styling
│
├── 16relind-rpi/                # Cloned hardware library repository
├── run_hardware.py              # Startup script for hardware mode
├── run_simulation.py            # Startup script for simulation mode
├── requirements.txt             # Python dependencies
├── START_HERE.md                # Quick start guide
├── PROJECT_STRUCTURE.md         # Detailed structure info
└── README.md                    # This file
```

## 🔧 Hardware Configuration

### Relay Boards
- **Device**: Sequent Microsystems 16-Relay Stackable HAT
- **Total Setup**: 6 stacks × 16 relays = 96 total relays
- **Stack Levels**: 0-5 (configured via jumpers on each board)
- **I2C Port**: 1 (Raspberry Pi default)

### Library Information
- **Library**: SM16relind (lib16relind)
- **Version**: 1.0.4
- **Repository**: https://github.com/SequentMicrosystems/16relind-rpi

## 📦 Installation

### Prerequisites
```bash
# On Raspberry Pi, ensure I2C is enabled
sudo raspi-config
# Navigate to: Interface Options -> I2C -> Enable
```

### Install Dependencies
```bash
# Install Python packages
pip install -r requirements.txt

# Clone and install hardware library (already done)
git clone https://github.com/SequentMicrosystems/16relind-rpi.git
cd 16relind-rpi/python
sudo python3 setup.py install
```

## 🚀 Running the Application

### Production Mode (With Hardware)
```bash
# Run the hardware controller
python3 run_hardware.py
# OR
python -m flask --app hardware run --host=0.0.0.0 --port=5001
```

### Simulation Mode (Without Hardware)
```bash
# Run the simulator for testing
python3 run_simulation.py
# OR
python -m flask --app simulation run --host=0.0.0.0 --port=5001
```

Access the web interface at: `http://localhost:5001` or `http://<raspberry-pi-ip>:5001`

## 📡 API Endpoints

### Get Single Relay State
```bash
GET /api/relay/<stack>/<relay>

# Example: Get state of Stack 0, Relay 1
curl http://localhost:5001/api/relay/0/1

# Response:
{
  "stack": 0,
  "relay": 1,
  "state": 1,
  "status": "ON"
}
```

### Set Single Relay State
```bash
POST /api/relay/<stack>/<relay>
Content-Type: application/json
Body: {"state": 0 or 1}

# Example: Turn ON Stack 0, Relay 1
curl -X POST http://localhost:5001/api/relay/0/1 \
  -H "Content-Type: application/json" \
  -d '{"state": 1}'

# Example: Turn OFF Stack 0, Relay 1
curl -X POST http://localhost:5001/api/relay/0/1 \
  -H "Content-Type: application/json" \
  -d '{"state": 0}'
```

### Get All Relays State
```bash
GET /api/relay/all

# Example:
curl http://localhost:5001/api/relay/all

# Response:
{
  "stack_0": [0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  "stack_1": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  ...
}
```

### Get Single Stack State
```bash
GET /api/relay/stack/<stack>

# Example: Get all relays in Stack 0
curl http://localhost:5001/api/relay/stack/0

# Response:
{
  "stack": 0,
  "relays": [0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
}
```

### Reset All Relays
```bash
POST /api/relay/reset

# Example: Turn OFF all relays
curl -X POST http://localhost:5001/api/relay/reset \
  -H "Content-Type: application/json"
```

### Health Check
```bash
GET /api/health

# Example: Check hardware connection status
curl http://localhost:5001/api/health

# Response:
{
  "status": "ok",
  "stacks": {
    "stack_0": "connected",
    "stack_1": "connected",
    ...
  }
}
```

## 🔌 Hardware Details

### SM16relind Class Methods

#### Initialize Card
```python
import lib16relind as SM16relind
card = SM16relind.SM16relind(stack=0, i2c=1)
```

#### Set Single Relay
```python
card.set(relay, val)
# relay: 1-16
# val: 0 (OFF) or 1 (ON)
```

#### Get Single Relay State
```python
state = card.get(relay)
# Returns: 0 or 1
```

#### Set All Relays (Bitmap)
```python
card.set_all(val)
# val: 16-bit bitmap (0 = all off, 65535 = all on)
```

#### Get All Relays (Bitmap)
```python
bitmap = card.get_all()
# Returns: 16-bit bitmap [0..65535]
```

## 🎨 Features

### Web Interface
- ✅ Real-time relay state visualization
- ✅ Click-to-toggle relay control
- ✅ Auto-refresh every 2 seconds
- ✅ Health status monitoring
- ✅ Reset all relays button
- ✅ Modern, responsive UI

### Error Handling
- Hardware connection failures
- Invalid stack/relay numbers
- I2C communication errors
- Graceful degradation

## 🧪 Development

### Testing Without Hardware
Use the simulation mode to develop and test the API without physical hardware:
```bash
python3 run_simulation.py
```

### Debugging
```bash
# Both run_hardware.py and run_simulation.py have debug=True enabled
# Just run them normally for debug mode
python3 run_simulation.py
```

## 📝 Notes

- **Stack Numbers**: 0-5 (configured via hardware jumpers)
- **Relay Numbers**: 1-16 (API uses 1-based indexing)
- **Bitmap Encoding**: LSB = Relay 1, MSB = Relay 16
- **I2C Address**: Automatically calculated from stack level

## 🔐 Security Considerations

When deploying to production:
1. Use a reverse proxy (nginx/Apache)
2. Add authentication middleware
3. Enable HTTPS
4. Restrict network access
5. Use environment variables for configuration

## 📚 Additional Resources

- [SM16relind GitHub Repository](https://github.com/SequentMicrosystems/16relind-rpi)
- [Sequent Microsystems Documentation](https://sequentmicrosystems.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)

## 📄 License

See LICENSE file for details.
