# 📦 Installation Guide - 8-Relay Boards

## ✅ What Changed:

Switched from **16-relay boards** to **8-relay boards**

- **Before:** 6 stacks × 16 relays = 96 total
- **Now:** 6 stacks × 8 relays = 48 total
- **Currently testing:** 1 board = 8 relays

---

## 🔧 Installation Steps

### 1. Install Python Dependencies

```bash
# Make sure you're in the casm_power conda environment
conda activate casm_power

# Install requirements
pip install -r requirements.txt
```

This will install:
- `Flask` - Web framework
- `Werkzeug` - WSGI utilities
- `SM8relind` - Sequent Microsystems 8-relay library
- `smbus2` - I2C communication

---

### 2. Install Hardware Library (On Raspberry Pi Only)

```bash
# Clone the 8-relay library
git clone https://github.com/SequentMicrosystems/8relind-rpi.git
cd 8relind-rpi/python

# Install the library
sudo python3 setup.py install
```

Reference: https://github.com/SequentMicrosystems/8relind-rpi/tree/main/python

---

## 🧪 Testing on Your Mac/Laptop

Run the **simulation** (no hardware needed):

```bash
conda activate casm_power
python run_simulation.py
```

Then open: **http://localhost:5001**

You'll see:
- 6 stacks × 8 relays each = 48 total relays
- Web UI with clickable relay buttons
- All API endpoints working

---

## ⚡ Running on Raspberry Pi

### Prerequisites:
1. Enable I2C on Raspberry Pi:
   ```bash
   sudo raspi-config
   # → Interface Options → I2C → Enable
   ```

2. Connect your 8-relay board
3. Set stack jumpers to level 0 (your first board)

### Run:
```bash
python run_hardware.py
```

Then access from your phone/computer:
- **Web UI:** `http://raspberrypi-ip:5001`
- **API:** `http://raspberrypi-ip:5001/api/relay/...`

---

## 📡 API Reference (8 Relays)

### Control Single Relay
```bash
# Turn ON Relay 1 on Stack 0
curl -X POST http://localhost:5001/api/relay/0/1 \
  -H "Content-Type: application/json" \
  -d '{"state": 1}'

# Turn OFF
curl -X POST http://localhost:5001/api/relay/0/1 \
  -H "Content-Type: application/json" \
  -d '{"state": 0}'

# Get state
curl http://localhost:5001/api/relay/0/1
```

### Get All States
```bash
curl http://localhost:5001/api/relay/all
```

Response (for 1 board):
```json
{
  "stack_0": [0, 0, 0, 0, 0, 0, 0, 0]
}
```

### Valid Parameters:
- **Stack:** 0 (currently), 0-5 (when you have all 6 boards)
- **Relay:** 1-8 (8 relays per board)
- **State:** 0 (OFF) or 1 (ON)

---

## 📋 When You Get More Boards

Update **3 files**:

### 1. `hardware/__init__.py` (Line 10)
```python
NUM_STACKS = 6  # Change from 1 to 6
```

### 2. `hardware/templates/index.html` (Line 13, 73)
```html
<!-- Line 13 -->
<p class="subtitle">6 Stacks × 8 Relays (48 Total) - Hardware Control</p>

<!-- Line 73 -->
const NUM_STACKS = 6;  // Change from 1 to 6
```

### 3. `run_hardware.py` (Line 18)
```python
print("🔌 Controlling 6 boards × 8 relays = 48 total relays")
```

Set jumpers on each board:
- Board 1 → Stack 0
- Board 2 → Stack 1
- Board 3 → Stack 2
- Board 4 → Stack 3
- Board 5 → Stack 4
- Board 6 → Stack 5

---

## 🎯 Quick Start

1. **Test on Mac:** `python run_simulation.py`
2. **Deploy to Pi:** Copy project, run `python run_hardware.py`
3. **Control from phone:** Open browser to `http://pi-ip:5001`

**All set for 8-relay boards!** 🚀

