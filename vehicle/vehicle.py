import time
import maestro


class Vehicle:
    def __init__(self, dev="/dev/ttyACM0"):
        self._maestro = maestro.Controller(dev)

    def __del__(self):
        # Set car in a known state, so wheels don't keep spinning
        self.set_throttle(0)
        self.set_steering(0)
        self._maestro.close()

    def set_throttle(self, value):
        # Set throttle with value in range [-1, 1]

        # Clip input to [-1, 1]
        value = max(value, -1)
        value = min(value, 1)

        if value == 0:
            pwm = self.THR.STOP
        elif value > 0:
            pwm = self.THR.DEADBAND_F + value * 100
        elif value < 0:
            pwm = self.THR.DEADBAND_B + value * 100

        self._maestro.setTarget(self.THR.CH, pwm)

    def set_steering(self, value):
        # Set throttle with value in range [-1, 1]

        # Clip input to [-1, 1]
        value = max(value, -1)
        value = min(value, 1)

        if value == 0:
            pwm = self.STEER.CENTER
        else:
            pwm = self.STEER.CENTER + value * 2000

        self._maestro.setTarget(self.STEER.CH, pwm)

    class THR:
        # Throttle params
        CH = 0  # channel
        STOP = 5602  # us (pulse width at which the motor is stopped)
        DEADBAND_F = 5725  # (motors start turning slightly forward)
        DEADBAND_B = 5480  # (motors start turning slightly backward)

        FW = 5825  # go slowly forward
        BW = 5380  # go slowly backward

        FW_MAX = 8000
        BW_MAX = 4000

    class STEER:
        CH = 4
        CENTER = 6000  # center
        RIGHT = 8000  # left
        LEFT = 4000  # right


if __name__ == "__main__":

    # Test code

    vehicle = Vehicle()

    print("Forward...")
    vehicle.set_throttle(1)
    time.sleep(1)

    print("Stop...")
    vehicle.set_throttle(0)
    time.sleep(1)

    print("Back...")
    vehicle.set_throttle(-1)
    time.sleep(1)

    print("Stop...")
    vehicle.set_throttle(0)
    time.sleep(1)

    print("Left...")
    vehicle.set_steering(-1)
    time.sleep(1)

    print("Center...")
    vehicle.set_steering(1)
    time.sleep(1)

    print("Right...")
    vehicle.set_steering(1)
    time.sleep(1)

    print("Center...")
    vehicle.set_steering(1)
    time.sleep(1)
