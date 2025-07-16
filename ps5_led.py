from dualsense_controller import DualSenseController
from time import sleep

controller = DualSenseController()

controller.activate()

# Set color to red
controller.lightbar.set_color(255, 0, 255)

try:
    while True:
        sleep(0.1)  # keep the script alive so the controller stays connected

except KeyboardInterrupt:
    print("Stopping controller...")
    controller.lightbar.set_color(0, 0, 0)
    sleep(1)
finally:
    controller.deactivate()  # cleanly stop the controller connection
