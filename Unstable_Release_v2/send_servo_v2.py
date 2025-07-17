import json
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685

# Load servo offsets from file
with open("offsets2.json", "r") as f:
    offsets = json.load(f)

# Set up I2C and PCA9685 controller
i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = 330

def angle_to_pwm(angle):
    """
    Convert an angle in degrees (0-180) to a PWM duty cycle value.
    """
    pulse_min = 500
    pulse_max = 2500
    pulse_width = pulse_min + (angle / 180.0) * (pulse_max - pulse_min)
    duty_cycle = int(pulse_width * 65535 / 3030)  # 20ms period
    return duty_cycle

def set_servo(channel, angle):
    """
    Set the servo on the specified channel to the given angle, applying any offset.
    """
    offset = offsets.get(str(channel), 0)
    corrected_angle = max(0, min(180, angle + offset))
    pwm = angle_to_pwm(corrected_angle)
    pca.channels[channel].duty_cycle = pwm
    # Uncomment for debugging:
    # print(f"Channel {channel}: base={angle:.1f}, offset={offset}, final={corrected_angle:.1f}")

def safe_set_servo(channel, angle):
    """
    Set the servo safely, catching I/O errors.
    """
    try:
        set_servo(channel, angle)
    except OSError as e:
        print(f"[Servo Error] Failed to write to channel {channel} at angle {angle:.1f}: {e}")
