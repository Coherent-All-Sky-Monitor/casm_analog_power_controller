from flask import Flask, jsonify, request, render_template
import lib8relind as relay

# Configuration for relay boards (8 relays per board)
# Stack levels 0-5 mapped to hardware jumper settings

# ⚠️ CURRENTLY TESTING WITH 1 BOARD (8 relays)
# When you get more boards, change NUM_STACKS to 6 for 48 total relays
NUM_STACKS = 1  # Change to 6 when you have all boards
RELAYS_PER_BOARD = 8


def create_app():
    app = Flask(__name__)

    @app.route('/')
    def index():
        """Render the web UI showing all relay states"""
        return render_template('index.html')

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

    return app
