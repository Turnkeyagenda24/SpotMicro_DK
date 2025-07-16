import time

class Interpolator:
    def __init__(self, step_time=0.03, speed=0.1):
        self.last_update = time.time()
        self.current_positions = {}  # leg_id -> (x, y, z)
        self.speed = speed
        self.step_time = step_time

    def update(self, target_positions):
        now = time.time()
        if now - self.last_update < self.step_time:
            return self.current_positions  # No update yet

        new_positions = {}
        for leg_id, (tx, ty, tz) in target_positions.items():
            cx, cy, cz = self.current_positions.get(leg_id, (tx, ty, tz))
            nx = cx + (tx - cx) * self.speed
            ny = cy + (ty - cy) * self.speed
            nz = cz + (tz - cz) * self.speed
            new_positions[leg_id] = (nx, ny, nz)

        self.current_positions = new_positions
        self.last_update = now
        return new_positions
