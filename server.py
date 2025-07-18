from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import time 
import pyray as raylib
import os
from circuit import SectionType as ST
from circuit import Circuit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  

real_circuit = Circuit([
    ST.SHORT, ST.SHORT, ST.TURN_RIGHT, ST.SHORT, ST.SHORT, ST.SHORT,
    ST.TURN_RIGHT, ST.TURN_LEFT, ST.SHORT, ST.TURN_LEFT, ST.SHORT,
    ST.TURN_RIGHT, ST.SHORT, ST.TURN_LEFT, ST.TURN_LEFT, ST.LONG,
    ST.LONG, ST.LONG, ST.LONG, ST.LONG, ST.LONG, ST.LONG,
    ST.TURN_LEFT, ST.SHORT, ST.SHORT, ST.SHORT, ST.TURN_LEFT,
    ST.LONG, ST.SHORT, ST.TURN_RIGHT, ST.TURN_LEFT, ST.TURN_LEFT,
])

latest_voltage = 0.0
latest_timestamp = 0.0

# Car state for visualization
car_state = {
    'position': {'x': 0, 'y': 0},
    'rail_distance': 0,
    'speed': 0,
    'tangent': {'x': 1, 'y': 0},
    'crashed': False
}

def generate_circuit_image(circuit, output_path, width=800, height=600):
    """Generate circuit image at server startup"""
    # Create static directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Initialize raylib with minimal window
    raylib.init_window(1, 1, "Hidden")
    raylib.set_target_fps(60)
    
    # Create render texture
    render_texture = raylib.load_render_texture(width, height)
    
    # Render to texture
    raylib.begin_texture_mode(render_texture)
    raylib.clear_background(raylib.WHITE)
    
    circuit.draw()
    
    raylib.end_texture_mode()
    
    # Export texture as image
    image = raylib.load_image_from_texture(render_texture.texture)
    raylib.export_image(image, output_path)
    
    # Cleanup
    raylib.unload_image(image)
    raylib.unload_render_texture(render_texture)
    raylib.close_window()
    
    print(f"Circuit image generated: {output_path}")

def get_circuit_bounds():
    """Calculate circuit bounds for coordinate mapping"""
    # Sample points along the circuit to find bounds
    positions = []
    rail_length = real_circuit._outside_rail_length
    
    for i in range(0, int(rail_length), 10):
        pos = real_circuit.get_position_at_rail(i, False)
        positions.append((pos.x, pos.y))
    
    x_coords = [p[0] for p in positions]
    y_coords = [p[1] for p in positions]
    
    return {
        'min_x': min(x_coords), 'max_x': max(x_coords),
        'min_y': min(y_coords), 'max_y': max(y_coords)
    }

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/circuit_bounds')
def circuit_bounds():
    return jsonify(get_circuit_bounds())

@app.route('/control', methods=['POST'])
def control_motor():
    data = request.get_json()
    duty_cycle = data.get('duty_cycle', 0.0)
    
    # Forward to controller via Socket.IO
    socketio.emit('motor_control', {'duty_cycle': duty_cycle})
    
    return jsonify({'status': 'success', 'duty_cycle': duty_cycle})

@app.route('/sensor_data', methods=['POST'])
def receive_data():
    global latest_voltage, latest_timestamp
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No JSON data received'}), 400
            
        value = data.get('value', None)
        timestamp = data.get('timestamp', None)
        latest_voltage = value
        latest_timestamp = timestamp

        if value is not None and timestamp is not None: 
            # Send to controller
            socketio.emit('update_plot', {'value': value})
            socketio.emit('to_controller', {'value': value, 'timestamp': timestamp})
            
            # Send sensor data to dashboard at 1Hz
            socketio.emit('sensor_update', {
                'voltage': value,
                'timestamp': timestamp
            })
            
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error', 'message': 'Invalid data'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/car_position', methods=['POST'])
def receive_car_position():
    """Receive car position from vision system"""
    global car_state
    try:
        data = request.get_json()
        rail_distance = data.get('rail_distance', 0)
        
        # Get position and tangent from circuit
        position = real_circuit.get_position_at_rail(rail_distance, True)  # Use inside rail
        tangent = real_circuit.get_tangent_at_rail(rail_distance, True)
        
        car_state.update({
            'position': {'x': position.x, 'y': position.y},
            'rail_distance': rail_distance,
            'tangent': {'x': tangent.x, 'y': tangent.y},
            'timestamp': time.time()
        })
        
        # Emit car position at high frequency (10-20Hz)
        socketio.emit('car_position_update', car_state)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/training_data', methods=['POST'])
def receive_training_data():
    """Receive Q-learning training data"""
    try:
        data = request.get_json()
        
        # Emit training data at 1Hz
        socketio.emit('training_update', {
            'state': data.get('state'),
            'action': data.get('action'), 
            'reward': data.get('reward'),
            'crashed': data.get('crashed', False),
            'episode': data.get('episode', 0),
            'timestamp': time.time()
        })
        
        # Update car crash state
        if data.get('crashed'):
            car_state['crashed'] = True
            socketio.emit('car_crashed', car_state)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/sensors', methods=['GET'])  
def get_sensors():
    return jsonify({
        'voltage': latest_voltage,
        'timestamp': latest_timestamp
    })

if __name__ == '__main__':
    # Generate circuit image at startup
    print("Generating circuit visualization...")
    generate_circuit_image(real_circuit, "static/circuit.png", 800, 600)
    
    print("Starting server...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
