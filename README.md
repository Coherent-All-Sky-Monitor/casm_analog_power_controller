# CASM Analog Power Controller

A Flask-based HTTP request system for controlling power to the CASM analog chain through Sequent Microsystems 8-relay boards on Raspberry Pis.

## System Overview

**Two Stages:**
- **Main Server** - Routes requests to appropriate Pi (port 5000)
- **Raspberry Pis** - Control physical relay boards (port 5001 each)

**Hardware:**
- 47 switches total: CH1-4 (power over full chassis) + CH1A-K, CH2A-K, CH3A-K, CH4A-J (individual SNAPs)
- Sequent Microsystems 8-relay HAT boards
- **Deployment:** 2 Raspberry Pis, each with 3 relay boards
  - Pi 1: Controls Chassis 1 & 2 (3 boards)
  - Pi 2: Controls Chassis 3 & 4 (3 boards)

---

## Quick Start with Command Line Tool: CASM Analog Power Controller (CAPC) CLI

The easiest way to control switches is with the `capc` command-line tool:

```bash
# Make it accessible system-wide (optional) so you don't have to be in the project directory.
sudo cp capc /usr/local/bin/
sudo chmod +x /usr/local/bin/capc

# Or use directly from the CASM_ANALOG_POWER_CONTROLLER repo
./capc --help

# 4 Main Example Workflows:
./capc -n CH1A --on              # 1. Main server + switch name (-n tag for name)
./capc -s 1 -r 7 --on            # 2. Main server + HAT/relay number (-s tag for HAT) (-r tag for relay)
./capc -n CH1A --on -d           # 3. Pi direct + switch name
./capc -s 1 -r 7 --on -d         # 4. Pi direct + HAT/relay number

# Get info
./capc --status                  # System status
./capc --list                    # List all switches
./capc -n CH1A                   # Get switch status
```

**Main reasons to use `capc` instead of curl commands?**
- Simpler syntax
- Auto-detects which Pi controls which switch

---

## SETUP: After Configuration of RPIs Including Static IPs, Disabling Bluetooth/WIFI, Username, Hardware Watchdog, etc.

### Step 1: Edit `main_config.yaml`

**Main Config Sets Up Full Configuration Across Main Server and Pis:**

```bash
# On your laptop
cd casm_analog_power_controller

# Edit main_config.yaml
nano main_config.yaml
```

**What to edit:**
- **Pi IP addresses** (`ip_address`) - must match static IPs set on Pis
- **Hardware specs** (`num_relay_hats`, `relays_per_hat`) per Pi (default is 3 HATs per pi with 8 relays per HAT)
- **Switch mappings** (`switch_mapping` section) for each Pi
  - Customize `{hat: X, relay: Y}` based on actual wiring

```bash
# Commit and push to GitHub
git add main_config.yaml
git commit -m "Configure system for deployment"
git push origin main
```

### Step 2: Deploy to Raspberry Pis

**Same steps for ALL Pis - they auto-configure based on Static IP!**

> **Note:** The Pis use username `casm` (not the default `pi`). Make sure both Pis have the same username for consistency.

> **Important:** Pis have WiFi/Bluetooth hardware **disabled** to prevent Radio Frequency Interference (RFI) with the radio telescope. WiFi is temporarily enabled ONLY for initial setup (to install dependencies), then hardware-disabled via `config.txt` before deployment.

#### Static IP Configuration

**Development (Your Laptop):**
- Pi 1: `192.168.2.2` (hardcoded static IP)
- Pi 2: `192.168.2.3` (hardcoded static IP)
- Use macOS Internet Sharing (automatically uses 192.168.2.x subnet)

**Configure Static IPs on Pis:**
```bash
# On each Pi, edit network config:
sudo nano /etc/dhcpcd.conf

# Add at the end (use 'end0' for RPi 5, 'eth0' for older models):
interface end0
static ip_address=192.168.2.2/24  # Use .3 for Pi 2
static routers=192.168.2.1
static domain_name_servers=8.8.8.8 8.8.4.4

# Save and reboot
sudo reboot
```

**Production (OVRO) - IMPORTANT:**

Before deploying to OVRO, coordinate with network administrators:

1. **Determine IP Subnet:** Ask what subnet to use (e.g., `10.0.5.x`)

2. **Get Pi MAC Addresses:**
   ```bash
   # On each Pi (use 'end0' for RPi 5, 'eth0' for older models):
   ip link show end0 | grep ether
   # Example output: link/ether dc:a6:32:ab:cd:ef
   ```

3. **Choose Static IPs:** Pick IPs in their subnet specific to OVRO (e.g., `10.0.5.100`, `10.0.5.101`)

4. **Update Pi Static IPs:**
   ```bash
   # On each Pi, edit /etc/dhcpcd.conf (use 'end0' for RPi 5, 'eth0' for older):
   interface end0
   static ip_address=10.0.5.100/24  # Or .101 for Pi 2
   static routers=10.0.5.1  # Gateway provided by OVRO
   static domain_name_servers=8.8.8.8 8.8.4.4
   ```

5. **Request DHCP Reservations (CRITICAL):**
   
   Email OVRO network admins:
   ```
   Subject: DHCP Reservation Request for CASM Raspberry Pis
   
   Please configure DHCP reservations to prevent IP conflicts:
   
   - Pi 1:
     MAC Address: dc:a6:32:ab:cd:ef
     Reserved IP: 10.0.5.100
     Hostname: casm-pi1
   
   - Pi 2:
     MAC Address: aa:bb:cc:dd:ee:ff
     Reserved IP: 10.0.5.101
     Hostname: casm-pi2
   
   This ensures the Pis maintain consistent IPs for our auto-configuration system.
   ```

**Why Both Static IP + DHCP Reservation?**
- **Redundancy:** If DHCP fails, Pi keeps its IP
- **No Conflicts:** DHCP won't assign these IPs to other devices
- **Standard Practice:** Industry-standard approach for critical infrastructure
- **Auto-Configuration:** Pis identify themselves via IP in `main_config.yaml`

#### Initial Setup (ONE TIME per Pi)

**Workflow:** Pi needs temporary internet for setup, then WiFi/Bluetooth are disabled to prevent RFI.

```bash
# 1. Temporarily enable WiFi on Pi to download dependencies
#    (Can be disabled after installation)
#    Connect Pi to WiFi network temporarily

# 2. SSH to Pi (via WiFi or Ethernet)
ssh casm@<pi-ip>

# 3. Clone repository
git clone https://github.com/Coherent-All-Sky-Monitor/casm_analog_power_controller.git
cd casm_analog_power_controller

# 4. Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate

# 5. Install dependencies (requires internet)
pip3 install -r requirements.txt

# 6. Disable WiFi and Bluetooth (REQUIRED for RFI prevention)
sudo nano /boot/firmware/config.txt
# Add these lines at the end:
#   dtoverlay=disable-wifi
#   dtoverlay=disable-bt
# Save and reboot: sudo reboot

# 7. After reboot, connect via Ethernet and start the server
ssh casm@192.168.2.2  # Use static IP from Step 2
cd casm_analog_power_controller
source venv/bin/activate  # If using venv
python3 run_hardware.py
```

**Summary:**
1. ✅ Pi starts with internet (WiFi enabled temporarily)
2. ✅ Clone repo and install dependencies in virtual environment
3. ✅ Disable WiFi/Bluetooth hardware to prevent RFI
4. ✅ Connect via Ethernet (static IP) and run code

#### Future Updates

**Option A: Git Pull (requires internet over Ethernet)**

If you have internet sharing enabled from laptop to Pi via Ethernet:

```bash
# SSH to Pi via Ethernet
ssh casm@192.168.2.2
cd casm_analog_power_controller
source venv/bin/activate  # If using venv

# Pull latest changes (via laptop's shared internet)
git pull

# Restart server (Ctrl+C to stop, then restart)
python3 run_hardware.py
```

**Option B: SCP Transfer (no internet needed)**

Transfer updated files from laptop:

```bash
# On laptop: Transfer updated files
cd ~/Desktop/casm_analog_power_controller
tar --exclude='.git' --exclude='venv' --exclude='__pycache__' \
    -czf casm_update.tar.gz .
scp casm_update.tar.gz casm@192.168.2.2:~/casm_analog_power_controller/

# On Pi: Extract and restart
ssh casm@192.168.2.2
cd casm_analog_power_controller
tar -xzf casm_update.tar.gz
source venv/bin/activate  # If using venv
python3 run_hardware.py
```

**Pi Auto-Configuration:**

The Pi automatically:
- Detects its IP address
- Finds its section in `main_config.yaml`
- Loads hardware specs and switch mappings
- Starts server on port 5001

### Step 4: Start Main Server (Docker)

**Prerequisites:**
- Docker installed ([Install Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (usually comes with Docker Desktop)

```bash
# On main server
cd casm_analog_power_controller

# Create data directory for database persistence
mkdir -p data

# Start main server with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f

# Check status
curl http://localhost:5000/api/status
```

**Docker Commands:**
```bash
# Stop server
docker-compose down

# Restart server
docker-compose restart

# Update after code changes
git pull
docker-compose down
docker-compose up -d --build

# View logs
docker-compose logs -f main_server
```

### Step 5: Test

```bash
# Check system status
curl http://main-server:5000/api/status

# Testing switch control:
# METHOD 1: Control by switch name via main server (RECOMMENDED)
curl -X POST http://main-server:5000/api/switch/CH1 \
  -H "Content-Type: application/json" \
  -d '{"state": 1}'

# METHOD 2: Control by relay number via main server
curl -X POST http://main-server:5000/api/relay/pi_1/0/1 \
  -H "Content-Type: application/json" \
  -d '{"state": 1}'

# METHOD 3: Control by switch name via Pi directly
curl -X POST http://192.168.1.100:5001/api/switch/CH1 \
  -H "Content-Type: application/json" \
  -d '{"state": 1}'

# METHOD 4: Control by relay number via Pi directly
curl -X POST http://192.168.1.100:5001/api/relay/0/1 \
  -H "Content-Type: application/json" \
  -d '{"state": 1}'

# Or open browser
# http://main-server:5000
```

---

## Configuration File

**ALL configuration is done in `main_config.yaml`** - one file for the whole system.

- Main server reads it to know where Pis are located (IPs/Ports)
- Each Pi reads it and auto-detects its own section based on IP address

### `main_config.yaml`

**Edit based on hardware design and set static IPs:**

```yaml
raspberry_pis:
  pi_1:
    ip_address: "192.168.1.100"
    port: 5001
    chassis: [1, 2]
    description: "Pi 1 - Chassis 1 & 2"
    num_relay_hats: 3
    relays_per_hat: 8
    
    # All switch mappings for Chassis 1 & 2 (customize based on wiring)
    switch_mapping:
      # Chassis 1: 1 Full Chassis + 11 SNAPs
      CH1: {hat: 0, relay: 1}   # Relay 1 on HAT 0
      CH1A: {hat: 0, relay: 2}  # Relay 2 on HAT 0
      CH1B: {hat: 0, relay: 3}  # Relay 3 on HAT 0
      # ... CH1C through CH1K (relays 4-8 on HAT 0, then 1-4 on HAT 1)
      
      # Chassis 2: 1 Full Chassis + 11 SNAPs
      CH2: {hat: 1, relay: 5}   # Relay 5 on HAT 1
      CH2A: {hat: 1, relay: 6}  # Relay 6 on HAT 1
      # ... CH2B through CH2K (relays 7-8 on HAT 1, then 1-8 on HAT 2)
  
  pi_2:
    ip_address: "192.168.1.101"
    port: 5001
    chassis: [3, 4]
    description: "Pi 2 - Chassis 3 & 4"
    num_relay_hats: 3
    relays_per_hat: 8
    
    # All switch mappings for Chassis 3 & 4
    switch_mapping:
      # Chassis 3: 1 Full Chassis + 11 SNAPs
      CH3: {hat: 0, relay: 1}   # Relay 1 on HAT 0
      CH3A: {hat: 0, relay: 2}  # Relay 2 on HAT 0
      # ... CH3B through CH3K (relays 3-8 on HAT 0, then 1-4 on HAT 1)
      
      # Chassis 4: 1 Full Chassis + 10 SNAPs (A-J, no K)
      CH4: {hat: 1, relay: 5}   # Relay 5 on HAT 1
      CH4A: {hat: 1, relay: 6}  # Relay 6 on HAT 1
      # ... CH4B through CH4J (relays 7-8 on HAT 1, then 1-7 on HAT 2)

status_check_interval: 30
request_timeout: 5
```

### How Pis Auto-Configure

**Each Pi automatically finds its configuration:**

1. Pi boots up and detects its own static IP address (e.g., `192.168.1.100`)
2. Pi loads `main_config.yaml` from the repo
3. Pi searches for the entry with matching `ip_address`
4. Pi extracts its configuration:
   - `pi_id` (e.g., `pi_1`)
   - `num_relay_hats`, `relays_per_hat`
   - `switch_mapping` (all switch-to-relay mappings)
5. Pi is fully configured

**Minimal Configuration on Pis** Set static IP and `git pull`.

**Important:** 
- ✅ **All Configuration Happens Through Main** - `main_config.yaml`
- ✅ **HAT numbers** are 0-based (0, 1, 2 for 3 HATs)
- ✅ **Relay numbers** are 1-based (1-8)
- ✅ **Switch mapping is NOT sequential** - must match physical wiring
---

## Usage

### Webpage Front End

Open browser:
- Main server: `http://<main-server-ip>:5000`
- Individual Pi: `http://<pi-ip>:5001`

Click switches to toggle on/off.

### Using the `capc` CLI Tool

The `capc` (CASM Analog Power Controller) command-line tool provides a user-friendly interface to control switches.

**Installation:**
```bash
# Make it accessible system-wide
sudo cp capc /usr/local/bin/
sudo chmod +x /usr/local/bin/capc

# Or use from repo
./capc --help
```

**4 Control Workflows:**

| Mode | Command | Description |
|------|---------|-------------|
| **1** | `capc -n CH1A --on` | Switch name → Main Server |
| **2** | `capc -s 1 -r 7 --on` | HAT/Relay → Main Server |
| **3** | `capc -n CH1A --on -d` | Switch name → Pi Direct |
| **4** | `capc -s 1 -r 7 --on -d` | HAT/Relay → Pi Direct |

**Common Commands:**
```bash
# Control switches by name (RECOMMENDED)
capc -n CH1 --on                # Turn chassis 1 ON (via main server)
capc -n CH1A --off              # Turn BACboard CH1A OFF
capc -n CH2 --on -d             # Turn chassis 2 ON (Pi direct)

# Control by hardware location (HAT/relay)
capc -s 1 -r 7 --on             # HAT 1, Relay 7 ON (via main server)
capc -s 2 -r 3 --off -d         # HAT 2, Relay 3 OFF (Pi direct)

# Get information
capc --status                   # Show system status
capc --list                     # List all switches
capc --list -d                  # List switches from Pi
capc -n CH1A                    # Get status of CH1A

# Direct Pi access (specify IP)
capc -n CH1A --on -d -p 192.168.1.2
```

**How curl Commands Map to capc:**

```bash
# curl → capc
curl -X POST http://localhost:5000/api/switch/CH1A -d '{"state": 1}'
capc -n CH1A --on

curl -X POST http://localhost:5000/api/relay/1/7 -d '{"state": 1}'
capc -s 1 -r 7 --on

curl -X POST http://192.168.1.2:5001/api/switch/CH1A -d '{"state": 1}'
capc -n CH1A --on -d

curl -X POST http://192.168.1.2:5001/api/relay/1/7 -d '{"state": 1}'
capc -s 1 -r 7 --on -d
```

**Why use `capc`?**
- ✅ Simpler syntax (no JSON formatting)
- ✅ Auto-detects which Pi controls which switch
- ✅ Clear success/error messages
- ✅ Less typing than curl
- ✅ Built-in help: `capc --help`

---

### Command Line Using Curl Commands (Legacy)

If you prefer curl or need to integrate with other tools, all functionality is available via REST API.

#### 4 Control Methods

| Method | Target | Control Type | Endpoint Example | 
|--------|--------|--------------|------------------|
| **1** | Main Server | Switch Name | `POST /api/switch/CH1` |
| **2** | Main Server | HAT/Relay | `POST /api/relay/1/7` |
| **3** | Pi Direct | Switch Name | `POST http://pi-ip:5001/api/switch/CH1` |
| **4** | Pi Direct | HAT/Relay | `POST http://pi-ip:5001/api/relay/1/7` |

---

**METHOD 1: Switch Name → Main Server (RECOMMENDED)**
- Uses logical names (CH1, CH1A, etc.)
- Main server handles routing and mapping
- Best for normal operations

**METHOD 2: Relay Number → Main Server**
- Direct hardware control via main server
- Specify Pi ID, HAT, and relay number

**METHOD 3: Switch Name → Pi Directly**
- Bypass main server entirely
- Pi has switch mappings loaded from `main_config.yaml`

**METHOD 4: Relay Number → Pi Directly**
- Bypass main server entirely
- Lowest-level hardware control

**Monitor system:**
```bash
# Check all Pis status
curl http://main-server:5000/api/status

# List all switches
curl http://main-server:5000/api/switch/list

# Get chassis switches
curl http://main-server:5000/api/switch/chassis/1
```

**Direct Pi access (bypasses main server):**
```bash
curl -X POST http://192.168.1.100:5001/api/switch/CH1 -d '{"state": 1}'
```

### Bash Script Example

```bash
#!/bin/bash
MAIN="http://192.168.1.50:5000" # replace 192.158.1.50 with main server's IP address

# Check status before starting
STATUS=$(curl -s $MAIN/api/status)
echo "System status: $STATUS"

# Power up chassis 1
echo "Powering up chassis 1..."
curl -X POST $MAIN/api/switch/CH1 -H "Content-Type: application/json" -d '{"state": 1}'
sleep 1

# Turn on BACboards
for switch in CH1A CH1B CH1C CH1D CH1E; do
    curl -X POST $MAIN/api/switch/$switch -H "Content-Type: application/json" -d '{"state": 1}'
done

echo "Done!"
```

---

## API Reference

### Switch Control With Switch Name
- `POST /api/switch/<name>` - Set switch state (`{"state": 0 or 1}`)
- `GET /api/switch/<name>` - Get switch state
- `GET /api/switch/list` - List all switches
- `GET /api/switch/chassis/<num>` - Get chassis switches (1-4)

### System Monitoring
- `GET /api/status` - System status (all Pis)
- `GET /api/pis` - List all configured Pis

### Switch Control With Relay Number
- `POST /api/relay/<hat>/<relay>` - Set relay (`{"state": 0 or 1}`)
- `GET /api/relay/<hat>/<relay>` - Get relay state
- `GET /api/relay/hat/<hat>` - Get all relays in HAT

**Switch Names:**
- Chassis: `CH1`, `CH2`, `CH3`, `CH4`
- Individual SNAPs and BACboards: `CH1A-K`, `CH2A-K`, `CH3A-K`, `CH4A-J`
- Case-insensitive (`CH1` = `ch1`)

---

## Deployment Architecture

### Two-Pi Deployment (Production Setup)

**Hardware:** 2 Raspberry Pis, each with 3 relay boards (daughterboards)
- Pi #1: Controls Chassis 1 & 2 (3 boards, 24 relays)
- Pi #2: Controls Chassis 3 & 4 (3 boards, 24 relays)

**Main server config (`main_config.yaml`):**
```yaml
raspberry_pis:
  pi_1:
    ip_address: "192.168.1.100"
    port: 5001
    chassis: [1, 2]
    description: "Pi 1 - Chassis 1 & 2"
  
  pi_2:
    ip_address: "192.168.1.101"
    port: 5001
    chassis: [3, 4]
    description: "Pi 2 - Chassis 3 & 4"

status_check_interval: 30
request_timeout: 5
```

**Pi #1 config (`main_config.yaml`):**
```yaml
pi_id: "pi_1"
chassis: [1, 2]
num_relay_hats: 3
relays_per_hat: 8

# Example switch mapping (customize for your wiring!)
switch_mapping:
  CH1: {hat: 0, relay: 0}
  CH1A: {hat: 0, relay: 1}
  CH1B: {hat: 0, relay: 2}
  # ... add all switches for chassis 1 & 2
```

**Pi #2 config (`main_config.yaml`):**
```yaml
pi_id: "pi_2"
chassis: [3, 4]
num_relay_hats: 3
relays_per_hat: 8

switch_mapping:
  CH3: {hat: 0, relay: 0}
  CH3A: {hat: 0, relay: 1}
  CH3B: {hat: 0, relay: 2}
  # ... add all switches for chassis 3 & 4
```

**Why Two Pis:**
- ✅ **Redundancy** - Chassis 1-2 stay operational if Pi 2 fails
- ✅ **Load distribution** - 24 relays per Pi instead of 48
- ✅ **Easier wiring** - Shorter cable runs from Pi to daughterboards
- ✅ **Modular** - Can test/debug one chassis pair at a time

**Important Notes:**
- Each Pi has **static IP** configured via boot script (no DHCP)
- **No internet/WiFi** during operation (RFI protection for radio telescope)
- Switch mappings are **non-sequential** - relay 0 and 7 might control chassis power!

---

## Troubleshooting

### Pi shows as "unreachable"

**Check:**
1. Is Pi powered on and running the server?
2. Can you ping it? `ping 192.168.1.100`
3. Is the IP correct in `main_config.yaml`?
4. Test directly: `curl http://192.168.1.100:5001/api/status`

**Fix:**
- Restart Pi server: `ssh casm@<ip>` then `python3 run_pi_server.py`
- Check network connection
- Verify firewall allows port 5001

### "Invalid switch name" error

**Check:**
1. Spelling correct? (`CH1` not `C1`)
2. Is that Pi configured for that chassis?
3. List valid switches: `curl http://main-server:5000/api/switch/list`

### Wrong relay activates

**Check:**
1. Verify `chassis_controlled` in Pi's `local_config.yaml`
2. Verify `chassis` in main server's `main_config.yaml`
3. They must match!
4. Restart both Pi and main server after config changes

### Main server can't start

**Error:** `Main server config not found`

**Fix:**
```bash
cp main_config.example.yaml main_config.yaml
nano main_config.yaml  # Edit IPs
```

### Pi server can't start

**Error:** `Configuration file not found`

**Fix:**
```bash
# For Pi 1:
cp local_config.example.pi1.yaml local_config.yaml
# For Pi 2:
cp local_config.example.pi2.yaml local_config.yaml

nano local_config.yaml  # Edit chassis and switch mappings
```

**Error:** `'switch_mapping' section is missing or empty`

**Fix:** Add switch mappings to `local_config.yaml`:
```yaml
switch_mapping:
  CH1: {hat: 0, relay: 0}
  CH1A: {hat: 0, relay: 1}
  # ... add all switches
```

**Error:** `Failed to initialize relay boards`

**Fix:**
- Enable I2C: `sudo raspi-config` → Interface Options → I2C
- Check boards connected: `i2cdetect -y 1`
- Verify jumper settings on boards

---

## Auto-Configuration System

The system automatically detects which config file to use based on the Pi's IP address.

### How It Works:

1. **Each Pi has a unique static IP** (configured via boot script)
2. **All Pis have the same repo** with all config files
3. **Pi auto-detects its IP** and loads the correct config file
4. **No copying needed** - just edit the config files directly in the repo

### Config Files in Repo:

```
casm_analog_power_controller/
├── local_config.pi1.yaml  # Pi at 192.168.1.100 uses this
├── local_config.pi2.yaml  # Pi at 192.168.1.101 uses this
└── auto_configure_pi.py   # Helper to show which config to edit
```

### Usage:

```bash
# On any Pi (after cloning the repo)
python3 auto_configure_pi.py

# Output:
# ✅ Detected IP address: 192.168.1.100
# ✅ This Pi should use: local_config.pi1.yaml
# 📝 To customize switch mappings, edit:
#    nano local_config.pi1.yaml
```

### IP-to-Config Mapping:

Both `hardware/__init__.py` and `auto_configure_pi.py` have the same mapping:

```python
IP_TO_CONFIG = {
    "192.168.1.100": "local_config.pi1.yaml",  # Pi 1 → Chassis 1 & 2
    "192.168.1.101": "local_config.pi2.yaml",  # Pi 2 → Chassis 3 & 4
}
```

### Benefits:

✅ **Same repo on all Pis** - No copying, just edit files in place  
✅ **Auto-detection** - Pi automatically loads the right config  
✅ **Version control** - All configs are in git  
✅ **Easy SD card cloning** - Clone one SD card, works on all Pis  
✅ **No duplicate files** - One config file per Pi, not per-Pi copies

---

## Key Features

✅ **Scalable** - 1 to N Pis, add/remove by editing config  
✅ **Unified API** - Same commands regardless of Pi count  
✅ **Status Monitoring** - Know when Pis are down  
✅ **Flexible** - Any chassis distribution  
✅ **Web + CLI** - Browser UI or curl commands  
✅ **Pi Agnostic** - Same code on all Pis  
✅ **Auto-Configuration** - Pis detect their role based on IP

---

## Important Notes

- **Use static IPs** for Pis
- **Username consistency**: Both Pis should use username `casm` (not default `pi`) for easier management
- **Check status** before experiments
- **Configs must match** between main server and Pis
- **HAT numbers are local** on each Pi (always start at 0)
- **Each chassis** can only be controlled by ONE Pi

### Setting Up Username on Second Pi

If your second Pi still uses the default `pi` username, change it to `casm`:

```bash
# SSH to the second Pi
ssh pi@192.168.1.101  # or whatever the current username is

# Create new user 'casm'
sudo adduser casm
# Follow prompts to set password

# Give sudo privileges
sudo usermod -aG sudo casm

# Copy SSH keys (optional, for passwordless login)
sudo cp -r /home/pi/.ssh /home/casm/
sudo chown -R casm:casm /home/casm/.ssh

# Test new user works
exit
ssh casm@192.168.1.101

# Once confirmed working, optionally delete old 'pi' user
sudo deluser --remove-home pi
```

---

## Docker Deployment

### Main Server (Dockerized)

**The main server runs in Docker for:**
- ✅ Consistent environment across different OS
- ✅ Easy deployment and updates
- ✅ Automatic restart on crash
- ✅ Isolated from system dependencies

**Files:**
- `Dockerfile` - Main server container image
- `docker-compose.yml` - Orchestration config
- `.dockerignore` - Files to exclude from container

**Architecture:**
```
Host Machine (laptop/OVRO server)
    ↓
Docker Container (casm_main_server)
    ├── Python 3.11
    ├── Flask + dependencies
    ├── main_server/ code
    └── main_config.yaml (mounted from host)
    ↓
Pis via Ethernet (192.168.1.100, 192.168.1.101)
```

**Data Persistence:**
- `./data/status_history.db` - Status check logs (mounted volume)
- `./main_config.yaml` - Configuration (mounted read-only)

**Deployment:**
```bash
# First time
docker-compose up -d

# Updates
git pull
docker-compose up -d --build

# View logs
docker-compose logs -f
```

### Raspberry Pis (Native - No Docker)

**Pis run native (non-containerized) because:**
- ❌ Docker adds complexity for hardware access
- ✅ Direct I2C access to relay HATs
- ✅ Lower resource overhead
- ✅ Easier debugging

**Deployment:**
- Systemd service for auto-start
- Direct hardware access via I2C
- See Step 2 in SETUP for Pi deployment

---

## Files

```
casm_analog_power_controller/
├── Dockerfile             # Main server container image
├── docker-compose.yml     # Docker orchestration
├── .dockerignore          # Docker build exclusions
├── hardware/              # Pi server code (runs natively on Pis)
├── main_server/           # Main coordinator code (runs in Docker)
├── simulation/            # Simulator (no hardware needed)
├── run_pi_server.py       # Start Pi server (on Pis)
├── run_main_server.py     # Start main server (in Docker container)
├── run_simulation.py      # Start simulator
├── main_config.yaml       # Single config file for entire system
└── requirements.txt       # Python dependencies
```

---

## Resources

- [lib8relind GitHub](https://github.com/SequentMicrosystems/8relind-rpi) - Hardware library
- [Sequent Microsystems](https://sequentmicrosystems.com/) - Board manufacturer
- [Flask Documentation](https://flask.palletsprojects.com/) - Web framework

---

## License

See LICENSE file for details.
