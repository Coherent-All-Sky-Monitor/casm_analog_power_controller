from flask import Flask, jsonify, request, render_template
import yaml
import requests
from pathlib import Path
import time
from threading import Thread, Lock
import sqlite3
from datetime import datetime
import json

# Load main server configuration
def load_config():
    """Load configuration from main_config.yaml"""
    config_path = Path(__file__).parent.parent / 'main_config.yaml'
    
    if not config_path.exists():
            raise FileNotFoundError(
                f"Main server config not found at {config_path}. "
                "Please create main_config.yaml with Raspberry Pi addresses."
            )
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            print(f"✅ Loaded main server config from {config_path}")
            return config
    except Exception as e:
        raise Exception(f"Error loading config: {e}")

# Load configuration
CONFIG = load_config()
RASPBERRY_PIS = CONFIG.get('raspberry_pis', {})
STATUS_CHECK_INTERVAL = CONFIG.get('status_check_interval', 30)
REQUEST_TIMEOUT = CONFIG.get('request_timeout', 5)

# Status cache
pi_status_cache = {}
pi_status_lock = Lock()

# Initialize status logging database
def init_status_db():
    """Create SQLite database for status check history"""
    db_path = Path(__file__).parent.parent / 'status_history.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create status_checks table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS status_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            datetime TEXT NOT NULL,
            pi_id TEXT NOT NULL,
            status TEXT NOT NULL,
            chassis_list TEXT,
            error_msg TEXT,
            response_time_ms REAL,
            pi_response TEXT
        )
    ''')
    
    # Add chassis_list column if it doesn't exist (migration for existing databases)
    try:
        cursor.execute('ALTER TABLE status_checks ADD COLUMN chassis_list TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    conn.commit()
    conn.close()
    print(f"✅ Status logging database initialized: {db_path}")

# Initialize database on module load
init_status_db()

def log_status_check(pi_id, status, chassis_list=None, error_msg=None, response_time_ms=None, pi_response=None):
    """Log a status check result to the database"""
    db_path = Path(__file__).parent.parent / 'status_history.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    timestamp = time.time()
    datetime_str = datetime.fromtimestamp(timestamp).isoformat()
    
    # Extract chassis_list from pi_response if available
    if pi_response and isinstance(pi_response, dict):
        chassis_list = pi_response.get('chassis_controlled', chassis_list)
    
    # Store chassis_list as JSON string if it's a list
    if chassis_list and isinstance(chassis_list, (list, dict)):
        chassis_list = json.dumps(chassis_list)
    
    # Store pi_response as JSON string if provided
    if pi_response and isinstance(pi_response, dict):
        pi_response = json.dumps(pi_response)
    
    cursor.execute('''
        INSERT INTO status_checks 
        (timestamp, datetime, pi_id, status, chassis_list, error_msg, response_time_ms, pi_response)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, datetime_str, pi_id, status, chassis_list, error_msg, response_time_ms, pi_response))
    
    conn.commit()
    conn.close()


class PiRouter:
    """Routes switch requests to the appropriate Raspberry Pi with relay mappings"""
    
    def __init__(self, pi_config):
        """
        Initialize the router with Pi configuration.
        
        Args:
            pi_config: Dictionary of Pi configurations from main_config.yaml
        """
        self.pi_config = pi_config
        self._build_switch_mappings()
    
    def _build_switch_mappings(self):
        """Build mappings from switch names to Pi addresses AND relay positions"""
        self.switch_to_pi = {}  # switch_name -> pi_url
        self.switch_to_relay = {}  # switch_name -> {pi_url, hat, relay}
        self.chassis_to_pi = {}  # chassis_num -> pi_info
        
        for pi_id, pi_data in self.pi_config.items():
            ip = pi_data.get('ip_address')
            port = pi_data.get('port', 5001)
            chassis_list = pi_data.get('chassis', [])
            switch_mapping = pi_data.get('switch_mapping', {})
            
            pi_url = f"http://{ip}:{port}"
            
            # Map each chassis to this Pi
            for chassis_num in chassis_list:
                self.chassis_to_pi[chassis_num] = {
                    'pi_id': pi_id,
                    'pi_url': pi_url,
                    'ip': ip,
                    'port': port
                }
            
            # Map each switch to its Pi URL and relay position
            for switch_name, relay_pos in switch_mapping.items():
                self.switch_to_pi[switch_name.upper()] = pi_url
                self.switch_to_relay[switch_name.upper()] = {
                    'pi_url': pi_url,
                    'hat': relay_pos.get('hat'),
                    'relay': relay_pos.get('relay')
                }
    
    def get_relay_info(self, switch_name):
        """
        Get complete relay information for a switch (Pi URL, HAT, relay).
        
        Args:
            switch_name: Logical switch name (e.g., 'CH1', 'CH1A')
        
        Returns:
            dict: {'pi_url': str, 'hat': int, 'relay': int} or None
        """
        return self.switch_to_relay.get(switch_name.upper())
    
    def get_pi_for_switch(self, switch_name):
        """
        Get the Pi URL for a given switch name.
        
        Args:
            switch_name: Switch name like 'CH1', 'CH1A', etc.
        
        Returns:
            str: URL of the Pi, or None if not found
        """
        return self.switch_to_pi.get(switch_name.upper())
    
    def get_pi_for_chassis(self, chassis_num):
        """
        Get the Pi info for a given chassis number.
        
        Args:
            chassis_num: Chassis number (1-4)
        
        Returns:
            dict: Pi information, or None if not found
        """
        return self.chassis_to_pi.get(chassis_num)
    
    def get_all_switches(self):
        """Get list of all valid switch names across all Pis"""
        return sorted(self.switch_to_pi.keys())


# Global router instance
router = PiRouter(RASPBERRY_PIS)


def forward_to_pi(pi_url, endpoint, method='GET', data=None, timeout=None):
    """
    Forward an HTTP request to a Raspberry Pi.
    
    Args:
        pi_url: URL of the Pi
        endpoint: API endpoint (e.g., '/api/switch/CH1')
        method: HTTP method ('GET' or 'POST')
        data: JSON data for POST requests
        timeout: Request timeout in seconds
    
    Returns:
        tuple: (response_json, status_code) or (error_dict, error_code)
    """
    if timeout is None:
        timeout = REQUEST_TIMEOUT
    
    full_url = f"{pi_url}{endpoint}"
    
    try:
        if method == 'GET':
            response = requests.get(full_url, timeout=timeout)
        elif method == 'POST':
            response = requests.post(full_url, json=data, timeout=timeout)
        else:
            return {'error': f'Unsupported method: {method}'}, 400
        
        # Return the Pi's response
        try:
            return response.json(), response.status_code
        except:
            return {'response': response.text}, response.status_code
            
    except requests.exceptions.Timeout:
        return {
            'error': f'Request to {pi_url} timed out after {timeout}s',
            'pi_url': pi_url
        }, 504
    except requests.exceptions.ConnectionError:
        return {
            'error': f'Could not connect to Pi at {pi_url}',
            'pi_url': pi_url,
            'suggestion': 'Check if Pi is online and accessible'
        }, 503
    except Exception as e:
        return {
            'error': f'Failed to communicate with Pi: {str(e)}',
            'pi_url': pi_url
        }, 500


def check_pi_status():
    """Background task to periodically check status of all Pis"""
    while True:
        try:
            for pi_id, pi_data in RASPBERRY_PIS.items():
                ip = pi_data.get('ip_address')
                port = pi_data.get('port', 5001)
                pi_url = f"http://{ip}:{port}"
                
                # Measure response time
                start_time = time.time()
                
                try:
                    response = requests.get(
                        f"{pi_url}/api/status",
                        timeout=REQUEST_TIMEOUT
                    )
                    response_time_ms = (time.time() - start_time) * 1000
                    status = 'online' if response.status_code == 200 else 'error'
                    
                    with pi_status_lock:
                        pi_status_cache[pi_id] = {
                            'status': status,
                            'last_check': time.time(),
                            'response': response.json() if response.status_code == 200 else None,
                            'pi_url': pi_url
                        }
                    
                    # Log the status check
                    if response.status_code == 200:
                        pi_response = response.json()
                    else:
                        pi_response = None
                    log_status_check(pi_id, status, error_msg=None, 
                                   response_time_ms=response_time_ms, pi_response=pi_response)
                    
                except Exception as e:
                    response_time_ms = (time.time() - start_time) * 1000
                    error_msg = str(e)
                    
                    with pi_status_lock:
                        pi_status_cache[pi_id] = {
                            'status': 'offline',
                            'last_check': time.time(),
                            'error': error_msg,
                            'pi_url': pi_url
                        }
                    
                    # Log the failure
                    log_status_check(pi_id, 'offline', error_msg=error_msg, 
                                   response_time_ms=response_time_ms, pi_response=None)
                    
        except Exception as e:
            print(f"Error in status check thread: {e}")
        
        time.sleep(STATUS_CHECK_INTERVAL)


def create_app():
    app = Flask(__name__)
    
    # Start status monitoring thread
    status_thread = Thread(target=check_pi_status, daemon=True)
    status_thread.start()

    @app.route('/')
    def index():
        """Render the web UI showing all relay states"""
        return render_template('index.html')
    
    @app.route('/api/status', methods=['GET'])
    def status_check():
        """Status check endpoint showing status of main server and all Pis"""
        with pi_status_lock:
            pi_statuses = dict(pi_status_cache)
        
        # Merge config data with status data
        merged_statuses = {}
        for pi_id, pi_config in RASPBERRY_PIS.items():
            status_data = pi_statuses.get(pi_id, {'status': 'unknown'})
            merged_statuses[pi_id] = {
                'ip_address': pi_config.get('ip_address'),
                'port': pi_config.get('port', 5001),
                'chassis': pi_config.get('chassis', []),
                'description': pi_config.get('description', ''),
                **status_data  # Merge in status, last_check, error, response, etc.
            }
            # Add response data if available
            if status_data.get('response'):
                pi_response = status_data['response']
                merged_statuses[pi_id]['total_switches'] = pi_response.get('total_switches')
                merged_statuses[pi_id]['response_time'] = (time.time() - status_data.get('last_check', time.time())) * 1000
        
        all_online = all(
            pi.get('status') == 'online' 
            for pi in merged_statuses.values()
        )
        
        return jsonify({
            'main_server_status': 'online',
            'all_pis_online': all_online,
            'raspberry_pis': merged_statuses,
            'total_pis': len(RASPBERRY_PIS),
            'total_switches': len(router.get_all_switches())
        })
    
    # ========== Switch Name Based API Endpoints ==========
    
    @app.route('/api/switch/<switch_name>', methods=['GET'])
    def get_switch_state(switch_name):
        """Get the state of a switch by its logical name (e.g., CH1, CH1A)"""
        pi_url = router.get_pi_for_switch(switch_name)
        
        if pi_url is None:
            return jsonify({
                'error': f'Invalid switch name: {switch_name}',
                'valid_switches': router.get_all_switches()
            }), 400
        
        response, status_code = forward_to_pi(
            pi_url, 
            f'/api/switch/{switch_name}',
            method='GET'
        )
        
        return jsonify(response), status_code
    
    @app.route('/api/switch/<switch_name>', methods=['POST'])
    def set_switch_state(switch_name):
        """Set the state of a switch by its logical name"""
        relay_info = router.get_relay_info(switch_name)
        
        if relay_info is None:
            return jsonify({
                'error': f'Invalid switch name: {switch_name}',
                'valid_switches': router.get_all_switches()
            }), 400
        
        data = request.get_json()
        if data is None or 'state' not in data:
            return jsonify({'error': 'Missing state in request body'}), 400
        
        # Send complete relay instruction to Pi (hat, relay, state)
        pi_data = {
            'switch_name': switch_name.upper(),
            'hat': relay_info['hat'],
            'relay': relay_info['relay'],
            'state': data['state']
        }
        
        response, status_code = forward_to_pi(
            relay_info['pi_url'],
            f'/api/relay/control',  # New endpoint on Pi that accepts full instructions
            method='POST',
            data=pi_data
        )
        
        return jsonify(response), status_code
    
    # ========== Direct Relay Control via Main Server ==========
    
    @app.route('/api/relay/<pi_id>/<int:hat>/<int:relay>', methods=['POST'])
    def control_relay_by_number(pi_id, hat, relay):
        """
        Control a relay by Pi ID, HAT number, and relay number through main server.
        This allows direct hardware control without knowing switch names.
        
        Args:
            pi_id: Pi identifier (e.g., 'pi_1', 'pi_2')
            hat: HAT number (0-based, e.g., 0, 1, 2)
            relay: Relay number (1-based, e.g., 1-8)
        
        Body:
            {"state": 0 or 1}
        
        Example:
            POST /api/relay/pi_1/0/1 with {"state": 1}
            -> Controls Pi 1, HAT 0, Relay 1 (turns ON)
        """
        # Validate Pi ID
        if pi_id not in RASPBERRY_PIS:
            return jsonify({
                'error': f'Invalid Pi ID: {pi_id}',
                'valid_pis': list(RASPBERRY_PIS.keys())
            }), 400
        
        # Get Pi info
        pi_config = RASPBERRY_PIS[pi_id]
        ip = pi_config.get('ip_address')
        port = pi_config.get('port', 5001)
        pi_url = f"http://{ip}:{port}"
        
        # Validate HAT and relay numbers
        num_hats = pi_config.get('num_relay_hats', 3)
        if hat < 0 or hat >= num_hats:
            return jsonify({'error': f'Invalid HAT number. Must be 0-{num_hats-1}'}), 400
        
        if relay < 1 or relay > 8:
            return jsonify({'error': 'Invalid relay number. Must be 1-8'}), 400
        
        # Get state from request
        data = request.get_json()
        if data is None or 'state' not in data:
            return jsonify({'error': 'Missing state in request body'}), 400
        
        state = data['state']
        if state not in [0, 1]:
            return jsonify({'error': 'State must be 0 or 1'}), 400
        
        # Send direct relay control to Pi (relay is already 1-based, no conversion!)
        pi_data = {
            'switch_name': f'{pi_id}_HAT{hat}_R{relay}',  # Descriptive name
            'hat': hat,
            'relay': relay,
            'state': state
        }
        
        response, status_code = forward_to_pi(
            pi_url,
            f'/api/relay/control',
            method='POST',
            data=pi_data
        )
        
        return jsonify(response), status_code
    
    @app.route('/api/relay/<pi_id>/<int:hat>/<int:relay>', methods=['GET'])
    def get_relay_state_by_number(pi_id, hat, relay):
        """
        Get the state of a relay by Pi ID, HAT number, and relay number.
        
        Args:
            pi_id: Pi identifier (e.g., 'pi_1', 'pi_2')
            hat: HAT number (0-based)
            relay: Relay number (1-based, 1-8)
        
        Example:
            GET /api/relay/pi_1/0/1
            -> Gets state of Pi 1, HAT 0, Relay 1
        """
        # Validate Pi ID
        if pi_id not in RASPBERRY_PIS:
            return jsonify({
                'error': f'Invalid Pi ID: {pi_id}',
                'valid_pis': list(RASPBERRY_PIS.keys())
            }), 400
        
        # Get Pi info
        pi_config = RASPBERRY_PIS[pi_id]
        ip = pi_config.get('ip_address')
        port = pi_config.get('port', 5001)
        pi_url = f"http://{ip}:{port}"
        
        # Validate HAT and relay numbers
        num_hats = pi_config.get('num_relay_hats', 3)
        if hat < 0 or hat >= num_hats:
            return jsonify({'error': f'Invalid HAT number. Must be 0-{num_hats-1}'}), 400
        
        if relay < 1 or relay > 8:
            return jsonify({'error': 'Invalid relay number. Must be 1-8'}), 400
        
        # Forward to Pi (relay is already 1-based, no conversion needed!)
        response, status_code = forward_to_pi(
            pi_url,
            f'/api/relay/{hat}/{relay}',
            method='GET'
        )
        
        return jsonify(response), status_code
    
    # ========== Switch List and Chassis Endpoints ==========
    
    @app.route('/api/switch/list', methods=['GET'])
    def list_all_switches():
        """Get a list of all valid switch names and their current states from all Pis"""
        all_switches = {}
        errors = []
        
        # Group switches by Pi to minimize requests
        pi_to_switches = {}
        for switch_name in router.get_all_switches():
            pi_url = router.get_pi_for_switch(switch_name)
            if pi_url not in pi_to_switches:
                pi_to_switches[pi_url] = []
            pi_to_switches[pi_url].append(switch_name)
        
        # Query each Pi once for all its switches
        for pi_url, switches in pi_to_switches.items():
            response, status_code = forward_to_pi(
                pi_url,
                '/api/switch/list',
                method='GET'
            )
            
            if status_code == 200 and isinstance(response, dict):
                # Extract switches from Pi response (response format: {"switches": {...}})
                pi_switches = response.get('switches', {})
                all_switches.update(pi_switches)
            else:
                errors.append({
                    'pi_url': pi_url,
                    'error': response.get('error', 'Unknown error')
                })
        
        result = {'switches': all_switches}
        if errors:
            result['errors'] = errors
        
        return jsonify(result)
    
    @app.route('/api/switch/chassis/<int:chassis_num>', methods=['GET'])
    def get_chassis_switches(chassis_num):
        """Get all switches for a specific chassis"""
        if chassis_num < 1 or chassis_num > 4:
            return jsonify({'error': 'Chassis number must be 1-4'}), 400
        
        pi_info = router.get_pi_for_chassis(chassis_num)
        
        if pi_info is None:
            return jsonify({
                'error': f'No Pi configured to control chassis {chassis_num}',
                'available_chassis': sorted(router.chassis_to_pi.keys())
            }), 404
        
        response, status_code = forward_to_pi(
            pi_info['pi_url'],
            f'/api/switch/chassis/{chassis_num}',
            method='GET'
        )
        
        return jsonify(response), status_code
    
    # ========== Direct Relay Control (if needed for debugging) ==========
    
    @app.route('/api/pis', methods=['GET'])
    def list_pis():
        """List all configured Raspberry Pis and their status"""
        pi_list = []
        
        with pi_status_lock:
            pi_statuses = dict(pi_status_cache)
        
        for pi_id, pi_data in RASPBERRY_PIS.items():
            status = pi_statuses.get(pi_id, {'status': 'unknown'})
            
            pi_list.append({
                'pi_id': pi_id,
                'ip_address': pi_data.get('ip_address'),
                'port': pi_data.get('port', 5001),
                'chassis': pi_data.get('chassis', []),
                'status': status.get('status'),
                'last_check': status.get('last_check'),
                'pi_url': f"http://{pi_data.get('ip_address')}:{pi_data.get('port', 5001)}"
            })
        
        return jsonify({
            'raspberry_pis': pi_list,
            'total': len(pi_list)
        })
    
    @app.route('/api/status/history', methods=['GET'])
    def status_history():
        """Get status check history from the database"""
        pi_id_filter = request.args.get('pi_id')
        limit = request.args.get('limit', 100)
        
        try:
            limit = int(limit)
        except ValueError:
            limit = 100
        
        db_path = Path(__file__).parent.parent / 'status_history.db'
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dicts
        cursor = conn.cursor()
        
        if pi_id_filter:
            cursor.execute('''
                SELECT * FROM status_checks 
                WHERE pi_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (pi_id_filter, limit))
        else:
            cursor.execute('''
                SELECT * FROM status_checks 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Convert rows to list of dicts
        history = []
        for row in rows:
            history.append({
                'id': row['id'],
                'timestamp': row['timestamp'],
                'datetime': row['datetime'],
                'pi_id': row['pi_id'],
                'status': row['status'],
                'chassis_list': row['chassis_list'],
                'error_msg': row['error_msg'],
                'response_time_ms': row['response_time_ms'],
                'pi_response': row['pi_response']
            })
        
        return jsonify({
            'history': history,
            'count': len(history)
        })
    
    @app.route('/api/status/stats', methods=['GET'])
    def status_stats():
        """Get status statistics for all Pis"""
        pi_id_filter = request.args.get('pi_id')
        
        db_path = Path(__file__).parent.parent / 'status_history.db'
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if pi_id_filter:
            cursor.execute('''
                SELECT 
                    pi_id,
                    status,
                    COUNT(*) as count,
                    AVG(response_time_ms) as avg_response_time
                FROM status_checks
                WHERE pi_id = ?
                GROUP BY pi_id, status
            ''', (pi_id_filter,))
        else:
            cursor.execute('''
                SELECT 
                    pi_id,
                    status,
                    COUNT(*) as count,
                    AVG(response_time_ms) as avg_response_time
                FROM status_checks
                GROUP BY pi_id, status
            ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        stats = {}
        for row in rows:
            pi_id = row['pi_id']
            if pi_id not in stats:
                stats[pi_id] = {}
            stats[pi_id][row['status']] = {
                'count': row['count'],
                'avg_response_time_ms': round(row['avg_response_time'], 2) if row['avg_response_time'] else None
            }
        
        return jsonify({'stats': stats})

    return app

