import time

class Interpolator:
    """Smoothly interpolates leg positions toward target positions."""

    def __init__(self, step_time=0.03, speed=0.1):
        self.last_update = time.time()
        self.current_positions = {}  # leg_id -> (x, y, z)
        self.speed = speed
        self.step_time = step_time

    def update(self, target_positions):
        """
        Move current positions toward target positions by a fraction (self.speed).
        Only updates if enough time (self.step_time) has passed.
        Returns updated positions dict.
        """
        now = time.time()
        if now - self.last_update < self.step_time:
            return self.current_positions

        new_positions = {}
        for leg_id, target in target_positions.items():
            current = self.current_positions.get(leg_id, target)
            nx = current[0] + (target[0] - current[0]) * self.speed
            ny = current[1] + (target[1] - current[1]) * self.speed
            nz = current[2] + (target[2] - current[2]) * self.speed
            new_positions[leg_id] = (nx, ny, nz)

        self.current_positions = new_positions
        self.last_update = now
        return
