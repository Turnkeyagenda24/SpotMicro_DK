import time
import math
import sys
import smbus2
sys.modules['smbus'] = smbus2

from mpu6050 import mpu6050

sensor = mpu6050(0x68)

def get_level_from_accel(accel):
    ax = accel['x']
    ay = accel['y']
    az = accel['z']
    pitch = math.degrees(math.atan2(ax, math.sqrt(ay*ay + az*az)))
    roll  = math.degrees(math.atan2(ay, math.sqrt(ax*ax + az*az)))
    return pitch, roll

# Low-pass filter smoothing factor (between 0 and 1, closer to 0 = more smoothing)
alpha = 0.1

filtered_pitch = 0.0
filtered_roll = 0.0
first_run = True

print("Detecting level orientation from gravity with smoothing...")

try:
    while True:
        accel = sensor.get_accel_data()
        pitch, roll = get_level_from_accel(accel)

        if first_run:
            filtered_pitch = pitch
            filtered_roll = roll
            first_run = False
        else:
            filtered_pitch = alpha * pitch + (1 - alpha) * filtered_pitch
            filtered_roll  = alpha * roll  + (1 - alpha) * filtered_roll

        print(f"PITCH: {filtered_pitch:.2f}°, ROLL: {filtered_roll:.2f}°")
        time.sleep(0.05)  # faster update rate
except KeyboardInterrupt:
    print("Exiting...")
