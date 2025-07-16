import math

def apply_rotation(x, y, z, leg_id, pitch=0, roll=0, yaw=0, body_dims=(29.5, 8)):

    length, width = body_dims
    dx = {"FL": -length/2, "FR": -length/2, "BL": length/2, "BR": length/2}[leg_id]
    dy = {"FL": width/2, "FR": -width/2, "BL": width/2, "BR": -width/2}[leg_id]

    # Convert angles to radians
    pitch_rad = math.radians(pitch)
    roll_rad = math.radians(roll)
    yaw_rad = math.radians(yaw)

    # ---- Pitch & Roll vertical shift ----
    dz_pitch = dx * math.tan(pitch_rad)
    dz_roll = dy * math.tan(roll_rad)
    dz = dz_pitch + dz_roll

    # ---- Apply Yaw (rotates x/y coords around center) ----
    cos_yaw = math.cos(yaw_rad)
    sin_yaw = math.sin(yaw_rad)
    x_rot = x * cos_yaw - y * sin_yaw
    y_rot = x * sin_yaw + y * cos_yaw

    return x_rot, y_rot, z + dz
