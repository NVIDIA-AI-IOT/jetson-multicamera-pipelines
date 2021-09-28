import logging
import time

# Gstreamer imports
import gi

gi.require_version("Gst", "1.0")
from gi.repository import GObject, Gst

from ..utils.gst import _err_if_none, _make_element_safe, _sanitize, bus_call


class BasePipeline:
    def __init__(self, **kwargs):

        # Gstreamer init
        GObject.threads_init()
        Gst.init(None)

        # create an event loop and feed gstreamer bus mesages to it
        self._mainloop = GObject.MainLoop()

        self._p = self._create_pipeline(**kwargs)
        self._log = logging.getLogger("jetvision")

        self._bus = self._p.get_bus()
        self._bus.add_signal_watch()
        self._bus.connect("message", bus_call, self._mainloop)

        # self.start()
        self._p.set_state(Gst.State.PLAYING)
        self.wait_ready()
        self._start_ts = time.perf_counter()

    # def run(self):

    #     try:
    #         self._mainloop.run()
    #     except KeyboardInterrupt:
    #         pass
    #     finally:
    #         self._mainloop.quit()
    #         self._p.set_state(Gst.State.NULL)

    def __del__(self):
        self.stop()

    def stop(self):
        self._p.set_state(Gst.State.NULL)

    def running(self):
        _, state, _ = self._p.get_state(1)
        return True if state == Gst.State.PLAYING else False

    def wait_ready(self):
        while not self.running():
            time.sleep(0.1)
