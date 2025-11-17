from flask import Flask, jsonify, request, render_template
import lib8relind as relay
import yaml
import os
from pathlib import Path

# Configuration for RPi with HATs with 8 relays per board.

# Load configuration from YAML file
def get_ip_address():
    """Get this Pi's IP address"""
    import socket
    import subprocess
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            result = subprocess.run(['hostname', '-I'], 
                                    capture_output=True, 
                                    text=True, 
                                    check=True)
            ips = result.stdout.strip().split()
            for ip in ips:
                if not ip.startswith('127.') and ':' not in ip:
                    return ip
        except Exception:
            pass
    return None

def load_config():
    """
    Load configuration from main_config.yaml and auto-detect this Pi's section.
    
    This Pi identifies itself by IP address, finds its entry in main_config.yaml,
    and extracts its specific configuration (hardware specs, switch mappings, etc.)
    
    Returns:
        dict: This Pi's configuration section with keys:
            - pi_id: str
            - num_relay_boards: int
            - relays_per_board: int
            - switch_mapping: dict
            - chassis: list (optional)
            - ip_address: str
            - port: int
    """
    repo_root = Path(__file__).parent.parent
    main_config_path = repo_root / 'main_config.yaml'
    
    # Check if main_config.yaml exists
    if not main_config_path.exists():
        raise FileNotFoundError(
            f"\n❌ ERROR: main_config.yaml not found at {main_config_path}\n\n"
            f"This Pi loads its configuration from main_config.yaml.\n"
            f"Make sure you've cloned the repo with the config file.\n\n"
            f"See README.md for setup instructions."
        )
    
    # Load main config
    try:
        with open(main_config_path, 'r') as f:
            main_config = yaml.safe_load(f)
    except Exception as e:
        raise Exception(
            f"\n❌ ERROR: Failed to load main_config.yaml\n"
            f"Error: {e}\n\n"
            f"Check that the file is valid YAML format."
        )
    
    # Get this Pi's IP address
    my_ip = get_ip_address()
    if not my_ip:
        raise RuntimeError(
            "\n❌ ERROR: Could not detect this Pi's IP address\n\n"
            "Make sure the Pi has a network connection.\n"
            "You can manually check with: hostname -I"
        )
    
    print(f"🔍 Detected this Pi's IP address: {my_ip}")
    
    # Find this Pi's configuration by matching IP address
    raspberry_pis = main_config.get('raspberry_pis', {})
    my_config = None
    my_pi_id = None
    
    for pi_id, pi_config in raspberry_pis.items():
        if pi_config.get('ip_address') == my_ip:
            my_config = pi_config.copy()
            my_pi_id = pi_id
            break
    
    if not my_config:
        # Show available IPs to help with debugging
        available_ips = [cfg.get('ip_address') for cfg in raspberry_pis.values()]
        raise RuntimeError(
            f"\n❌ ERROR: This Pi's IP ({my_ip}) not found in main_config.yaml\n\n"
            f"Available Pi IPs in config: {available_ips}\n\n"
            f"Either:\n"
            f"  1. Update main_config.yaml to include this Pi's IP\n"
            f"  2. Set this Pi's static IP to match one in main_config.yaml\n\n"
            f"See README.md for setup instructions."
        )
    
    # Add pi_id to the config
    my_config['pi_id'] = my_pi_id
    
    # Validate required fields
    required_fields = ['num_relay_boards', 'relays_per_board', 'switch_mapping']
    missing_fields = [field for field in required_fields if field not in my_config]
    
    if missing_fields:
        raise ValueError(
            f"\n❌ ERROR: Missing required fields in main_config.yaml for {my_pi_id}\n"
            f"Missing: {missing_fields}\n\n"
            f"Each Pi entry must have:\n"
            f"  - num_relay_boards: 3\n"
            f"  - relays_per_board: 8\n"
            f"  - switch_mapping: {{...}}\n"
        )
    
    print(f"✅ Loaded configuration for {my_pi_id} from main_config.yaml")
    print(f"   - Chassis: {my_config.get('chassis', 'N/A')}")
    print(f"   - Relay boards: {my_config['num_relay_boards']}")
    print(f"   - Switch mappings: {len(my_config['switch_mapping'])} switches")
    
    return my_config

# Load configuration from YAML file
CONFIG = load_config()
NUM_STACKS = CONFIG['num_relay_boards']
RELAYS_PER_BOARD = CONFIG['relays_per_board']
PI_ID = CONFIG['pi_id']

# Note: Switch mappings are now centralized in main_config.yaml
# This Pi server just needs to know its hardware specs


class SwitchMapper:
    """
    Maps switch names to relay HAT positions using YAML configuration.
    
    This allows flexible, non-sequential mapping where any switch can be
    assigned to any relay position. 
    
    The mapping is loaded from main_config.yaml under the 'switch_mapping' key.
    Each entry is: switch_name: {hat: X, relay: Y}
    
    NOTE: 'hat' in YAML = 'stack' in code (I2C HAT index 0-based)
          'relay' in YAML is 1-based (1-8) to match physical hardware labels
    """
    
    def __init__(self, switch_mapping_config):
        """
        Initialize the mapper from YAML configuration.
        
        Args:
            switch_mapping_config: Dict from YAML with format:
                {'CH1': {'hat': 0, 'relay': 1}, 'CH1A': {'hat': 0, 'relay': 2}, ...}
                Relay numbers are 1-based (1-8) matching physical hardware labels.
        """
        self._switch_to_relay = {}
        self._relay_to_switch = {}
        self._build_mapping_from_yaml(switch_mapping_config)
    
    def _build_mapping_from_yaml(self, switch_mapping_config):
        """
        Build bidirectional mapping from YAML config.
        
        Relay numbers in YAML are 1-based (1-8) to match physical hardware labels.
        No conversion needed - YAML values map directly to hardware.
        
        NOTE: Switch mappings are now in main_config.yaml (centralized).
        This method is kept for backwards compatibility with direct Pi access.
        """
        if not switch_mapping_config:
            # No mappings is OK now - main server sends complete instructions
            print("ℹ️  No switch mappings in local config (using centralized config)")
            return
        
        for switch_name, position in switch_mapping_config.items():
            if not isinstance(position, dict) or 'relay' not in position:
                raise ValueError(
                    f"\n❌ ERROR: Invalid mapping for '{switch_name}' in main_config.yaml\n"
                    f"Expected format: {switch_name}: {{hat: X, relay: Y}}\n"
                    f"Got: {position}"
                )
            
            # Accept either 'hat' or 'board' (backwards compatibility)
            hat = position.get('hat', position.get('board'))
            if hat is None:
                raise ValueError(
                    f"\n❌ ERROR: Missing 'hat' field for '{switch_name}' in main_config.yaml\n"
                    f"Expected format: {switch_name}: {{hat: X, relay: Y}}\n"
                    f"Got: {position}"
                )
            
            relay = position['relay']  # 1-based relay in YAML (matches hardware!)
            
            # Validate relay number
            if relay < 1 or relay > 8:
                raise ValueError(
                    f"\n❌ ERROR: Invalid relay number for '{switch_name}'\n"
                    f"Relay must be 1-8 (got {relay})\n"
                    f"Use 1-based numbering to match physical hardware labels."
                )
            
            # Store with uppercase switch names for consistency
            switch_name_upper = switch_name.upper()
            
            # Build bidirectional mapping
            # Relay numbers are 1-based, matching physical hardware
            self._switch_to_relay[switch_name_upper] = (hat, relay)
            self._relay_to_switch[(hat, relay)] = switch_name_upper
        
        print(f"✅ Loaded {len(self._switch_to_relay)} switch mappings from YAML config")
    
    def get_relay_position(self, switch_name):
        """
        Convert switch name to (hat, relay) position.
        
        Args:
            switch_name: Logical name like 'CH1', 'CH1A', etc.
        
        Returns:
            tuple: (hat, relay) or None if not found
            Relay numbers are 1-based (1-8) matching physical hardware.
            
        Example:
            get_relay_position('CH1') -> (0, 1)  # HAT 0, Relay 1
        """
        return self._switch_to_relay.get(switch_name.upper())
    
    def get_switch_name(self, stack, relay):
        """
        Convert (hat/stack, relay) position to switch name.
        
        Args:
            stack: HAT/stack number (0-based)
            relay: Relay number (1-based for hardware)
        
        Returns:
            str: Switch name like 'CH1', 'CH1A', or None if not mapped
        """
        return self._relay_to_switch.get((stack, relay))
    
    def get_all_switches(self):
        """Get sorted list of all valid switch names"""
        return sorted(self._switch_to_relay.keys())
    
    def is_valid_switch(self, switch_name):
        """Check if a switch name is valid"""
        return switch_name.upper() in self._switch_to_relay


# Global switch mapper instance - loads mappings from main_config.yaml
# Pi auto-detects its section based on IP address
switch_mapper = SwitchMapper(switch_mapping_config=CONFIG.get('switch_mapping', {}))


def create_app():
    app = Flask(__name__)

    @app.route('/')
    def index():
        """Render the web UI showing all relay states"""
        return render_template('index.html')
    
    @app.route('/api/status', methods=['GET'])
    def status_check():
        """Status check endpoint for main server to monitor this Pi"""
        # Try to get switch count from mapper, but don't fail if no mappings
        try:
            switch_count = len(switch_mapper.get_all_switches())
            switches = switch_mapper.get_all_switches()
        except:
            switch_count = 0
            switches = []
        
        return jsonify({
            'status': 'online',
            'pi_id': PI_ID,
            'num_relay_boards': NUM_STACKS,
            'relays_per_board': RELAYS_PER_BOARD,
            'total_switches': switch_count,
            'switches': switches
        })
    
    @app.route('/api/relay/control', methods=['POST'])
    def control_relay_direct():
        """
        Control a relay directly with complete instructions from main server.
        Main server sends: {switch_name, hat, relay, state}
        Relay numbers are 1-based (1-8) matching physical hardware labels.
        This endpoint bypasses switch name lookup entirely.
        """
        data = request.get_json()
        if data is None:
            return jsonify({'error': 'Missing JSON data'}), 400
        
        # Extract parameters
        switch_name = data.get('switch_name')
        hat = data.get('hat')  # 0-based HAT number
        relay = data.get('relay')  # 1-based relay number (1-8)
        state = data.get('state')
        
        # Validate
        if hat is None or relay is None or state is None:
            return jsonify({'error': 'Missing required fields: hat, relay, state'}), 400
        
        if hat < 0 or hat >= NUM_STACKS:
            return jsonify({'error': f'Invalid HAT number. Must be 0-{NUM_STACKS-1}'}), 400
        
        if relay < 1 or relay > 8:
            return jsonify({'error': 'Invalid relay number. Must be 1-8'}), 400
        
        if state not in [0, 1]:
            return jsonify({'error': 'State must be 0 or 1'}), 400
        
        try:
            # Set relay state on hardware (relay is already 1-based, no conversion needed!)
            relay.set(hat, relay, state)
            
            return jsonify({
                'success': True,
                'switch_name': switch_name,
                'hat': hat,
                'relay': relay,
                'state': state,
                'status': 'ON' if state == 1 else 'OFF',
                'message': f'{switch_name} (HAT {hat}, Relay {relay}) turned {"ON" if state == 1 else "OFF"}'
            })
        except Exception as e:
            return jsonify({'error': f'Failed to set relay state: {str(e)}'}), 500

    @app.route('/api/relay/<int:stack>/<int:relay_num>', methods=['GET'])
    def get_relay_state(stack, relay_num):
        """Get the state of a specific relay
        
        Args:
            stack: Stack number (currently 0, will be 0-5 when all boards arrive)
            relay_num: Relay number (1-8)
        
        Returns:
            JSON with relay state (0 or 1)
        """
        if stack < 0 or stack >= NUM_STACKS:
            return jsonify({'error': f'Invalid stack. Must be 0-{NUM_STACKS-1}'}), 400
        if relay_num < 1 or relay_num > RELAYS_PER_BOARD:
            return jsonify({'error': f'Invalid relay. Must be 1-{RELAYS_PER_BOARD}'}), 400
        
        try:
            # Get relay state from hardware (returns 0 or 1)
            state = relay.get(stack, relay_num)
            return jsonify({
                'stack': stack,
                'relay': relay_num,
                'state': state,
                'status': 'ON' if state == 1 else 'OFF'
            })
        except Exception as e:
            return jsonify({'error': f'Failed to read relay state: {str(e)}'}), 500

    @app.route('/api/relay/<int:stack>/<int:relay_num>', methods=['POST'])
    def set_relay_state(stack, relay_num):
        """Set the state of a specific relay
        
        Args:
            stack: Stack number (currently 0, will be 0-5 when all boards arrive)
            relay_num: Relay number (1-8)
        
        Body:
            JSON with 'state': 0 (OFF) or 1 (ON)
        
        Returns:
            JSON with updated relay state
        """
        if stack < 0 or stack >= NUM_STACKS:
            return jsonify({'error': f'Invalid stack. Must be 0-{NUM_STACKS-1}'}), 400
        if relay_num < 1 or relay_num > RELAYS_PER_BOARD:
            return jsonify({'error': f'Invalid relay. Must be 1-{RELAYS_PER_BOARD}'}), 400
        
        data = request.get_json()
        if data is None or 'state' not in data:
            return jsonify({'error': 'Missing state in request body'}), 400
        
        new_state = data['state']
        if new_state not in [0, 1]:
            return jsonify({'error': 'State must be 0 (OFF) or 1 (ON)'}), 400
        
        try:
            # Set relay state on hardware
            relay.set(stack, relay_num, new_state)
            
            return jsonify({
                'stack': stack,
                'relay': relay_num,
                'state': new_state,
                'status': 'ON' if new_state == 1 else 'OFF',
                'message': f'Stack {stack}, Relay {relay_num} turned {"ON" if new_state == 1 else "OFF"}'
            })
        except Exception as e:
            return jsonify({'error': f'Failed to set relay state: {str(e)}'}), 500

    @app.route('/api/relay/all', methods=['GET'])
    def get_all_relays():
        """Get the state of all relays across all stacks"""
        all_states = {}
        
        for stack in range(NUM_STACKS):
            try:
                # Get all 8 relays as bitmap, then convert to list
                bitmap = relay.get_all(stack)
                relays = []
                for relay_num in range(RELAYS_PER_BOARD):
                    # Extract bit for each relay (LSB is relay 1)
                    relays.append((bitmap >> relay_num) & 1)
                all_states[f'stack_{stack}'] = relays
            except Exception as e:
                all_states[f'stack_{stack}'] = {'error': str(e)}
        
        return jsonify(all_states)

    @app.route('/api/relay/stack/<int:stack>', methods=['GET'])
    def get_stack_state(stack):
        """Get the state of all relays in a specific stack
        
        Args:
            stack: Stack number (currently 0, will be 0-5 when all boards arrive)
        """
        if stack < 0 or stack >= NUM_STACKS:
            return jsonify({'error': f'Invalid stack. Must be 0-{NUM_STACKS-1}'}), 400
        
        try:
            # Get all 8 relays as bitmap, then convert to list
            bitmap = relay.get_all(stack)
            relays = []
            for relay_num in range(RELAYS_PER_BOARD):
                # Extract bit for each relay (LSB is relay 1)
                relays.append((bitmap >> relay_num) & 1)
            
            return jsonify({
                'stack': stack,
                'relays': relays
            })
        except Exception as e:
            return jsonify({'error': f'Failed to read stack state: {str(e)}'}), 500

    @app.route('/api/relay/stack/<int:stack>/all-on', methods=['POST'])
    def turn_on_stack(stack):
        """Turn on all relays on a specific stack"""
        if stack < 0 or stack >= NUM_STACKS:
            return jsonify({'error': f'Invalid stack. Must be 0-{NUM_STACKS-1}'}), 400
        
        try:
            relay.set_all(stack, 255)
            return jsonify({
                'stack': stack,
                'message': f'All relays ON for stack {stack}'
            })
        except Exception as e:
            return jsonify({'error': f'Failed to turn on stack {stack}: {str(e)}'}), 500

    @app.route('/api/relay/stack/<int:stack>/all-off', methods=['POST'])
    def turn_off_stack(stack):
        """Turn off all relays on a specific stack"""
        if stack < 0 or stack >= NUM_STACKS:
            return jsonify({'error': f'Invalid stack. Must be 0-{NUM_STACKS-1}'}), 400
        
        try:
            relay.set_all(stack, 0)
            return jsonify({
                'stack': stack,
                'message': f'All relays OFF for stack {stack}'
            })
        except Exception as e:
            return jsonify({'error': f'Failed to turn off stack {stack}: {str(e)}'}), 500

    @app.route('/api/relay/all-on', methods=['POST'])
    def turn_on_all_stacks():
        """Turn on all relays across ALL stacks"""
        results = {}
        
        for stack in range(NUM_STACKS):
            try:
                relay.set_all(stack, 255)
                results[f'stack_{stack}'] = 'All relays ON'
            except Exception as e:
                results[f'stack_{stack}'] = f'Error: {str(e)}'
        
        return jsonify({
            'message': 'All ON command sent to all stacks',
            'results': results
        })

    @app.route('/api/relay/all-off', methods=['POST'])
    def turn_off_all_stacks():
        """Turn off all relays across ALL stacks"""
        results = {}
        
        for stack in range(NUM_STACKS):
            try:
                relay.set_all(stack, 0)
                results[f'stack_{stack}'] = 'All relays OFF'
            except Exception as e:
                results[f'stack_{stack}'] = f'Error: {str(e)}'
        
        return jsonify({
            'message': 'All OFF command sent to all stacks',
            'results': results
        })

    # ========== Switch Name Based API Endpoints ==========
    
    @app.route('/api/switch/<switch_name>', methods=['GET'])
    def get_switch_state(switch_name):
        """Get the state of a switch by its logical name (e.g., CH1, CH1A)
        
        Args:
            switch_name: Logical switch name (CH1, CH1A, CH2, etc.)
        
        Returns:
            JSON with switch state (0 or 1)
        """
        position = switch_mapper.get_relay_position(switch_name)
        if position is None:
            return jsonify({
                'error': f'Invalid switch name: {switch_name}',
                'valid_switches': switch_mapper.get_all_switches()
            }), 400
        
        stack, relay_num = position
        
        try:
            state = relay.get(stack, relay_num)
            return jsonify({
                'switch_name': switch_name.upper(),
                'stack': stack,
                'relay': relay_num,
                'state': state,
                'status': 'ON' if state == 1 else 'OFF'
            })
        except Exception as e:
            return jsonify({'error': f'Failed to read switch state: {str(e)}'}), 500
    
    @app.route('/api/switch/<switch_name>', methods=['POST'])
    def set_switch_state(switch_name):
        """Set the state of a switch by its logical name
        
        Args:
            switch_name: Logical switch name (CH1, CH1A, CH2, etc.)
        
        Body:
            JSON with 'state': 0 (OFF) or 1 (ON)
        
        Returns:
            JSON with updated switch state
        """
        position = switch_mapper.get_relay_position(switch_name)
        if position is None:
            return jsonify({
                'error': f'Invalid switch name: {switch_name}',
                'valid_switches': switch_mapper.get_all_switches()
            }), 400
        
        stack, relay_num = position
        
        data = request.get_json()
        if data is None or 'state' not in data:
            return jsonify({'error': 'Missing state in request body'}), 400
        
        new_state = data['state']
        if new_state not in [0, 1]:
            return jsonify({'error': 'State must be 0 (OFF) or 1 (ON)'}), 400
        
        try:
            relay.set(stack, relay_num, new_state)
            
            return jsonify({
                'switch_name': switch_name.upper(),
                'stack': stack,
                'relay': relay_num,
                'state': new_state,
                'status': 'ON' if new_state == 1 else 'OFF',
                'message': f'{switch_name.upper()} turned {"ON" if new_state == 1 else "OFF"}'
            })
        except Exception as e:
            return jsonify({'error': f'Failed to set switch state: {str(e)}'}), 500
    
    @app.route('/api/switch/list', methods=['GET'])
    def list_all_switches():
        """Get a list of all valid switch names and their current states"""
        switches = {}
        
        for switch_name in switch_mapper.get_all_switches():
            position = switch_mapper.get_relay_position(switch_name)
            if position:
                stack, relay_num = position
                try:
                    state = relay.get(stack, relay_num)
                    switches[switch_name] = {
                        'state': state,
                        'status': 'ON' if state == 1 else 'OFF',
                        'stack': stack,
                        'relay': relay_num
                    }
                except Exception as e:
                    switches[switch_name] = {'error': str(e)}
        
        return jsonify(switches)
    
    @app.route('/api/switch/chassis/<int:chassis_num>', methods=['GET'])
    def get_chassis_switches(chassis_num):
        """Get all switches for a specific chassis (e.g., chassis 1 returns CH1 + CH1A-K)
        
        Args:
            chassis_num: Chassis number (1-4)
        """
        if chassis_num < 1 or chassis_num > 4:
            return jsonify({'error': 'Chassis number must be 1-4'}), 400
        
        chassis_name = f'CH{chassis_num}'
        switches = {}
        
        # Get chassis switch
        position = switch_mapper.get_relay_position(chassis_name)
        if position:
            stack, relay_num = position
            try:
                state = relay.get(stack, relay_num)
                switches[chassis_name] = {
                    'state': state,
                    'status': 'ON' if state == 1 else 'OFF',
                    'type': 'chassis'
                }
            except Exception as e:
                switches[chassis_name] = {'error': str(e)}
        
        # Get BACboard switches
        max_letter = 'J' if chassis_num == 4 else 'K'
        for letter in 'ABCDEFGHIJK':
            if letter > max_letter:
                break
            switch_name = f'CH{chassis_num}{letter}'
            position = switch_mapper.get_relay_position(switch_name)
            if position:
                stack, relay_num = position
                try:
                    state = relay.get(stack, relay_num)
                    switches[switch_name] = {
                        'state': state,
                        'status': 'ON' if state == 1 else 'OFF',
                        'type': 'BACboard'
                    }
                except Exception as e:
                    switches[switch_name] = {'error': str(e)}
        
        return jsonify({
            'chassis': chassis_num,
            'switches': switches
        })

    return app
