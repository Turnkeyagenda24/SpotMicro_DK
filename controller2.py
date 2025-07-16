import pygame
import time

# Initialize pygame and joystick
pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("No joystick detected!")
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()

print("Starting controller. Use joystick to move leg. Ctrl+C to quit.")

# Movement limits (adjust to your dog’s range)
X_MIN, X_MAX = -5, 5  # cm
Y_MIN, Y_MAX = -5, 5
Z_MIN, Z_MAX = -20, -12

deadzone = 0.05

def map_range(value, in_min, in_max, out_min, out_max):
    return out_min + (value - in_min) * (out_max - out_min) / (in_max - in_min)

try:
    while True:
        pygame.event.pump()

        # Read joystick axes (adjust indices if needed)
        rx = -joystick.get_axis(3)  # Right stick X
        ry = -joystick.get_axis(4)  # Right stick Y
        # For height, you can use triggers or left stick Y if you want; here just zero:
        # lz = joystick.get_axis(4) or similar

        # Apply deadzone
        rx = 0 if abs(rx) < deadzone else rx
        ry = 0 if abs(ry) < deadzone else ry

        # Map joystick values to position ranges
        pos_x = map_range(rx, -1, 1, X_MIN, X_MAX)
        pos_y = map_range(ry, -1, 1, Y_MIN, Y_MAX)
        pos_z = -15  # Static default height

        # Print leg coordinates for front-left leg (FL)
        print(f"Leg FL coords: x={pos_x:.2f}, y={pos_y:.2f}, z={pos_z:.2f}")

        time.sleep(0.05)

except KeyboardInterrupt:
    print("Exiting controller.")
    pygame.quit()
