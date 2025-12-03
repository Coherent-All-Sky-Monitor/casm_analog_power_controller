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

## SETUP:

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

> **Important:** Pis have WiFi/Bluetooth hardware **disabled** to prevent Radio Frequency Interference (RFI) with the radio telescope. WiFi is temporarily enabled ONLY for initial setup (to install dependencies), then disabled via sudo nano /boot/firmware/config.txt, dtoverlay=disable-wifi, dtoverlay=disable-bt, before deployment.

#### Static IP Configuration

**Development Setup:**
- Pi connects to WiFi network
- Configure static IPs on Pi
- To SSH into Pi: Computer and Pi must be on same WiFi network (or connected via Ethernet with compatible subnet) or connected via ethernet cable with same subnet

**Configure Static IPs on Pi on Boot (RPi 5 using systemd):**

```bash
# Step 1: Create boot script
sudo nano /usr/local/bin/set_static_ip_nm.sh

# Paste this script and save (Ctrl+O, then Enter, then Ctrl+X):
#!/bin/bash
# Force static IP on Raspberry Pi 5 (Bookworm) Ethernet interface, every boot
# Configure IP settings to match your network subnet

# Ethernet interface on RPi 5
INTERFACE="end0"

# Configure IP settings to match your network subnet
# Development: Use your local subnet (e.g., 192.168.1.x)
# Production (OVRO): REPLACE with subnet provided by network admins
IP_ADDRESS="192.168.1.2/24"  # REPLACE: Your chosen static IP (e.g., 192.168.1.3 for Pi 2, or OVRO subnet IP)
NETWORK="192.168.1.0/24"     # REPLACE: Match your subnet (change for OVRO subnet)
GATEWAY="192.168.1.1"        # REPLACE: Your router/gateway IP (change for OVRO gateway)

sleep 2

# Bring up interface even if no cable is connected
ip link set "$INTERFACE" up

# Remove any DHCP or old addresses
ip addr flush dev "$INTERFACE"

# Assign static IP
ip addr add "$IP_ADDRESS" dev "$INTERFACE"

# Add local route
ip route add "$NETWORK" dev "$INTERFACE"

# Add default route
ip route add default via "$GATEWAY"

echo "Static IP $IP_ADDRESS assigned to $INTERFACE"

# Step 2: Make script executable
sudo chmod +x /usr/local/bin/set_static_ip_nm.sh

# Step 3: Create systemd service
sudo nano /etc/systemd/system/set-static-ip.service

# Paste this service configuration:
[Unit]
Description=Applies static IP on boot through network manager compatible with RPI 5
After=network-pre.target
Before=NetworkManager.service
Wants=network-pre.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/set_static_ip_nm.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target

# Step 4: Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable set-static-ip.service
sudo systemctl start set-static-ip.service

# Step 5: Reboot and verify
sudo reboot

# After reboot, check IP:
hostname -I
```

**Important Notes:**
- **Ethernet cable must be plugged in:** The static IP is configured on `end0` (Ethernet), so Ethernet cable must be connected for the Pi to be reachable
- **Static IP persists:** Once configured, the Pi will ALWAYS use this IP address whenever Ethernet is connected (even after reboots)
- **IP addresses must match `main_config.yaml`**
- **WiFi is disabled after installing dependencies**

**Configure Your Computer:**
- Connect your laptop/computer to the same WiFi network
- This allows you to SSH and git clone the repo on the Pi

**Production (OVRO) - IMPORTANT:**

Before deploying to OVRO, coordinate with network administrators:

1. **Determine IP Subnet:** Ask what subnet to use (provided by OVRO network admins)

2. **Get Pi MAC Addresses:**
   ```bash
   # On each Pi (use 'end0' for RPi 5, 'eth0' for older models):
   ip link show end0 | grep ether
   # Example output: link/ether dc:a6:32:ab:cd:ef
   ```

3. **Choose Static IPs:** Pick IPs in the OVRO subnet (provided by network admins)

4. **Update Pi Static IPs:**
   ```bash
   # Edit the boot script created earlier:
   sudo nano /usr/local/bin/set_static_ip_nm.sh
   
   # Update with OVRO network settings (subnet provided by network admins):
   INTERFACE="end0"            # Ethernet interface on RPi 5
   IP_ADDRESS="X.X.X.X/24"     # REPLACE: OVRO subnet IP (change for OVRO subnet)
   NETWORK="X.X.X.0/24"        # REPLACE: OVRO subnet (change for OVRO subnet)
   GATEWAY="X.X.X.1"           # REPLACE: OVRO gateway (change for OVRO gateway)
   
   # Restart the service to apply:
   sudo systemctl restart set-static-ip.service
   
   # Verify:
   hostname -I
   ```
   
   **Important:** The IP addresses you choose here must match what's in `main_config.yaml` on the main server, and must match what you request for DHCP reservations

5. **Request DHCP Reservations:**
   
   Configure DHCP reservations to prevent IP conflicts:
   
   - Pi 1:
     MAC Address: <pi1-mac-address>
     Reserved IP: <pi1-chosen-ip>
     Hostname: casm-pi1
   
   - Pi 2:
     MAC Address: <pi2-mac-address>
     Reserved IP: <pi2-chosen-ip>
     Hostname: casm-pi2
   
   This ensures the DHCP server assigns the same IP as the static IP set on the Pi based on its MAC address.
   ```

**Why Both Static IP + DHCP Reservation?**
- **Redundancy:** If DHCP fails, Pi keeps its IP
- **No Conflicts:** DHCP won't assign these IPs to other devices
- **Auto-Configuration:** Pis identify themselves via IP in `main_config.yaml`

#### Initial Setup (ONE TIME per Pi)

**Workflow:** 
1. Pi connects to WiFi and static IP is set
2. Enable I2C interface (required for HAT communication)
3. Clone repo and install dependencies (WiFi provides internet)
4. Disable WiFi/Bluetooth hardware to prevent RFI
5. Connect via Ethernet and run code

```bash
# 1. Connect Pi to WiFi network and configure static IP
#    See "Static IP Configuration" section above
#    Pi 1: 192.168.1.2, Pi 2: 192.168.1.3

# 2. Connect your computer to the same WiFi network
#    This allows SSH and git clone access

# 3. SSH to Pi (via WiFi static IP)
ssh casm@192.168.1.2  # Pi 1 (or 192.168.1.3 for Pi 2)

# 4. Enable I2C interface (REQUIRED for HAT communication)
sudo raspi-config
# Navigate to: Interface Options → I2C → Enable
# Or use command line: sudo raspi-config nonint do_i2c 0
# Exit raspi-config (no reboot needed yet)

# 5. Clone repository (WiFi provides internet access)
git clone https://github.com/Coherent-All-Sky-Monitor/casm_analog_power_controller.git
cd casm_analog_power_controller

# 6. Create virtual environment
python3 -m venv casmpower
source casmpower/bin/activate

# 7. Install dependencies (via WiFi internet)
pip3 install -r requirements.txt

# 8. Disable WiFi and Bluetooth (REQUIRED for RFI prevention)
sudo nano /boot/firmware/config.txt
# Add these lines at the end:
#   dtoverlay=disable-wifi
#   dtoverlay=disable-bt
# Save and reboot: sudo reboot

# 9. After reboot, Pi WiFi/Bluetooth are disabled
#    Configure Ethernet static IP (if not already configured)
#    SSH via Ethernet static IP and start server
ssh casm@192.168.1.2  # Use static IP configured in main_config.yaml
cd casm_analog_power_controller
source casmpower/bin/activate  # If using casmpower
python3 run_pi_server.py
```

**Summary:**
1. ✅ Pi connects to WiFi/ethernet with static IP (ex: 192.168.1.2 or 192.168.1.3)
2. ✅ Computer connects to same WiFi/ethernet for SSH access
3. ✅ Enable I2C interface (required for HAT communication)
4. ✅ Clone repo and install dependencies
5. ✅ Disable WiFi/Bluetooth hardware to prevent RFI
6. ✅ Connect via Ethernet and run code

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
    ip_address: "192.168.1.3"
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

### Command Line Using Curl Commands

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
    ip_address: "192.168.1.3"
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

## Auto-Configuration System

The system automatically detects which Pi's configuration to use based on the Pi's IP address in `main_config.yaml`.

### How It Works:

1. **Each Pi has a unique static IP** (configured in `/etc/dhcpcd.conf`)
2. **All Pis have the same repo** with `main_config.yaml`
3. **Pi auto-detects its IP** and finds its entry in `main_config.yaml`
4. **Single source of truth** - All configs centralized in one file

### Config File:

```
casm_analog_power_controller/
└── main_config.yaml  # Single config file for all Pis
```

The `main_config.yaml` file contains entries for all Pis:

```yaml
raspberry_pis:
  pi_1:
    ip_address: "192.168.1.2"
    chassis: [1, 2]
    switch_mapping: {...}
  pi_2:
    ip_address: "192.168.1.3"
    chassis: [3, 4]
    switch_mapping: {...}
```

### How Pi Auto-Configures:

**Each Pi automatically finds its configuration:**

1. Pi boots up and detects its own static IP address (e.g., `192.168.1.2`)
2. Pi loads `main_config.yaml` from the repo
3. Pi searches for the entry with matching `ip_address`
4. Pi extracts its configuration:
   - `pi_id` (e.g., `pi_1`)
   - `num_relay_hats`, `relays_per_hat`
   - `switch_mapping` (all switch-to-relay mappings)
5. Pi is fully configured

**Minimal Configuration on Pis** Set static IP and `git pull`.

### Benefits:

✅ **Single config file** - All Pis configured in `main_config.yaml`  
✅ **Auto-detection** - Pi automatically finds its config by IP  
✅ **Version control** - Centralized config in git  
✅ **Easy updates** - Edit `main_config.yaml` and push, Pis auto-configure  
✅ **No per-Pi files** - One config for all Pis

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
- **HAT numbers are local** on each Pi (always start at 0)
- **Each chassis** can only be controlled by ONE Pi

### Setting Up Username on Raspberry Pi


**Why `casm` username?** Consistent username across all Pis makes management easier and matches the project name.

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
Pis via Ethernet (192.168.1.2, 192.168.1.3)
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
├── simulation/            # Simulator of relay switch
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
