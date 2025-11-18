# Offline Pi Deployment Guide (RFI-Safe Environment)

## Overview

This system ensures **100% offline Pi deployment** using pre-downloaded packages that match the Docker main server exactly. No WiFi needed!

## Workflow

### 1️⃣ On Your Laptop (One-Time Export)

```bash
cd ~/Desktop/casm_analog_power_controller

# Export all Python packages (same versions as Docker)
./export_packages.sh
```

**What this does:**
- Downloads ~20 Python .whl files from PyPI
- Saves to `pi_packages/` directory
- Uses **exact same versions** as Docker container
- Total size: ~15-20 MB

**Output:**
```
pi_packages/
  ├── Flask-3.0.3-py3-none-any.whl
  ├── Werkzeug-3.0.3-py3-none-any.whl
  ├── PyYAML-6.0.1-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl
  ├── requests-2.31.0-py3-none-any.whl
  ├── SM8relind-...whl
  ├── smbus2-...whl
  └── ... (all dependencies)
```

### 2️⃣ Transfer to Pi via Ethernet SCP

**For each Pi (no WiFi - RFI protection!):**

```bash
# Pi 1 (192.168.1.100)
scp -r casm_analog_power_controller casm@192.168.1.100:~/
scp -r pi_packages casm@192.168.1.100:~/

# Pi 2 (192.168.1.101)
scp -r casm_analog_power_controller casm@192.168.1.101:~/
scp -r pi_packages casm@192.168.1.101:~/
```

### 3️⃣ On Each Pi (Offline Installation)

```bash
# SSH to Pi
ssh casm@192.168.1.100

# Run offline setup
cd casm_analog_power_controller
./setup_pi_offline.sh
```

**What this does:**
- ✅ Checks Python version (3.9+)
- ✅ Checks I2C interface
- ✅ Creates isolated Python venv
- ✅ Installs from `~/pi_packages/` (no internet!)
- ✅ Auto-detects Pi config from `main_config.yaml`
- ✅ Tests for relay HATs

**Key command used:**
```bash
pip install --no-index --find-links ~/pi_packages -r requirements.txt
```
- `--no-index`: Don't use PyPI (no internet)
- `--find-links ~/pi_packages`: Use local files only

### 4️⃣ Start Pi Server

```bash
./start_pi_server.sh
```

Done! Pi is running with **exact same packages as Docker main server**.

---

## Benefits

| Feature | Benefit |
|---------|---------|
| 🔒 **No WiFi Required** | RFI-safe for radio telescope |
| 📦 **Same as Docker** | Perfect version consistency |
| ⚡ **Fast Install** | No slow downloads |
| 🛡️ **Reliable** | No network failures |
| 🔧 **Isolated venv** | No system conflicts |
| 📋 **Version Locked** | Reproducible deployment |

---

## Troubleshooting

### "Package not found" error

If you see:
```
ERROR: Could not find a version that satisfies the requirement ...
```

**Solution:** Re-export packages on laptop:
```bash
cd ~/Desktop/casm_analog_power_controller
rm -rf pi_packages
./export_packages.sh
scp -r pi_packages casm@192.168.1.100:~/
```

### Missing `pi_packages/` directory

```bash
# On Pi, check if packages exist
ls -lh ~/pi_packages/

# If missing, transfer from laptop again
```

### Wrong Python version

```bash
# Check Python version on Pi
python3 --version

# Must be 3.9 or higher
# Upgrade if needed:
sudo apt update
sudo apt install python3.11 python3.11-venv
```

---

## Package Versions (Docker Container Match)

All packages match `requirements.txt` and Docker container:

```
flask==3.0.3
werkzeug==3.0.3
pyyaml==6.0.1
requests==2.31.0
SM8relind
smbus2
```

Plus all dependencies:
- Jinja2
- MarkupSafe
- click
- blinker
- itsdangerous
- certifi
- charset-normalizer
- idna
- urllib3

**Total:** ~20 packages, ~15-20 MB

---

## Alternative: Online Setup (if WiFi available)

If you have WiFi available (non-RFI environment), you can use the regular setup:

```bash
# On Pi with internet
cd casm_analog_power_controller
./setup_pi.sh
```

This will download packages directly from PyPI.

---

## Files

- `export_packages.sh` - Export packages on laptop
- `setup_pi_offline.sh` - Install from offline cache on Pi
- `setup_pi.sh` - Online setup (requires internet)
- `start_pi_server.sh` - Start server with venv
- `pi_packages/` - Offline package cache (gitignored)

