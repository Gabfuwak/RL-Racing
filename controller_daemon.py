import socketio
import RPi.GPIO as GPIO
import time

def run_controller():
    # GPIO setup
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(18, GPIO.OUT)
    pwm = GPIO.PWM(18, 800)
    pwm.start(0)

    # Socket.IO client
    sio = socketio.Client()

    @sio.on('motor_control')
    def on_motor_control(data):
        duty_cycle = data.get('duty_cycle', 0.0)
        pwm.ChangeDutyCycle(duty_cycle)
        print(f"[Controller] PWM set to {duty_cycle}%")

    try:
        sio.connect("http://10.98.93.56:5000")
        print("[Controller] Connected, listening for commands...")

        # Keep alive loop
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("[Controller] Shutting down...")
    finally:
        pwm.stop()
        GPIO.cleanup()
        sio.disconnect()

if __name__ == "__main__":
    run_controller()
