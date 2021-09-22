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
    make_nvenc_bin_no_ds,
)

from .basepipeline import BasePipeline


def make_conv_bin(caps="video/x-raw, format=(string)RGBA") -> Gst.Bin:
    bin = Gst.Bin()

    nvvidconv = _make_element_safe("nvvidconv")
    conv_cf = _make_element_safe("capsfilter")
    conv_cf.set_property(
        "caps",
        Gst.Caps.from_string(
            caps
        ),  # NOTE: make parametric? i.e. height=1080, width=1920
    )

    nvvidconv.link(conv_cf)

    # We enter via conv sink pad
    enter_pad = _sanitize(nvvidconv.get_static_pad("sink"))
    gp_enter = _sanitize(Gst.GhostPad.new(name="sink", target=enter_pad))
    bin.add_pad(gp_enter)

    # We exit via conv_cf source pad
    exit_pad = _sanitize(conv_cf.get_static_pad("src"))
    gp = _sanitize(Gst.GhostPad.new(name="src", target=exit_pad))
    bin.add_pad(gp)

    return bin


def make_appsink_configured() -> Gst.Element:
    appsink = _make_element_safe("appsink")
    appsink.set_property("max-buffers", 1)
    appsink.set_property("drop", True)
    return appsink


class CameraPipeline(BasePipeline):
    def __init__(self, cameras, **kwargs):
        """
        models parameter can be:
        - `dict`: mapping of models->sensor-ids to infer on
        - `list`: list of models to use on frames from all cameras
        """

        save_h264_path = "/home/nx/logs/videos"
        os.makedirs(save_h264_path, exist_ok=True)

        self._cams = cameras

        super().__init__(**kwargs)

    def _create_pipeline(self):

        pipeline = _sanitize(Gst.Pipeline())

        cameras = [
            make_argus_camera_configured(c, bufapi_version=0) for c in self._cams
        ]
        # convs = [make_conv_bin() for _ in self._cams]
        convs = [_make_element_safe("nvvidconv") for _ in self._cams]

        conv_cfs = [_make_element_safe("capsfilter") for _ in self._cams]

        for cf in conv_cfs:
            cf.set_property(
                "caps",
                Gst.Caps.from_string(
                    "video/x-raw, format=(string)RGBA"
                ),  # NOTE: make parametric? i.e. height=1080, width=1920
            )

        tees = [_make_element_safe("tee") for _ in self._cams]
        h264sinks = [
            make_nvenc_bin_no_ds(f"/home/nx/logs/videos/jetvision-singlecam-{c}.mkv")
            for c in self._cams
        ]
        self._appsinks = appsinks = [make_appsink_configured() for _ in self._cams]

        for el in [*cameras, *convs, *conv_cfs, *tees, *h264sinks, *appsinks]:
            pipeline.add(el)

        for cam, conv in zip(cameras, convs):
            print(cam, conv)
            cam.link(conv)

        for conv, cf in zip(convs, conv_cfs):
            conv.link(cf)

        for cf, tee in zip(conv_cfs, tees):
            cf.link(tee)

        for (tee, enc, app) in zip(tees, h264sinks, appsinks):

            for idx, sink in enumerate([enc, app]):
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

        return pipeline

    def read(self, cam_idx):
        """
        Returns np.array or None
        """
        sample = self._appsinks[cam_idx].emit("pull-sample")
        if sample is None:
            return None
        buf = sample.get_buffer()
        buf2 = buf.extract_dup(0, buf.get_size())
        # Get W, H, C:
        caps_format = sample.get_caps().get_structure(0)  # Gst.Structure
        w, h = caps_format.get_value("width"), caps_format.get_value("height")
        c = 4  # Earlier we converted to RGBA
        # To check format: print(caps_format.get_value("format"))
        arr = np.ndarray(shape=(h, w, c), buffer=buf2, dtype=np.uint8)

        return arr
