import threading
import time
from imu_tilt import get_filtered_tilt

class IMUReader:
    def __init__(self, update_rate=50):
        self.pitch = 0.0
        self.roll = 0.0
        self.running = True
        self.update_interval = 1.0 / update_rate
        self.thread = threading.Thread(target=self._update_loop)
        self.thread.daemon = True
        self.thread.start()

    def _update_loop(self):
        while self.running:
            try:
                self.pitch, self.roll = get_filtered_tilt()
            except OSError as e:
                print("IMU read failed:", e)
            time.sleep(self.update_interval)

    def stop(self):
        self.running = False
        self.thread.join()

    def get(self):
        return self.pitch, self.roll
