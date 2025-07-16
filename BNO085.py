import time
import math
import board
import busio

# ──► NOTE: import from the .i2c sub‑module
from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x.enums import BNO_REPORT_ID_GAME_ROTATION_VECTOR

# ── I²C setup
i2c = busio.I2C(board.SCL, board.SDA)
sensor = BNO08X_I2C(i2c)

# enable the fused‑orientation (quaternion) report
sensor.enable_feature(0x05)

def quat_to_euler(w, x, y, z):
    pitch = math.degrees(math.asin(-2.0 * (x * z - w * y)))
    roll  = math.degrees(math.atan2(2.0 * (w * x + y * z),
                                    1.0 - 2.0 * (x * x + y * y)))
    yaw   = math.degrees(math.atan2(2.0 * (w * z + x * y),
                                    1.0 - 2.0 * (y * y + z * z)))
    return pitch, roll, yaw

print("BNO085 quaternion → Euler demo (Ctrl‑C to quit)\n")
while True:
    q = sensor.quaternion  # (w, x, y, z); returns None until first packet
    if q:
        pitch, roll, yaw = quat_to_euler(*q)
        print(f"Pitch {pitch:6.2f}°  Roll {roll:6.2f}°  Yaw {yaw:6.2f}°")
    time.sleep(0.1)
