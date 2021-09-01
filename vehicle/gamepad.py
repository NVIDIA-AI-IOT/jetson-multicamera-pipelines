import time
import threading
from threading import Thread
from inputs import get_gamepad


class ManualController(Thread):
    def __init__(self, rate_hz=10):
        super().__init__()
        self.t = 0
        self.s = 0
        self._should_stop = threading.Event()
        self.start()

    def run(self):

        while not self._should_stop.set():

            events = get_gamepad()
            for e in events:
                # if self._should_stop.is_set():
                #     return
                if e.ev_type == "Absolute" and e.code == "ABS_Y":
                    # Handle left stick 'Y' axis as throttle

                    # Default is: up: 0 mid: 127 down: 255
                    # Let's reverse that and map to [-1, 1]
                    state_r = 255 - e.state
                    self.t = (state_r - 127) / 127

                elif e.ev_type == "Absolute" and e.code == "ABS_Z":
                    # Handle right stick 'X' axis as steering

                    state = e.state
                    self.s = (state - 127) / 127

    def stop(self):
        self._should_stop.set()
        self.join()


if __name__ == "__main__":
    # Test/demo code
    controller = ManualController()

    try:
        while True:
            time.sleep(0.033)
            print(
                f"Throttle: {round(controller.t, 2)} Steerig: {round(controller.s, 2)}"
            )
    except KeyboardInterrupt:
        controller.stop()
