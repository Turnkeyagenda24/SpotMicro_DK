import pygame

# Initialize Pygame and Joystick
pygame.init()
pygame.joystick.init()

# Check for controller
if pygame.joystick.get_count() == 0:
    print("No controller detected.")
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()

print(f"Using controller: {joystick.get_name()}")
print("Move sticks, press buttons, or D-pad to see mappings. Press CTRL+C to stop.\n")

try:
    while True:
        pygame.event.pump()

        # Axes (sticks and triggers)
        for i in range(joystick.get_numaxes()):
            axis_val = joystick.get_axis(i)
            if abs(axis_val) > 0.05:  # deadzone
                print(f"Axis {i}: {axis_val:.2f}")

        # Buttons (face, bumpers, etc.)
        for i in range(joystick.get_numbuttons()):
            if joystick.get_button(i):
                print(f"Button {i} pressed")

        # Hats (D-pad)
        for i in range(joystick.get_numhats()):
            hat_val = joystick.get_hat(i)
            if hat_val != (0, 0):
                print(f"Hat {i}: {hat_val}")

        pygame.time.wait(100)

except KeyboardInterrupt:
    print("\nExiting.")
    pygame.quit()
