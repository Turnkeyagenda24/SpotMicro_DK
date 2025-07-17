import pygame
import time
from leg_ik import leg_ik
from send_servo import set_servo, safe_set_servo
from dualsense_controller import DualSenseController
from interpolation import Interpolator
import gait

# === CONSTANTS ===
MODE_TRANSLATE = "translate"
MODE_ROTATE = "rotate"
MODE_WALK = "walk"
MODE_TOGGLE_BUTTON = 1

BASE_HEIGHT = -16

SMOOTHING_SPEED = 0.2
DEADZONE = 0.05

X_MIN, X_MAX = -10, 10
Y_MIN, Y_MAX = -10, 10
Z_MIN, Z_MAX = -22, -11
PITCH_MIN, PITCH_MAX = -10, 20
ROLL_MIN, ROLL_MAX = -20, 20
YAW_MIN, YAW_MAX = -20, 20
STEP_LENGTH_MIN, STEP_LENGTH_MAX = -5, 5

CHANNEL_MAP = {
    "FL": {"hip": 8, "thigh": 9, "shin": 10},
    "FR": {"hip": 12, "thigh": 13, "shin": 14},
    "BL": {"hip": 4, "thigh": 5, "shin": 6},
    "BR": {"hip": 0, "thigh": 1, "shin": 2}
}

HIP_X_OFFSETS = {
    "FL": 6.2,
    "FR": -6.2,
    "BL": 6.2,
    "BR": -6.2
}

# === UTILITY FUNCTIONS ===
def map_range(value, in_min, in_max, out_min, out_max):
    return out_min + (value - in_min) * (out_max - out_min) / (in_max - in_min)

def map_joystick_separate(value, neg_min, pos_max):
    if value < 0:
        return neg_min + (value + 1) * (0 - neg_min)
    else:
        return value * pos_max

def apply_deadzone(value, deadzone=DEADZONE):
    return 0 if abs(value) < deadzone else value

def calculate_offset(angle, ratio=1.0, cap=5.9):
    offset = angle * ratio
    return max(min(offset, cap), -cap)

# === MODE HANDLERS ===
def handle_translate(rx, ry, ly):
    pos_x = map_range(rx, -1, 1, X_MIN, X_MAX)
    pos_y = map_range(ry, -1, 1, Y_MIN, Y_MAX)
    pos_z = map_range(-ly, -1, 1, Z_MIN, Z_MAX)
    return pos_x, pos_y, pos_z, 0, 0, 0

def handle_rotate(joystick):
    pitch = map_joystick_separate(joystick.get_axis(4), PITCH_MIN, PITCH_MAX)
    roll = -map_range(joystick.get_axis(0), -1, 1, ROLL_MIN, ROLL_MAX)
    return 0, 0, BASE_HEIGHT, pitch, roll, 0

def handle_walk(ry, gait_controller):
    step_length = -map_range(ry, -1, 1, STEP_LENGTH_MIN, STEP_LENGTH_MAX)
    gait_controller.STEP_LENGTH = step_length
    return 0, 0, BASE_HEIGHT, 0, 0, 0

# === MAIN CONTROLLER ===
def main():
    # Initialize
    pygame.init()
    pygame.joystick.init()
    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    controller_led = DualSenseController()
    controller_led.activate()

    interpolator = Interpolator(step_time=0.005, speed=0.7)
    gait_controller = gait.GaitController()

    mode = MODE_TRANSLATE
    mode_toggle_ready = True

    pos_x = pos_y = 0
    pos_z = BASE_HEIGHT
    smoothed_pos_x = pos_x
    smoothed_pos_y = pos_y
    smoothed_pos_z = pos_z

    try:
        while True:
            pygame.event.pump()
            pressed = joystick.get_button(MODE_TOGGLE_BUTTON)

            # Set your desired offsets here
            cog_x_offset = 0
            cog_y_offset = 2  # Try positive or negative values to see the effect

            # Mode toggle logic
            if pressed and mode_toggle_ready:
                if mode == MODE_TRANSLATE:
                    mode = MODE_ROTATE
                elif mode == MODE_ROTATE:
                    mode = MODE_WALK
                else:
                    mode = MODE_TRANSLATE
                mode_toggle_ready = False
            elif not pressed:
                mode_toggle_ready = True

            # Read joystick axes
            rx = apply_deadzone(-joystick.get_axis(3))
            ry = apply_deadzone(joystick.get_axis(4))
            ly = apply_deadzone(-joystick.get_axis(1))

            # Mode handling
            if mode == MODE_TRANSLATE:
                pos_x, pos_y, pos_z, pitch, roll, yaw = handle_translate(rx, ry, ly)
                controller_led.lightbar.set_color(0, 180, 60)
            elif mode == MODE_ROTATE:
                pos_x, pos_y, pos_z, pitch, roll, yaw = handle_rotate(joystick)
                controller_led.lightbar.set_color(255, 200, 50)
            elif mode == MODE_WALK:
                pos_x, pos_y, pos_z, pitch, roll, yaw = handle_walk(ry, gait_controller)
                controller_led.lightbar.set_color(255, 0, 0)
                # IMU/CoG compensation could be added here if needed
                # cog_x_offset = 0
                # cog_y_offset = 0

            # Smoothing
            smoothed_pos_x += (pos_x - smoothed_pos_x) * SMOOTHING_SPEED
            smoothed_pos_y += (pos_y - smoothed_pos_y) * SMOOTHING_SPEED
            smoothed_pos_z += (pos_z - smoothed_pos_z) * SMOOTHING_SPEED

            # Target leg positions
            if mode == MODE_WALK:
                raw_targets = gait_controller.get_crawl_targets(
                    pos_x, pos_y, BASE_HEIGHT, HIP_X_OFFSETS, interpolator.current_positions
                )
                target_leg_positions = interpolator.update(raw_targets)
            else:
                target_leg_positions = {}
                for leg_id in ['FL', 'FR', 'BL', 'BR']:
                    hip_offset = HIP_X_OFFSETS[leg_id]
                    rel_x = smoothed_pos_x - hip_offset
                    target_leg_positions[leg_id] = (rel_x, smoothed_pos_y, smoothed_pos_z)

            # Apply global offsets to all leg positions
            for leg_id in target_leg_positions:
                x, y, z = target_leg_positions[leg_id]
                x += cog_x_offset
                y += cog_y_offset
                target_leg_positions[leg_id] = (x, y, z)

            # Send servo commands
            for leg_id, (x, y, z) in target_leg_positions.items():
                if mode == MODE_WALK:
                    angles = leg_ik(x, y, z, leg_id, pitch, roll)
                else:
                    offset_smoothed_pos_y = smoothed_pos_y + cog_y_offset
                    angles = leg_ik(smoothed_pos_x, offset_smoothed_pos_y, smoothed_pos_z, leg_id, pitch, roll)
                safe_set_servo(CHANNEL_MAP[leg_id]["hip"], angles["hip"])
                safe_set_servo(CHANNEL_MAP[leg_id]["thigh"], angles["thigh"])
                safe_set_servo(CHANNEL_MAP[leg_id]["shin"], angles["shin"])

            time.sleep(0.02)

    except KeyboardInterrupt:
        controller_led.lightbar.set_color(0, 0, 0)
        print("Controller stopped by user")

if __name__ == "__main__":
    main()
