# CASM Analog Power Controller

A scalable Flask-based HTTP request system for controlling power to the CASM analog chain through Sequent Microsystems 8-relay boards on Raspberry Pis.

## System Overview

**Two Stages:**
- **Main Server/Head Node** - Routes requests to appropriate Pi (port 5000)
- **Raspberry Pis** - Control physical relay boards (port 5001 each)

**Hardware:**
- 47 switches total: CH1-4 (full chassis power) + CH1A-K, CH2A-K, CH3A-K, CH4A-J (Per SNAP BACboards)
- Sequent Microsystems 8-relay HAT boards
- **Two deployment options:**
  - **Option 1 (Single Pi)**: 6 relay boards on one Pi controlling all 4 chassis
  - **Option 2 (Two Pis)**: 3 relay boards per Pi (Pi 1: CH1-2, Pi 2: CH3-4)

---

## SETUP

### Step 1: Configure Each Raspberry Pi

```bash
# On each Pi
ssh pi@<pi-ip>

# Install dependencies
pip3 install -r requirements.txt

# Create config (tells Pi which chassis it controls)
cp local_config.example.all_chassis.yaml local_config.yaml # copies example YAML file
nano local_config.yaml # edit the YAML file
```

**Edit `local_config.yaml`:** # this is the YAML file on the individual Pi
```yaml
pi_id: "pi_1"
chassis_controlled: [1, 2, 3, 4]  # Which chassis this Pi controls
num_relay_boards: 6               # Number of HATs connected to this Pi
relays_per_board: 8
```

**Start Pi server:**
```bash
python3 run_pi_server.py
```

### Step 2: Configure Main Server

```bash
# On main server
cd casm_analog_power_controller

# Create config (tells main server where all Pis are)
cp main_config.example.single_pi.yaml main_config.yaml
nano main_config.yaml
```

**Edit `main_config.yaml` (on main server):**
```yaml
raspberry_pis:
  pi_1:
    ip_address: "192.168.1.100"    # Pi's IP address
    port: 5001
    chassis: [1, 2]                # Must match Pi's local_config.yaml
  pi_2:
    ip_address: "192.168.1.101"
    port: 5001
    chassis: [3, 4]

status_check_interval: 30 # Amount of seconds in between requests for the status of the Pis
request_timeout: 5
```

**Start main server:**
```bash
python3 run_main_server.py
```

### Step 3: Test

```bash
# Check system status
curl http://main-server:5000/api/status

# Control a switch
curl -X POST http://main-server:5000/api/switch/CH1 \
  -H "Content-Type: application/json" \
  -d '{"state": 1}'

# Or open browser
# http://main-server:5000
```

---

## Configuration Details

### Pi Configuration (`local_config.yaml`)
Each Pi needs to know which chassis it controls.

**Examples:**

**Option 1 - Single Pi (6 boards total):**
```yaml
pi_id: "main_pi"
chassis_controlled: [1, 2, 3, 4]  # Controls all chassis
num_relay_boards: 6               # 6 boards on this one Pi
```

**Option 2 - Four Pis (2 boards each):**

Pi #1:
```yaml
pi_id: "pi_chassis_1"
chassis_controlled: [1]
num_relay_boards: 2    # 2 boards for chassis 1
```

Pi #2:
```yaml
pi_id: "pi_chassis_2"
chassis_controlled: [2]
num_relay_boards: 2    # 2 boards for chassis 2
```

Pi #3:
```yaml
pi_id: "pi_chassis_3"
chassis_controlled: [3]
num_relay_boards: 2    # 2 boards for chassis 3
```

Pi #4:
```yaml
pi_id: "pi_chassis_4"
chassis_controlled: [4]
num_relay_boards: 2    # 2 boards for chassis 4
```

**Important:** 
- Stack numbers are LOCAL (always start at 0 on each Pi)
- `num_relay_boards` should match physical hardware connected to that Pi

### Main Server Configuration (`main_config.yaml`)
Main server needs to know where all Pis are.

**Important:** 
- Use static IPs for Pis
- Chassis assignment in `main_config.yaml` must match each Pi's `local_config.yaml`
- Each chassis can only be assigned to ONE Pi
---

## Usage

### Webpage Front End

Open browser:
- Main server: `http://<main-server-ip>:5000`
- Individual Pi: `http://<pi-ip>:5001`

Click switches to toggle on/off.

### Command Line Using Curl Commands

**Control switches:**
```bash
# Turn on
curl -X POST http://main-server:5000/api/switch/CH1 \
  -H "Content-Type: application/json" \
  -d '{"state": 1}' # state 1 is on

# Turn off
curl -X POST http://main-server:5000/api/switch/CH2A \
  -H "Content-Type: application/json" \
  -d '{"state": 0}' # state 0 is off

# Get status
curl http://main-server:5000/api/switch/CH1
```

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
- `POST /api/relay/<stack>/<relay>` - Set relay (`{"state": 0 or 1}`)
- `GET /api/relay/<stack>/<relay>` - Get relay state
- `GET /api/relay/stack/<stack>` - Get all relays in stack

**Switch Names:**
- Chassis: `CH1`, `CH2`, `CH3`, `CH4`
- Individual SNAPs and BACboards: `CH1A-K`, `CH2A-K`, `CH3A-K`, `CH4A-J`
- Case-insensitive (`CH1` = `ch1`)

---

## Deployment Options

### Option 1: Single Pi (6 Relay Boards)

**Hardware:** 1 Raspberry Pi with 6 relay boards (48 relays total)

**Main server config (`main_config.yaml`):**
```yaml
raspberry_pis:
  main_pi:
    ip_address: "192.168.1.100"    # Or "localhost" if main server runs on same Pi
    port: 5001
    chassis: [1, 2, 3, 4]          # This Pi controls all 4 chassis

status_check_interval: 30
request_timeout: 5
```

**Pi config (`local_config.yaml` on the Pi):**
```yaml
pi_id: "main_pi"
chassis_controlled: [1, 2, 3, 4]   # All chassis on this Pi
num_relay_boards: 6                # 6 boards physically connected
relays_per_board: 8
```

**Pros:** Simple, fewer machines to manage  
**Cons:** Single point of failure, all relays on one Pi

---

### Option 2: Two Pis (6 Relay Boards Total)

**Hardware:** 2 Raspberry Pis, each with 3 relay boards (24 relays each)
- Pi #1: Chassis 1 & 2 (3 boards: CH1, CH1A-K, CH2, CH2A-K)
- Pi #2: Chassis 3 & 4 (3 boards: CH3, CH3A-K, CH4, CH4A-J)

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

**Each Pi config (`local_config.yaml`):**

Pi #1:
```yaml
pi_id: "pi_1"
chassis_controlled: [1, 2]
num_relay_boards: 3    # 3 boards for chassis 1 & 2
relays_per_board: 8
```

Pi #2:
```yaml
pi_id: "pi_2"
chassis_controlled: [3, 4]
num_relay_boards: 3    # 3 boards for chassis 3 & 4
relays_per_board: 8
```

**Pros:** Redundancy, load distribution across 2 Pis  
**Cons:** More hardware to manage than single Pi option

---

## Troubleshooting

### Pi shows as "unreachable"

**Check:**
1. Is Pi powered on and running the server?
2. Can you ping it? `ping 192.168.1.100`
3. Is the IP correct in `main_config.yaml`?
4. Test directly: `curl http://192.168.1.100:5001/api/status`

**Fix:**
- Restart Pi server: `ssh pi@<ip>` then `python3 run_pi_server.py`
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
cp main_config.example.single_pi.yaml main_config.yaml
nano main_config.yaml  # Edit IPs
```

### Pi server can't start

**Error:** `No config file found`

**Fix:**
```bash
cp local_config.example.one_chassis.yaml local_config.yaml
nano local_config.yaml  # Edit chassis
```

**Error:** `Failed to initialize relay boards`

**Fix:**
- Enable I2C: `sudo raspi-config` → Interface Options → I2C
- Check boards connected: `i2cdetect -y 1`
- Verify jumper settings on boards

---

## Key Features

✅ **Scalable** - 1 to N Pis, add/remove by editing config  
✅ **Unified API** - Same commands regardless of Pi count  
✅ **Status Monitoring** - Know when Pis are down  
✅ **Flexible** - Any chassis distribution  
✅ **Web + CLI** - Browser UI or curl commands  
✅ **Pi Agnostic** - Same code on all Pis  

---

## Important Notes

- **Use static IPs** for Pis
- **Check status** before experiments
- **Configs must match** between main server and Pis
- **Stack numbers are local** on each Pi (always start at 0)
- **Each chassis** can only be controlled by ONE Pi

---

## Files

```
casm_analog_power_controller/
├── hardware/                 # Pi server code
├── main_server/             # Main coordinator code
├── simulation/              # Simulator (no hardware needed)
├── run_pi_server.py         # Start Pi server
├── run_main_server.py       # Start main server
├── run_simulation.py        # Start simulator
├── main_config.yaml         # Main server config
├── local_config.yaml        # Pi config (one per Pi)
├── main_config.example.*.yaml    # Main server config examples
├── local_config.example.*.yaml   # Pi config examples
└── requirements.txt         # Dependencies
```

---

## Resources

- [lib8relind GitHub](https://github.com/SequentMicrosystems/8relind-rpi) - Hardware library
- [Sequent Microsystems](https://sequentmicrosystems.com/) - Board manufacturer
- [Flask Documentation](https://flask.palletsprojects.com/) - Web framework

---

## License

See LICENSE file for details.
