from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import time 

app = Flask(__name__)
socketio = SocketIO(app)  

latest_voltage = 0.0
latest_timestamp = 0.0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/control', methods=['POST'])
def control_motor():
    data = request.get_json()
    duty_cycle = data.get('duty_cycle', 0.0)
    
    # Forward au contrôleur via Socket.IO
    socketio.emit('motor_control', {'duty_cycle': duty_cycle})
    
    return jsonify({'status': 'success', 'duty_cycle': duty_cycle})


@app.route('/sensor_data', methods=['POST'])
def receive_data():
    global latest_voltage, latest_timestamp
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No JSON data received'}), 400
        #Données envoyes par le capteur
        value = data.get('value', None)
        timestamp = data.get('timestamp',None)
        latest_voltage = value
        latest_timestamp = timestamp

        if value is not None and timestamp is not None: 
            #print(f"Received value: {value}")  
            #Envoyer au Raspberry pi 
            socketio.emit('update_plot',  {'value': value})
            socketio.emit('to_controller', {'value':value, 'timestamp': timestamp})
            return jsonify({'status': 'success'})
        else:
            #print("Invalid data received")  
            return jsonify({'status': 'error', 'message': 'Invalid data'}), 400
    except Exception as e:
        #print(f"Error: {e}")  
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/sensors', methods=['GET'])  
def get_sensors():
    return jsonify({
        'voltage': latest_voltage,
        'timestamp': latest_timestamp
    })

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)

