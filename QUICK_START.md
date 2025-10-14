# Quick Start Guide - Switch Mapping System

## 🎯 What Changed?

You can now control relays using **logical names** instead of stack/relay numbers!

## 🔌 Your Prototype Setup (2 Boards)

### Current Wiring Map

**Board 1 (Stack 0):**
- Relay 1 → **CH1** (Chassis 1)
- Relay 2 → CH1A
- Relay 3 → CH1B
- Relay 4 → CH1C
- Relay 5 → CH1D
- Relay 6 → CH1E
- Relay 7 → CH1F
- Relay 8 → CH1G

**Board 2 (Stack 1):**
- Relay 1 → CH1H
- Relay 2 → CH1I
- Relay 3 → CH1J
- Relay 4 → CH1K
- Relay 5 → **CH2** (Chassis 2) [Optional - not wired yet]
- Relay 6 → CH2A [Optional]
- Relay 7 → CH2B [Optional]
- Relay 8 → CH2C [Optional]

## 🚀 Quick Usage Examples

### Using curl

```bash
# Turn CH1 chassis ON
curl -X POST http://localhost:5001/api/switch/CH1 -H "Content-Type: application/json" -d '{"state": 1}'

# Turn CH1A backboard OFF
curl -X POST http://localhost:5001/api/switch/CH1A -H "Content-Type: application/json" -d '{"state": 0}'

# Get status of CH1
curl http://localhost:5001/api/switch/CH1

# Get all CH1 switches (chassis + backboards)
curl http://localhost:5001/api/switch/chassis/1
```

### Web Interface

1. Start the server: `python3 run_hardware.py`
2. Open browser: `http://localhost:5001`
3. You'll see:
   - **Chassis Control** section with CH1 button
   - **Backboard Controls** section with CH1A-K buttons
   - **API Examples** at the bottom with curl commands

## 📋 API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/switch/CH1` | GET | Get switch status |
| `/api/switch/CH1` | POST | Set switch state (body: `{"state": 0 or 1}`) |
| `/api/switch/chassis/1` | GET | Get all chassis 1 switches |
| `/api/switch/list` | GET | List all available switches |
| `/api/relay/0/1` | GET/POST | Legacy API (still works) |

## 🔧 When You Get More Boards

The system is already configured for the full 6-board setup:

- **6 boards** = 48 relays total
- **47 switches** mapped:
  - 4 chassis (CH1-4)
  - 43 backboards (CH1A-K, CH2A-K, CH3A-K, CH4A-J)
  - 1 spare relay

Just update `NUM_STACKS = 6` in `/hardware/__init__.py` when ready!

## 📖 More Details

See `SWITCH_MAPPING_GUIDE.md` for complete documentation.

