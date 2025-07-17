import pygame
import time
from leg_ik import leg_ik
from send_servo import set_servo, safe_set_servo
from rotation import apply_rotation
from dualsense_controller import DualSenseController
from interpolation import Interpolator
import gait

mode = "translate" # or "rotate"
mode_toggle_button = 1
mode_toggle_ready = True

BASE_HEIGHT = -16
pos_z = -16

pos_x = pos_y = 0

smoothing_speed = 0.2
smoothed_pos_x = pos_x
smoothed_pos_y = pos_y
smoothed_pos_z = pos_z

interpolator = Interpolator(step_time=0.005, speed=0.7)

gait_controller = gait.GaitController()

# Initialize joystick
pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()

# Init DualSnse LED system
controller_led = DualSenseController()
controller_led.activate()

# Roll compensation
ROLL_TILT_AMOUNT = 0.8

# Movement limits (cm)
X_MIN, X_MAX = -10, 10
Y_MIN, Y_MAX = -10, 10
Z_MIN, Z_MAX = -22, -11

PITCH_MIN, PITCH_MAX = -10, 20
ROLL_MIN, ROLL_MAX = -20, 20
YAW_MIN, YAW_MAX = -20, 20

STEP_LENGTH_MIN, STEP_LENGTH_MAX = -5, 5

# Starting position (cm)
pos_x, pos_y, pos_z = 0, 0, -15

# Servo channel mapping
channel_map = {
    "FL": {"hip": 8, "thigh": 9, "shin": 10},
    "FR": {"hip": 12, "thigh": 13, "shin": 14},
    "BL": {"hip": 4, "thigh": 5, "shin": 6},
    "BR": {"hip": 0, "thigh": 1, "shin": 2}
}

# Hip X positions relative to body center (in cm)
hip_x_offsets = {
    "FL": 6.2,
    "FR": -6.2,
    "BL": 6.2,
    "BR": -6.2
}


# Movement scaling factor
delta_scale = 0.1

try:
    while True:
        pygame.event.pump()
        pressed = joystick.get_button(mode_toggle_button)

        if pressed and mode_toggle_ready:
            if mode == "translate":
                mode = "rotate"
            elif mode == "rotate":
                mode = "walk"
            else:
                mode = "translate"

            mode_toggle_ready = False
        elif not pressed:
            mode_toggle_ready = True

        rx = -joystick.get_axis(3)
        ry = joystick.get_axis(4)
        ly = -joystick.get_axis(1)
        lx = joystick.get_axis(0)
	# Deadzone

        deadzone = 0.05

        def calculate_offset(angle, ratio=1.0, cap=5.9):
            offset = angle * ratio
            if offset > cap:
                offset = cap
            elif offset < -cap:
                offset = -cap
            return offset

        def map_range(value, in_min, in_max, out_min, out_max):
            # Linearly map a value from one range to another
            return out_min + (value - in_min) * (out_max - out_min) / (in_max - in_min)

        def map_joystick_separate(value, neg_min, pos_max):
            if value < 0:
                return neg_min + (value + 1) * (0 - neg_min)
            else:
                return value * pos_max

	# If within deadzone, be zero
        rx = 0 if abs(rx) < deadzone else rx
        ry = 0 if abs(ry) < deadzone else ry
        ly = 0 if abs(ly) < deadzone else ly

        # Map joysticks based on mode
        if mode == "translate":

            # Map joystick values directly to position
            pos_x = map_range(rx, -1, 1, X_MIN, X_MAX)
            pos_y = map_range(ry, -1, 1, Y_MIN, Y_MAX)
            pos_z = map_range(-ly, -1, 1, Z_MIN, Z_MAX)  # Invert so pushing up raises dog
            pitch = 0
            roll = 0
            yaw = 0
            controller_led.lightbar.set_color(0, 180, 60)

        elif mode == "rotate":

            # Map joysticks to rotation
            pitch = map_joystick_separate(joystick.get_axis(4), PITCH_MIN, PITCH_MAX)
            roll = -map_range(joystick.get_axis(0), -1, 1, ROLL_MIN, ROLL_MAX)
            yaw = 0
            pos_x = 0
            pos_y = 0
            pos_z = BASE_HEIGHT
            controller_led.lightbar.set_color(255, 200, 50)

        elif mode == "walk":
            STEP_LENGTH = -map_range(ry, -1, 1, STEP_LENGTH_MIN, STEP_LENGTH_MAX)
            gait_controller.STEP_LENGTH = STEP_LENGTH
            pos_x = 0
            pos_y = 0
            pos_z = BASE_HEIGHT
            pitch = 0
            roll = 0
            yaw = 0
            controller_led.lightbar.set_color(255, 0, 0)

            filtered_pitch = 0.0
            filtered_roll = 0.0
            alpha = 0.1

            #imu_pitch, imu_roll = imu.get()

            cog_x_offset = 0

            #target_offset = imu_roll * 1
            #target_offset = max(min(target_offset, 4), -4)

            cog_y_offset = 0
            #cog_y_offset = calculate_offset(imu_pitch, ratio=0.5, cap=3.0)

            #if 'filtered_cog_x_offset' not in globals():
                #filtered_cog_x_offset = target_offset
            #else:
                #filtered_cog_x_offset = alpha * target_offset + (1 - alpha) * filtered_cog_x_offset

            #cog_x_offset = filtered_cog_x_offset

        smoothed_pos_x += (pos_x - smoothed_pos_x) * smoothing_speed
        smoothed_pos_y += (pos_y - smoothed_pos_y) * smoothing_speed
        smoothed_pos_z += (pos_z - smoothed_pos_z) * smoothing_speed

        # Build leg target positions relative to body position
        if mode == "walk":
            corrected_pos_y = pos_y + cog_y_offset
            corrected_pos_x = pos_x + cog_x_offset
            raw_targets = gait_controller.get_crawl_targets(pos_x, pos_y, BASE_HEIGHT, hip_x_offsets, interpolator.current_positions)
            target_leg_positions = interpolator.update(raw_targets)

            for leg_id in target_leg_positions:
                x, y, z = target_leg_positions[leg_id]
                x += cog_x_offset
                target_leg_positions[leg_id] = (x, y, z)

        else:
            target_leg_positions = {}
            for leg_id in ['FL', 'FR', 'BL', 'BR']:
                hip_offset = hip_x_offsets[leg_id]
                rel_x = smoothed_pos_x - hip_offset
                target_leg_positions[leg_id] = (rel_x, smoothed_pos_y, smoothed_pos_z)

        # For each leg, calculate angles and send commands
        for leg_id, (x, y, z) in target_leg_positions.items():

            # Leg stuff
            if mode == "walk":
                angles = leg_ik(x, y, z, leg_id, pitch, roll)
            else:
                angles = leg_ik(smoothed_pos_x, smoothed_pos_y, smoothed_pos_z, leg_id, pitch, roll)
            safe_set_servo(channel_map[leg_id]["hip"], angles["hip"])
            safe_set_servo(channel_map[leg_id]["thigh"], angles["thigh"])
            safe_set_servo(channel_map[leg_id]["shin"], angles["shin"])

        time.sleep(0.02)

except KeyboardInterrupt:
    controller_led.lightbar.set_color(0, 0, 0)
    #imu.stop()
    print("Controller stopped by user")

