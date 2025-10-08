from flask import Flask, jsonify, request, render_template

# Simulate 6 stacks of 8 relays each (48 total relays)
# State: 0 = OFF, 1 = ON
relay_state = {
    'stack_0': [0] * 8,
    'stack_1': [0] * 8,
    'stack_2': [0] * 8,
    'stack_3': [0] * 8,
    'stack_4': [0] * 8,
    'stack_5': [0] * 8,
}


def create_app():
    app = Flask(__name__)

    @app.route('/')
    def index():
        """Render the web UI showing all relay states"""
        return render_template('index.html')

    @app.route('/api/relay/<int:stack>/<int:relay>', methods=['GET'])
    def get_relay_state(stack, relay):
        """Get the state of a specific relay
        
        Args:
            stack: Stack number (0-5)
            relay: Relay number (1-8)
        
        Returns:
            JSON with relay state (0 or 1)
        """
        if stack < 0 or stack > 5:
            return jsonify({'error': 'Invalid stack. Must be 0-5'}), 400
        if relay < 1 or relay > 8:
            return jsonify({'error': 'Invalid relay. Must be 1-8'}), 400
        
        state = relay_state[f'stack_{stack}'][relay - 1]
        return jsonify({
            'stack': stack,
            'relay': relay,
            'state': state,
            'status': 'ON' if state == 1 else 'OFF'
        })

    @app.route('/api/relay/<int:stack>/<int:relay>', methods=['POST'])
    def set_relay_state(stack, relay):
        """Set the state of a specific relay
        
        Args:
            stack: Stack number (0-5)
            relay: Relay number (1-8)
        
        Body:
            JSON with 'state': 0 (OFF) or 1 (ON)
        
        Returns:
            JSON with updated relay state
        """
        if stack < 0 or stack > 5:
            return jsonify({'error': 'Invalid stack. Must be 0-5'}), 400
        if relay < 1 or relay > 8:
            return jsonify({'error': 'Invalid relay. Must be 1-8'}), 400
        
        data = request.get_json()
        if data is None or 'state' not in data:
            return jsonify({'error': 'Missing state in request body'}), 400
        
        new_state = data['state']
        if new_state not in [0, 1]:
            return jsonify({'error': 'State must be 0 (OFF) or 1 (ON)'}), 400
        
        # Update the relay state (simulating hardware control)
        relay_state[f'stack_{stack}'][relay - 1] = new_state
        
        return jsonify({
            'stack': stack,
            'relay': relay,
            'state': new_state,
            'status': 'ON' if new_state == 1 else 'OFF',
            'message': f'Stack {stack}, Relay {relay} turned {"ON" if new_state == 1 else "OFF"}'
        })

    @app.route('/api/relay/all', methods=['GET'])
    def get_all_relays():
        """Get the state of all relays"""
        return jsonify(relay_state)

    @app.route('/api/relay/stack/<int:stack>', methods=['GET'])
    def get_stack_state(stack):
        """Get the state of all relays in a specific stack
        
        Args:
            stack: Stack number (0-5)
        """
        if stack < 0 or stack > 5:
            return jsonify({'error': 'Invalid stack. Must be 0-5'}), 400
        
        return jsonify({
            'stack': stack,
            'relays': relay_state[f'stack_{stack}']
        })

    @app.route('/api/relay/reset', methods=['POST'])
    def reset_all_relays():
        """Turn off all relays"""
        for stack in relay_state:
            relay_state[stack] = [0] * 8
        
        return jsonify({
            'message': 'All relays turned OFF',
            'state': relay_state
        })

    return app

