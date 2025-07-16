#!/usr/bin/env python3
"""
BNO085  ▸  fast‑read, filtered Pitch/Roll with robust I²C handling
"""
import math, time, threading, queue, warnings, sys
import board, busio
from adafruit_bno08x import BNO_REPORT_GAME_ROTATION_VECTOR
from adafruit_bno08x.i2c import BNO08X_I2C

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
READ_PERIOD   = 0.01      #  10 ms  FIFO‑drain interval
PRINT_PERIOD  = 0.50      #  0.5 s  display / control loop
EMA_ALPHA     = 0.15      #  Low‑pass: 0→heavy, 1→none
MAX_ERR_COUNT = 5         #  auto‑reset sensor after this many I²C errors
QUEUE_LIMIT   = 100       #  safety cap (drops oldest)

# ─────────────────────────────────────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────────────────────────────────────
warnings.filterwarnings("ignore", category=RuntimeWarning)

i2c = busio.I2C(board.SCL, board.SDA)
bno = BNO08X_I2C(i2c)
bno.enable_feature(BNO_REPORT_GAME_ROTATION_VECTOR)

def quat_to_pitch_roll(w, x, y, z):
    roll  = math.atan2(2*(w*x + y*z), 1 - 2*(x*x + y*y))
    sinp  = 2*(w*y - z*x)
    pitch = math.asin(max(-1, min(1, sinp)))
    return math.degrees(pitch), math.degrees(roll)

def unwrap_angle(a, last):
    if last is None:
        return a
    d = a - last
    if   d > 180:  a -= 360
    elif d < -180: a += 360
    return a

def wrap_for_print(a):
    """Map any angle to the neat −180…+180 range."""
    return (a + 180) % 360 - 180

# ─────────────────────────────────────────────────────────────────────────────
# SENSOR READER THREAD
# ─────────────────────────────────────────────────────────────────────────────
quat_q = queue.Queue()
def sensor_reader():
    """Continuously read quaternions and push to queue, resilient to I²C errors."""
    err_streak = 0
    while True:
        try:
            qi, qj, qk, qr = bno.game_quaternion
            if quat_q.qsize() > QUEUE_LIMIT:      # drop oldest to cap memory
                try: quat_q.get_nowait()
                except queue.Empty: pass
            quat_q.put((qi, qj, qk, qr))
            err_streak = 0                        # successful read → reset counter

        except (KeyError, OSError):               # unknown packet or I²C hiccup
            err_streak += 1
            if err_streak >= MAX_ERR_COUNT:
                try:
                    print("[WARN] consecutive I²C errors – soft‑resetting BNO085")
                    bno.soft_reset()
                    time.sleep(0.2)
                    bno.enable_feature(BNO08X_I2C.BNO_REPORT_GAME_ROTATION_VECTOR)
                    err_streak = 0
                except Exception as e:
                    print(f"[ERR ] soft‑reset failed: {e}")
                    err_streak = 0
            time.sleep(0.02)                      # brief back‑off, then retry
            continue

        time.sleep(READ_PERIOD)

threading.Thread(target=sensor_reader, daemon=True).start()

# ─────────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────────────────────────────────────
last_pitch = last_roll = None    # for unwrap
filt_pitch = filt_roll = None    # for EMA
t0 = time.monotonic()

while True:
    # Wait until next display tick
    while time.monotonic() - t0 < PRINT_PERIOD:
        time.sleep(0.01)
    t0 = time.monotonic()

    # Drain queue → convert all to pitch/roll
    pitches, rolls = [], []
    while True:
        try:
            qi, qj, qk, qr = quat_q.get_nowait()
        except queue.Empty:
            break
        p, r = quat_to_pitch_roll(qr, qi, qj, qk)
        p = unwrap_angle(p, last_pitch)
        r = unwrap_angle(r, last_roll)
        last_pitch, last_roll = p, r
        pitches.append(p)
        rolls.append(r)

    if not pitches:
        print("[WARN] No quaternion data available.")
        continue

    # Average samples in this half‑second
    avg_pitch = sum(pitches) / len(pitches)
    avg_roll  = sum(rolls)  / len(rolls)

    # Exponential moving average (optional)
    if filt_pitch is None:
        filt_pitch, filt_roll = avg_pitch, avg_roll
    else:
        filt_pitch = (1 - EMA_ALPHA) * filt_pitch + EMA_ALPHA * avg_pitch
        filt_roll  = (1 - EMA_ALPHA) * filt_roll  + EMA_ALPHA * avg_roll

    # Neatly wrapped for display
    disp_pitch = wrap_for_print(filt_pitch)
    disp_roll  = wrap_for_print(filt_roll)

    print(f"Pitch: {disp_pitch:7.2f}°\tRoll: {disp_roll:7.2f}°")
