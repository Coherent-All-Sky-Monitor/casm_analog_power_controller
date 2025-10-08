from flask import Flask, jsonify, request, render_template
import lib8relind as SM8relind

# Configuration for relay boards (8 relays per board)
# Stack levels 0-5 mapped to hardware jumper settings
# I2C port: 1 = Raspberry Pi default

# ⚠️ CURRENTLY TESTING WITH 1 BOARD (8 relays)
# When you get more boards, change NUM_STACKS to 6 for 48 total relays
NUM_STACKS = 1  # Change to 6 when you have all boards
RELAYS_PER_BOARD = 8
I2C_PORT = 1

# Initialize relay card objects for each stack
relay_cards = {}

def init_relay_cards():
    """Initialize all relay cards on startup"""
    global relay_cards
    for stack in range(NUM_STACKS):
        try:
            # Initialize card with stack level and I2C port
            relay_cards[stack] = SM8relind.SM8relind(stack=stack, i2c=I2C_PORT)
            print(f"✓ Initialized Stack {stack} (8 relays)")
        except Exception as e:
            print(f"✗ Error initializing Stack {stack}: {e}")
            # Create a mock object if hardware is not available
            relay_cards[stack] = None


def create_app():
    app = Flask(__name__)
    
    # Initialize hardware on app startup
    with app.app_context():
        init_relay_cards()

    @app.route('/')
    def index():
        """Render the web UI showing all relay states"""
        return render_template('index.html')

    @app.route('/api/relay/<int:stack>/<int:relay>', methods=['GET'])
    def get_relay_state(stack, relay):
        """Get the state of a specific relay
        
        Args:
            stack: Stack number (currently 0, will be 0-5 when all boards arrive)
            relay: Relay number (1-8)
        
        Returns:
            JSON with relay state (0 or 1)
        """
        if stack < 0 or stack >= NUM_STACKS:
            return jsonify({'error': f'Invalid stack. Must be 0-{NUM_STACKS-1}'}), 400
        if relay < 1 or relay > RELAYS_PER_BOARD:
            return jsonify({'error': f'Invalid relay. Must be 1-{RELAYS_PER_BOARD}'}), 400
        
        card = relay_cards.get(stack)
        if card is None:
            return jsonify({'error': f'Stack {stack} not initialized or hardware unavailable'}), 503
        
        try:
            # Get relay state from hardware (returns 0 or 1)
            state = card.get(relay)
            return jsonify({
                'stack': stack,
                'relay': relay,
                'state': state,
                'status': 'ON' if state == 1 else 'OFF'
            })
        except Exception as e:
            return jsonify({'error': f'Failed to read relay state: {str(e)}'}), 500

    @app.route('/api/relay/<int:stack>/<int:relay>', methods=['POST'])
    def set_relay_state(stack, relay):
        """Set the state of a specific relay
        
        Args:
            stack: Stack number (currently 0, will be 0-5 when all boards arrive)
            relay: Relay number (1-8)
        
        Body:
            JSON with 'state': 0 (OFF) or 1 (ON)
        
        Returns:
            JSON with updated relay state
        """
        if stack < 0 or stack >= NUM_STACKS:
            return jsonify({'error': f'Invalid stack. Must be 0-{NUM_STACKS-1}'}), 400
        if relay < 1 or relay > RELAYS_PER_BOARD:
            return jsonify({'error': f'Invalid relay. Must be 1-{RELAYS_PER_BOARD}'}), 400
        
        data = request.get_json()
        if data is None or 'state' not in data:
            return jsonify({'error': 'Missing state in request body'}), 400
        
        new_state = data['state']
        if new_state not in [0, 1]:
            return jsonify({'error': 'State must be 0 (OFF) or 1 (ON)'}), 400
        
        card = relay_cards.get(stack)
        if card is None:
            return jsonify({'error': f'Stack {stack} not initialized or hardware unavailable'}), 503
        
        try:
            # Set relay state on hardware
            card.set(relay, new_state)
            
            return jsonify({
                'stack': stack,
                'relay': relay,
                'state': new_state,
                'status': 'ON' if new_state == 1 else 'OFF',
                'message': f'Stack {stack}, Relay {relay} turned {"ON" if new_state == 1 else "OFF"}'
            })
        except Exception as e:
            return jsonify({'error': f'Failed to set relay state: {str(e)}'}), 500

    @app.route('/api/relay/all', methods=['GET'])
    def get_all_relays():
        """Get the state of all relays across all stacks"""
        all_states = {}
        
        for stack in range(NUM_STACKS):
            card = relay_cards.get(stack)
            if card is None:
                all_states[f'stack_{stack}'] = {'error': 'Not initialized'}
                continue
            
            try:
                # Get all 8 relays as bitmap, then convert to list
                bitmap = card.get_all()
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
        
        card = relay_cards.get(stack)
        if card is None:
            return jsonify({'error': f'Stack {stack} not initialized or hardware unavailable'}), 503
        
        try:
            # Get all 8 relays as bitmap, then convert to list
            bitmap = card.get_all()
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

    @app.route('/api/relay/reset', methods=['POST'])
    def reset_all_relays():
        """Turn off all relays across all stacks"""
        results = {}
        
        for stack in range(NUM_STACKS):
            card = relay_cards.get(stack)
            if card is None:
                results[f'stack_{stack}'] = 'Not initialized'
                continue
            
            try:
                # Set all relays to 0 (OFF) using bitmap
                card.set_all(0)
                results[f'stack_{stack}'] = 'All relays OFF'
            except Exception as e:
                results[f'stack_{stack}'] = f'Error: {str(e)}'
        
        return jsonify({
            'message': 'Reset command sent to all stacks',
            'results': results
        })

    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Check the health status of all relay cards"""
        status = {}
        for stack in range(NUM_STACKS):
            card = relay_cards.get(stack)
            status[f'stack_{stack}'] = 'connected' if card is not None else 'unavailable'
        
        return jsonify({
            'status': 'ok',
            'stacks': status
        })

    return app
