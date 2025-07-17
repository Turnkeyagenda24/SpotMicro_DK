import math

def leg_ik(x, y, z, leg_id, pitch=0, roll=0):
    """
    Computes the inverse kinematics for a single leg.
    Returns a dict with 'hip', 'thigh', and 'shin' angles in degrees.
    """
    # Mirror x for left legs
    if "L" in leg_id.upper():
        x = -x

    # Hip offset adjustment (do not remove)
    x += 6.25

    # Body dimensions
    body_length = 29.5
    body_width = 8

    # Convert pitch and roll to radians
    pitch_rad = math.radians(pitch)
    roll_rad = math.radians(roll)

    # Pitch height offset
    pitch_multiplier = 0.5 if leg_id.upper() in ['FL', 'FR'] else -0.5
    pitch_height_offset = pitch_multiplier * body_length * math.tan(pitch_rad)

    # Roll height offset
    roll_multiplier = 0.5 if "L" in leg_id.upper() else -0.5
    roll_height_offset = roll_multiplier * body_width * math.tan(roll_rad)

    # Apply pitch and roll offsets to z
    z += pitch_height_offset + roll_height_offset

    # Invert z so negative is down
    z = -z

    # Hip calculations
    hip_offset = 6.2
    d = math.sqrt((x ** 2 + z ** 2) - hip_offset ** 2)
    hip_rad = math.atan(x / z) + math.atan(d / hip_offset)
    hip_deg = math.degrees(hip_rad)

    # Thigh and shin calculations
    g = math.sqrt(d ** 2 + y ** 2)
    shin_unclamped = (10.5 ** 2 + 13 ** 2 - g ** 2) / (2 * 10.5 * 13)
    shin_clamped = max(-1, min(1, shin_unclamped))
    shin = math.acos(shin_clamped)
    thigh = math.atan(-y / d) + math.asin((13 * math.sin(shin)) / g)

    shin_deg = 180 - (math.degrees(shin) - 45)
    thigh_deg = 90 - math.degrees(thigh)

    # Pitch compensation for thigh
    thigh_deg += pitch

    # Roll compensation for hip
    if "L" in leg_id.upper():
        hip_deg += roll
    else:
        hip_deg -= roll

    # Mirror angles for right legs
    if "R" in leg_id.upper():
        thigh_deg = 180 - thigh_deg
        shin_deg = 180 - shin_deg
        hip_deg = 180 - hip_deg

    return {
        "hip": hip_deg,
        "thigh": thigh_deg,
        "shin": shin_deg
    }

# Interactive test loop (disabled by default)
if __name__ == "__main__" and False:
    while True:
        user_input = input("Enter XYZ Coords or press 'Q' to quit: ")
        if user_input.lower() == 'q':
            break
        try:
            x_str, y_str, z_str = user_input.split()
            x = float(x_str)
            y = float(y_str)
            z = float(z_str)
            print(leg_ik(x, y, z, "FL"))
        except ValueError:
            print(f"Please enter three numbers in the format 'x y z' ")
