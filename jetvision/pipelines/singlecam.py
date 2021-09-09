import logging  # TODO: print -> logging
import sys
import os
import time
from threading import Thread

import cv2

# Gstreamer imports
import gi
import numpy as np

gi.require_version("Gst", "1.0")
from gi.repository import GObject, Gst

from ..gstutils import _err_if_none, _make_element_safe, _sanitize, bus_call
from .bins import make_nvenc_bin, make_argus_camera_configured, make_v4l2_cam_bin


class CameraPipeline(Thread):
    def __init__():
        pass

    def __init__(self, camera):
        """
        models parameter can be:
        - `dict`: mapping of models->sensor-ids to infer on
        - `list`: list of models to use on frames from all cameras
        """

        super().__init__()

        # Gstreamer init
        GObject.threads_init()
        Gst.init(None)

        save_h264_path = "/home/nx/logs/videos"
        os.makedirs(save_h264_path, exist_ok=True)

        # create an event loop and feed gstreamer bus mesages to it
        self._mainloop = GObject.MainLoop()

        self._p = self._make_singlecam_pipeline(camera)

        self._bus = self._p.get_bus()
        self._bus.add_signal_watch()
        self._bus.connect("message", bus_call, self._mainloop)

        self.start()
        self.wait_ready()

    def _make_singlecam_pipeline(self, camera, filepath=None):

        pipeline = _sanitize(Gst.Pipeline())
        cam = make_argus_camera_configured(camera)
        tee = _make_element_safe("tee")
        h264sink = make_nvenc_bin(f"/home/nx/logs/videos/jetvision-singlecam.mkv")
        
        nvvidconv = _make_element_safe("nvvideoconvert")
        nvvidconv_cf = _make_element_safe("capsfilter")
        # Ensure we output something nvvideoconvert has caps for
        nvvidconv_cf.set_property(
            "caps", Gst.Caps.from_string("video/x-raw, format=(string)RGBA")
        )

        self._appsink = appsink = _make_element_safe("appsink")

        for el in [cam, tee, h264sink, appsink, nvvidconv, nvvidconv_cf]:
            pipeline.add(el)

        sinks = [h264sink, nvvidconv]

        for idx, sink in enumerate(sinks):
            # Use queues for each sink. This ensures the sinks can execute in separate threads
            queue = _make_element_safe("queue")
            pipeline.add(queue)
            # tee.src_%d -> queue
            srcpad_or_none = tee.get_request_pad(f"src_{idx}")
            sinkpad_or_none = queue.get_static_pad("sink")
            srcpad = _sanitize(srcpad_or_none)
            sinkpad = _sanitize(sinkpad_or_none)
            srcpad.link(sinkpad)
            # queue -> sink
            queue.link(sink)
        
        nvvidconv.link(nvvidconv_cf)
        nvvidconv_cf.link(appsink)

        cam.link(tee)

        return pipeline

    def read(self):
        sample = self._appsink.emit("pull-sample")
        buf = sample.get_buffer()
        # (result, mapinfo) = buf.map(Gst.MapFlags.READ)
        # buf2 = buf.extract_dup(0, buf.get_size())
        # arr = np.frombuffer(buf2)

        print(buf.pts, buf.dts, buf.offset)

        caps_format = sample.get_caps().get_structure(0)  # Gst.Structure
        print(caps_format.get_value("format"))

        # GstVideo.VideoFormat

        w, h = caps_format.get_value("width"), caps_format.get_value("height")
        c = 4

        buf_size = buf.get_size()
        print(buf_size)
        arr = np.ndarray(
            shape=(h,w,c), buffer=buf.extract_dup(0, buf_size), dtype=np.uint8
        )

        return arr

    def run(self):
        # start play back and listen to events
        print("Starting pipeline...")

        self._p.set_state(Gst.State.PLAYING)
        try:
            self._mainloop.run()
        except KeyboardInterrupt as e:
            print(e)
        finally:
            self._p.set_state(Gst.State.NULL)

    def stop(self):
        self._p.set_state(Gst.State.NULL)

    def running(self):
        _, state, _ = self._p.get_state(1)
        return True if state == Gst.State.PLAYING else False

    def wait_ready(self):
        while not self.running():
            time.sleep(0.1)
