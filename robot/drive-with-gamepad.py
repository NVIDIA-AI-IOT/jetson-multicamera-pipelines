import time

from controler.gamepad import ManualController
from vehicle.vehicle import Vehicle

MAX_RATE_HZ = 30

controller = ManualController()
vehicle = Vehicle()

try:
    while True:
        time.sleep(1 / MAX_RATE_HZ)
        v, theta = controller.t, controller.s
        print(f"v: {v:0.2f} th: {theta:0.2f}")

        vehicle.set_throttle(v)
        vehicle.set_steering(theta)

except KeyboardInterrupt:
    controller.stop()
    vehicle.stop()
