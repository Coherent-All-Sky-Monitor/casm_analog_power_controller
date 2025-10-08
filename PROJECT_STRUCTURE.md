# Project Structure

## Two Main Folders

```
casm_analog_power_controller/
│
├── 🔴 hardware/                    ← REAL HARDWARE (Raspberry Pi)
│   ├── __init__.py                ← Flask app with SM16relind
│   ├── templates/
│   │   └── index.html             ← Hardware controller UI
│   └── static/
│       └── style.css              ← Styles
│
├── 🟢 simulation/                  ← TESTING (No hardware needed)
│   ├── __init__.py                ← Flask app with fake relays
│   ├── templates/
│   │   └── index.html             ← Simulator UI
│   └── static/
│       └── style.css              ← Styles
│
├── 📄 run_hardware.py             ← Run this on Raspberry Pi
├── 📄 run_simulation.py           ← Run this for testing
├── 📄 requirements.txt            ← Dependencies to install
├── 📄 README.md                   ← Full documentation
└── 📁 16relind-rpi/               ← Hardware library (ignore this)
```

---

## HOW TO USE

### For SIMULATION (No Hardware):
```bash
python3 run_simulation.py
```
This runs the **simulation/** folder

### For HARDWARE (Raspberry Pi):
```bash
python3 run_hardware.py
```
This runs the **hardware/** folder

---

## Key Difference

**hardware/__init__.py:**
- Uses `import lib16relind as SM16relind`
- Controls real relay boards
- Reads/writes to physical hardware

**simulation/__init__.py:**
- Uses Python dictionary for fake relay states
- No hardware needed



