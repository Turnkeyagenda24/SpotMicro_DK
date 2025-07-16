import math

def leg_ik(x, y, z, leg_id, pitch=0, roll=0):

    if "L" in leg_id.upper():
         x = -x

    # Important line, dont delete
    x = x + 6.25

    # Body dimensions
    body_length = 29.5
    body_width = 8

    pitch_rad = math.radians(pitch)
    roll_rad = math.radians(roll)

    # Calculate pitch height offset
    if leg_id.upper() in ['FL', 'FR']:
        pitch_multiplier = +0.5
    else:
        pitch_multiplier = -0.5

    pitch_height_offset = pitch_multiplier * body_length * math.tan(pitch_rad)

    # Calculate roll height offset
    if "L" in leg_id.upper():
        roll_multiplier = +0.5
    else:
        roll_multiplier = -0.5

    roll_height_offset = roll_multiplier * body_width * math.tan(roll_rad)

    #Final vertical offset with pitch and roll
    z = z + pitch_height_offset + roll_height_offset

    # Switch Z so negative is down
    z = -z

    #print(f"Leg {leg_id} coords before IK: x={x}, y={y}, z={z}, pitch={pitch}")

    # Hip calculations
    hip_offset = 6.2
    d = math.sqrt((x**2 + z**2) - hip_offset**2)
    hip_rad = math.atan(x / z) + math.atan(d / hip_offset)
    hip_deg = math.degrees(hip_rad)

    # Find the new height after adjusting for Y
    g = math.sqrt(d**2 + y**2) 
    shin_unclamped = (10.5**2 + 13**2 - g**2) / (2 * 10.5 * 13)
    shin_clamped = max(-1, min(1, shin_unclamped))
    shin = math.acos(shin_clamped)

    thigh = math.atan(-y / d) + math.asin((13 * math.sin(shin)) / g)

    shin_deg = 180 - (math.degrees(shin) - 45)
    thigh_deg = 90 - math.degrees(thigh)

    # Pitch compensation for thigh
    thigh_deg += pitch

    if "L" in leg_id.upper():
        hip_deg += roll
    else:
        hip_deg -= roll

    # Roll compensation for hip
    #hip_deg += roll

    if "R" in leg_id.upper():
        thigh_deg = 180 - thigh_deg
        shin_deg = 180 - shin_deg
        hip_deg = 180 - hip_deg

    #print(f"New leg height should be {d} to maintain a height of {z} ")
    #print(f"Hip servo should be set to {hip_deg} degrees.")
    #print(f"New leg height should be {g} to maintain height of {z}")
    #print(f"Thigh servo should be set to {thigh_deg} and shin servo should be set to {shin_deg} ")

    return {
        "hip": hip_deg,
        "thigh": thigh_deg,
        "shin": shin_deg
    }

while False:
    user_input = input("Enter XYZ Coords or press 'Q' to quit: ")
    if user_input.lower() == 'q':
        break

    try:
        x_str, y_str, z_str = user_input.split()
        x = float(x_str)
        y = float(y_str)
        z = float(z_str)

        leg_IK(x, y, z, "FL")

    except ValueError:
        print(f"Please enter three numbers in the format 'x y z' ")
