import socketio
import RPi.GPIO as GPIO


MOTOR_PIN = 18       # Broche GPIO utilisée pour le PWM
PWM_FREQUENCY = 800  # Fréquence du PWM en Hz

class RailCarController:
    def __init__(self, server_url):
        # Socket.IO client setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(MOTOR_PIN, GPIO.OUT)

        # GPIO & PWM setup
        self.pwm = GPIO.PWM(MOTOR_PIN, PWM_FREQUENCY)
        self.pwm.start(0)

        self.sio = socketio.Client()
        self.server_url = server_url
        self.sio.on('update_plot', self._on_sensor_update)

        self.last_voltage = 0.0
        self.current_duty_cycle = 0.0

        
    def connect(self):
        # Connect to Socket.IO server
        # Register callback for 'update_plot' event
        self.sio.connect(self.server_url)
        print(f"[Controller] Connected to {self.server_url}")
        
    def _on_sensor_update(self, data):
        # Callback pour Socket.IO
        # Update self.last_voltage
        try:
            self.last_voltage = float(data['value'])
        except (KeyError, ValueError) as e:
            print(f"[Controller] Error parsing voltage: {e}")
        
    def step(self, action):
        # Convert action (0.0-1.0) to duty cycle (0-95%)
        # Apply via GPIO PWM
        # Return current state dict

        self.current_duty_cycle = action * 95.0 # Max 95%
        self.pwm.ChangeDutyCycle(self.current_duty_cycle)
        return self.get_state()
        
    def get_state(self):
        return {
            'voltage': self.last_voltage,
            'current_duty_cycle': self.current_duty_cycle,
        }
        
    def reset(self):
        # Set duty cycle to 0
        # Maybe wait for stable voltage reading
        self.current_duty_cycle = 0.0
        self.pwm.ChangeDutyCycle(0.0)
        return self.get_state()
        
    def cleanup(self):
        # Stop PWM, cleanup GPIO
        # Disconnect Socket.IO
        self.pwm.stop()
        GPIO.cleanup()
        self.sio.disconnect()
