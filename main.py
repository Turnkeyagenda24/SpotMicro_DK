from leg_ik import leg_ik
from send_servo import set_servo

# Leg positions
leg_positions = {
    "FL": (0, 0, -16),
    "FR": (0, 0, -16),
    "BL": (0, 0, -16),
    "BR": (0, 0, -16)
}

pitch = 0
roll = 0

# Joint mapping to PCA9685
channel_map = {
    "FL": {"hip": 8, "thigh": 9, "shin": 10},
    "FR": {"hip": 12, "thigh": 13, "shin": 14},
    "BL": {"hip": 4, "thigh": 5, "shin": 6},
    "BR": {"hip": 0, "thigh": 1, "shin": 2}
}

# Calculate angles
angle_commands = {}
for leg_id, (x, y, z) in leg_positions.items():
    angle_commands[leg_id] = leg_ik(x, y, z, leg_id, pitch=pitch, roll=roll)

# Send to PCA9685
for leg_id, angles in angle_commands.items():
    set_servo(channel_map[leg_id]["hip"], angles["hip"])
    set_servo(channel_map[leg_id]["thigh"], angles["thigh"])
    set_servo(channel_map[leg_id]["shin"], angles["shin"])
