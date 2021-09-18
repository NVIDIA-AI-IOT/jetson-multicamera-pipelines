import logging  # TODO: print -> logging
import os
import time
from threading import Thread

# Gstreamer imports
import gi
import numpy as np

gi.require_version("Gst", "1.0")
from gi.repository import GObject, Gst

from ..gstutils import _err_if_none, _make_element_safe, _sanitize, bus_call
from .bins import (
    make_nvenc_bin,
    make_argus_camera_configured,
    make_v4l2_cam_bin,
    make_argus_cam_bin,
    make_nvenc_bin_no_ds
)

from .basepipeline import BasePipeline


def on_buffer():
    print("test")

    return Gst.FlowReturn.OK


class CameraPipeline(BasePipeline):

    def __init__(self, camera, **kwargs):
        """
        models parameter can be:
        - `dict`: mapping of models->sensor-ids to infer on
        - `list`: list of models to use on frames from all cameras
        """

        save_h264_path = "/home/nx/logs/videos"
        os.makedirs(save_h264_path, exist_ok=True)
        
        self._camera = camera
        
        super().__init__(**kwargs)

    def _create_pipeline(self):

        pipeline = _sanitize(Gst.Pipeline())
        cam = make_argus_camera_configured(self._camera, bufapi_version=0)
        tee = _make_element_safe("tee")
        h264sink = make_nvenc_bin_no_ds(f"/home/nx/logs/videos/jetvision-singlecam.mkv")

        # Converter
        nvvidconv = _make_element_safe("nvvidconv")
        nvvidconv_cf = _make_element_safe("capsfilter")
        nvvidconv_cf.set_property(
            "caps", Gst.Caps.from_string("video/x-raw, format=(string)RGBA") # NOTE: make parametric? i.e. height=1080, width=1920
        )

        # Appsink
        self._appsink = appsink = _make_element_safe("appsink")
        appsink.set_property("max-buffers", 1)
        appsink.set_property("drop", True)
        appsink.connect("new-sample", on_buffer, None)

        sinks = [h264sink, appsink]

        for el in [cam, nvvidconv, nvvidconv_cf, tee, *sinks]:
            pipeline.add(el)

        cam.link(nvvidconv)
        nvvidconv.link(nvvidconv_cf)
        nvvidconv_cf.link(tee)

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

        return pipeline

    def read(self):
        sample = self._appsink.emit("pull-sample")
        buf = sample.get_buffer()
        # (result, mapinfo) = buf.map(Gst.MapFlags.READ)
        buf2 = buf.extract_dup(0, buf.get_size())
        # arr = np.frombuffer(buf2)

        print(buf.pts, buf.dts, buf.offset)

        caps_format = sample.get_caps().get_structure(0)  # Gst.Structure
        print(caps_format.get_value("format"))

        # GstVideo.VideoFormat

        w, h = caps_format.get_value("width"), caps_format.get_value("height")
        c = 4

        buf_size = buf.get_size()

        arr = np.ndarray(shape=(h, w, c), buffer=buf2, dtype=np.uint8)

        return arr
