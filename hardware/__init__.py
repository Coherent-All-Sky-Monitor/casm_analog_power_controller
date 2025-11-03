from flask import Flask, jsonify, request, render_template
import lib8relind as relay
import yaml
import os
from pathlib import Path

# Configuration for RPi with HATs with 8 relays per board.

# Load configuration from YAML file
def load_config():
    """Load configuration from local_config.yaml"""
    config_path = Path(__file__).parent.parent / 'local_config.yaml'
    
    if not config_path.exists(): # Check if the congif file exists
        raise FileNotFoundError(
            f"\n❌ ERROR: Configuration file not found at {config_path}\n\n"
            f"Please create local_config.yaml by copying an example:\n"
            f"  cp local_config.example.all_chassis.yaml local_config.yaml\n"
            f"  nano local_config.yaml\n\n"
            f"See README.md for setup instructions."
        )
    
    try: # Opens the config file and loads it
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            print(f"✅ Loaded config from {config_path}")
            return config
    except Exception as e:  # If the config file isn't a valid YAML file
        raise Exception(
            f"\n❌ ERROR: Failed to load config from {config_path}\n"
            f"Error: {e}\n\n"
            f"Check that the file is valid YAML format."
        )

# Load configuration from YAML file
CONFIG = load_config()
NUM_STACKS = CONFIG['num_relay_boards']
RELAYS_PER_BOARD = CONFIG['relays_per_board']
CHASSIS_CONTROLLED = CONFIG['chassis_controlled']
PI_ID = CONFIG['pi_id']


class SwitchMapper:
    """
    Maps switch names representing real hardware(CH1, CH1A, etc.) to stack/relay number (stack, relay).
    
    Layout with 4 chassis and 43 planks:
    - 4 chassis switches: CH1, CH2, CH3, CH4
    - 43 SNAP-BACboards switches: CH1A-K (11), CH2A-K (11), CH3A-K (11), CH4A-J (10)
    
    Sequential mapping across boards (when controlling all chassis):
    Stack 0: CH1, CH1A-G
    Stack 1: CH1H-K, CH2, CH2A-C
    Stack 2: CH2D-K, CH3
    Stack 3: CH3A-G, CH4
    Stack 4: CH3H-K, CH4A-C
    Stack 5: CH4D-J, SPARE
    
    NOTE: This class maps the chassis listed in the config file (so not necessarily all 4 chassis)
    Each Pi's relay boards start at stack 0 (local numbering).
    """
    
    def __init__(self, chassis_controlled=None):
        """
        Initialize the mapper with specific chassis to control.
        
        Args:
            chassis_controlled: List of chassis numbers (1-4) this Pi controls.
        """
        self._switch_to_relay = {}
        self._relay_to_switch = {}
        self.chassis_controlled = chassis_controlled or [1, 2, 3, 4]
        self._build_mapping()
    
    def _build_mapping(self):
        """Build the bidirectional mapping between switch names and relay positions
        
        This dynamically builds mappings ONLY for the chassis this Pi controls.
        Stack numbers are always local (starting from 0) on each Pi.
        """
        mapping = []  # Temporary list of tuples: (switch_name, stack, relay)
        
        # Build full mapping table first, then filter by controlled chassis
        # Full mapping represents the logical arrangement across all possible chassis
        full_mapping = self._build_full_mapping()
        
        # Now extract only the chassis this Pi controls and renumber stacks locally
        mapping = self._extract_controlled_chassis(full_mapping)
        
        # Build bidirectional dictionaries
        for switch_name, stack, relay in mapping:
            self._switch_to_relay[switch_name] = (stack, relay)
            self._relay_to_switch[(stack, relay)] = switch_name
    
    def _build_full_mapping(self):
        """Build the complete mapping for all chassis (logical arrangement)"""
        mapping = []
        
        # CH1 chassis + CH1A-K BACboards (12 total, needs 1.5 boards)
        mapping.append(('CH1', 0, 1, 1))  # (name, stack, relay, chassis_num)
        for i, letter in enumerate('ABCDEFGHIJK'):
            stack = 0 if i < 7 else 1
            relay = (2 + i) if i < 7 else (1 + i - 7)
            mapping.append((f'CH1{letter}', stack, relay, 1))
        
        # CH2 chassis + CH2A-K BACboards (12 total, needs 1.5 boards)
        mapping.append(('CH2', 1, 5, 2))
        for i, letter in enumerate('ABCDEFGHIJK'):
            if i < 3:
                stack = 1
                relay = 6 + i
            else:
                stack = 2
                relay = 1 + i - 3
            mapping.append((f'CH2{letter}', stack, relay, 2))
        
        # CH3 chassis + CH3A-K BACboards (12 total, needs 1.5 boards)
        mapping.append(('CH3', 3, 1, 3))
        for i, letter in enumerate('ABCDEFGHIJK'):
            stack = 3 if i < 7 else 4
            relay = (2 + i) if i < 7 else (1 + i - 7)
            mapping.append((f'CH3{letter}', stack, relay, 3))
        
        # CH4 chassis + CH4A-J BACboards (11 total, needs 1.375 boards)
        mapping.append(('CH4', 4, 5, 4))
        for i, letter in enumerate('ABCDEFGHIJ'):
            if i < 3:
                stack = 4
                relay = 6 + i
            else:
                stack = 5
                relay = 1 + i - 3
            mapping.append((f'CH4{letter}', stack, relay, 4))
        
        return mapping
    
    def _extract_controlled_chassis(self, full_mapping):
        """Extract and renumber mappings for only the chassis this Pi controls"""
        # Filter mappings to only include controlled chassis
        filtered = [m for m in full_mapping if m[3] in self.chassis_controlled]
        
        if not filtered:
            return []
        
        # Find the unique stack numbers used by controlled chassis
        used_stacks = sorted(set(m[1] for m in filtered))
        
        # Create a mapping from global stack numbers to local stack numbers
        stack_renumbering = {global_stack: local_idx 
                            for local_idx, global_stack in enumerate(used_stacks)}
        
        # Renumber stacks to start from 0
        result = []
        for switch_name, global_stack, relay, chassis_num in filtered:
            local_stack = stack_renumbering[global_stack]
            result.append((switch_name, local_stack, relay))
        
        return result
    
    def get_relay_position(self, switch_name):
        """
        Convert switch name to (stack, relay) position.
        
        Args:
            switch_name: Logical name like 'CH1', 'CH1A', etc.
        
        Returns:
            tuple: (stack, relay) or None if not found
        """
        return self._switch_to_relay.get(switch_name.upper())
    
    def get_switch_name(self, stack, relay):
        """
        Convert (stack, relay) position to switch name.
        
        Args:
            stack: Stack number (0-5)
            relay: Relay number (1-8)
        
        Returns:
            str: Switch name like 'CH1', 'CH1A', etc., or None if not mapped
        """
        return self._relay_to_switch.get((stack, relay))
    
    def get_all_switches(self):
        """Get list of all valid switch names"""
        return sorted(self._switch_to_relay.keys())
    
    def is_valid_switch(self, switch_name):
        """Check if a switch name is valid"""
        return switch_name.upper() in self._switch_to_relay


# Global switch mapper instance - uses configured chassis
switch_mapper = SwitchMapper(chassis_controlled=CHASSIS_CONTROLLED)


def create_app():
    app = Flask(__name__)

    @app.route('/')
    def index():
        """Render the web UI showing all relay states"""
        return render_template('index.html')
    
    @app.route('/api/status', methods=['GET'])
    def status_check():
        """Status check endpoint for main server to monitor this Pi"""
        return jsonify({
            'status': 'online',
            'pi_id': PI_ID,
            'chassis_controlled': CHASSIS_CONTROLLED,
            'num_relay_boards': NUM_STACKS,
            'relays_per_board': RELAYS_PER_BOARD,
            'total_switches': len(switch_mapper.get_all_switches()),
            'switches': switch_mapper.get_all_switches()
        })

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
