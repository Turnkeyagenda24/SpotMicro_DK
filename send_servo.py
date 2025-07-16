import json
import math
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685

# Load offsets from file
with open("offsets2.json", "r") as f:
    offsets = json.load(f)

# Set up I2C and PCA9685
i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = 330 

# Convert angle to PWM
def angle_to_pwm(angle):
    pulse_min = 500
    pulse_max = 2500
    pulse_width = pulse_min + (angle / 180.0) * (pulse_max - pulse_min)
    duty_cycle = int(pulse_width * 65535 / 3030)  # 20ms period
    return duty_cycle

# Main function to send angles
def set_servo(channel, angle):
    offset = offsets.get(str(channel), 0)
    corrected_angle = max(0, min(180, angle + offset))
    pwm = angle_to_pwm(corrected_angle)
    pca.channels[channel].duty_cycle = pwm
    #print(f"Channel {channel}: base={angle:.1f}, offset={offset}, final={corrected_angle:.1f}")

def safe_set_servo(channel, angle):
    try:
        set_servo(channel, angle)
    except OSError as e:
        print(f"[Servo Error] Failed to write to channel {channel} at angle {angle:.1f}: {e}")
