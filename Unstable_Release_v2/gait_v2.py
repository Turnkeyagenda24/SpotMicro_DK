import time

class GaitController:
    """Controls quadruped gait cycles and computes leg target positions."""

    # Gait parameters
    STEP_DURATION = 0.5      # Duration of a full step cycle per pair (seconds)
    LIFT_HEIGHT = 5          # Height to lift foot during swing phase
    PAIR_1 = ['FR', 'BL']    # Leg pairs for alternating gait
    PAIR_2 = ['FL', 'BR']

    # Leg order for crawl gait (phase offsets)
    LEG_ORDER = ['FL', 'FR', 'BR', 'BL']
    LEG_PHASE_OFFSETS = {'FL': 2, 'FR': 6, 'BR': 4, 'BL': 0}
    NUM_PHASES = 8           # Number of discrete phases in crawl gait

    def __init__(self):
        self.STEP_LENGTH = 0
        self.phase = 0.0
        self.start_time = time.time()
        self.just_started = True
        self.start_count = 0

    def square_step_phase(self, phase, base_x, base_y, base_z):
        """
        Computes the (x, y, z) target for a leg during its swing phase.
        Phase: 0–1 (normalized swing cycle).
        """
        swing_start_y = base_y - self.STEP_LENGTH

        if phase < 0.25:
            # Lift quickly
            z = base_z + self.LIFT_HEIGHT * (phase / 0.25)
            y = base_y if self.just_started else swing_start_y
        elif phase < 0.5:
            # Move forward
            z = base_z + self.LIFT_HEIGHT
            y = base_y + self.STEP_LENGTH * ((phase - 0.25) / 0.25)
        elif phase < 0.75:
            # Lower down
            z = base_z + self.LIFT_HEIGHT * (1 - (phase - 0.5) / 0.25)
            y = base_y + self.STEP_LENGTH
        else:
            # Move backward while foot is on ground
            z = base_z
            y = base_y + self.STEP_LENGTH * (1 - (phase - 0.75) / 0.25)

        return (base_x, y, z)

    def stance_slide_phase(self, phase, base_x, base_y, base_z):
        """
        Computes the (x, y, z) target for a leg during stance slide.
        Only slides back during last 25% of stance.
        """
        if phase < 0.75:
            return (base_x, base_y, base_z)
        else:
            progress = (phase - 0.75) / 0.25
            y = base_y - self.STEP_LENGTH * progress
            return (base_x, y, base_z)

    def get_crawl_targets(self, pos_x, pos_y, pos_z, hip_x_offsets, current_positions):
        """
        Computes target positions for all legs in crawl gait.
        Returns: dict leg_id -> (x, y, z)
        """
        now = time.time()
        elapsed = now - self.start_time
        total_cycle_time = self.STEP_DURATION * self.NUM_PHASES
        current_phase = (elapsed % total_cycle_time) / total_cycle_time  # 0–1 over full gait

        # Compute body shift for stability
        body_shift = 2
        left_phase = (current_phase - self.LEG_PHASE_OFFSETS['FL'] / self.NUM_PHASES) % 1.0
        right_phase = (current_phase - self.LEG_PHASE_OFFSETS['FR'] / self.NUM_PHASES) % 1.0
        left_legs_swinging = left_phase < 1.0 / self.NUM_PHASES
        right_legs_swinging = right_phase < 1.0 / self.NUM_PHASES

        if left_legs_swinging and not right_legs_swinging:
            body_shift_x = body_shift
        elif right_legs_swinging and not left_legs_swinging:
            body_shift_x = -body_shift
        else:
            body_shift_x = 0

        target_positions = {}
        for leg_id in self.LEG_ORDER:
            phase_offset = self.LEG_PHASE_OFFSETS[leg_id] / self.NUM_PHASES
            leg_phase = (current_phase - phase_offset) % 1.0
            is_swinging = leg_phase < 1.0 / self.NUM_PHASES

            base_x = pos_x + body_shift_x
            base_y = pos_y
            base_z = pos_z

            if is_swinging:
                swing_phase = leg_phase * self.NUM_PHASES  # normalize to 0–1
                target = self.square_step_phase(swing_phase, base_x, base_y, base_z)
            else:
                stance_phase = (leg_phase - 1 / self.NUM_PHASES) / (1 - 1 / self.NUM_PHASES)
                y = base_y + self.STEP_LENGTH / 2 - self.STEP_LENGTH * stance_phase
                z = base_z
                target = (base_x, y, z)

            target_positions[leg_id] = target

        return target_positions

    def get_walk_targets(self, pos_x, pos_y, pos_z, hip_x_offsets, current_positions, interpolation_tolerance=0.3, phase_increment=0.1):
        """
        Computes target positions for all legs in walk gait.
        Advances phase only if all legs are close to their targets.
        Returns: dict leg_id -> (x, y, z)
        """
        target_positions = {}
        all_close = True
        body_shift = 2

        for leg_id in self.LEG_ORDER:
            # Use hip_x_offsets if needed for per-leg base_x
            base_x = pos_x + hip_x_offsets.get(leg_id, 0)
            base_y = pos_y
            base_z = pos_z

            # Determine phase and swing/stance for each leg
            if leg_id in self.PAIR_1:
                leg_phase = self.phase % 1.0
            else:
                leg_phase = (self.phase + 0.5) % 1.0  # shift phase for pair 2

            in_swing = leg_phase < 0.5
            swing_phase = (leg_phase * 2) % 1.0  # Normalize to 0–1

            if in_swing:
                target = self.square_step_phase(swing_phase, base_x, base_y, base_z)
            elif swing_phase >= 0.75:
                target = self.stance_slide_phase(swing_phase, base_x, base_y, base_z)
            else:
                target = (base_x, base_y, base_z)

            target_positions[leg_id] = target

            # Check if current position is close to target
            cx, cy, cz = current_positions.get(leg_id, target)
            tx, ty, tz = target
            dist = ((tx - cx)**2 + (ty - cy)**2 + (tz - cz)**2)**0.5
            if dist > interpolation_tolerance:
                all_close = False

        # Advance phase only if all legs are close to their targets
        if all_close:
            self.phase = (self.phase + phase_increment) % 1.0
            if self.phase >= 0.5:
                self.just_started = False

        return
