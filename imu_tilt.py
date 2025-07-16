import sys
import smbus2
sys.modules['smbus'] = smbus2

from mpu6050 import mpu6050
import math
import time

sensor = mpu6050(0x68)

alpha = 0.1
filtered_pitch = 0.0
filtered_roll = 0.0
first_run = True

def get_filtered_tilt():
    global filtered_pitch, filtered_roll, first_run

    accel = sensor.get_accel_data()
    ax = accel['x']
    ay = accel['y']
    az = accel['z']
    pitch = math.degrees(math.atan2(ax, math.sqrt(ay*ay + az*az)))
    roll = math.degrees(math.atan2(ay, math.sqrt(ax*ax + az*az)))

    if first_run:
        filtered_pitch = pitch
        filtered_roll = roll
        first_run = False
    else:
        filtered_pitch = alpha * pitch + (1 - alpha) * filtered_pitch
        filtered_roll = alpha * roll + (1 - alpha) * filtered_roll

    return filtered_pitch, filtered_roll
