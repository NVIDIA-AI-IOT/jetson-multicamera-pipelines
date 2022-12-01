# SPDX-License-Identifier: MIT

import logging  # TODO: remove
import os
import time
from threading import Thread

# Gstreamer imports
import gi
import numpy as np

gi.require_version("Gst", "1.0")
from gi.repository import Gst

from .basepipeline import BasePipeline
from ..utils.gst import _make_element_safe, _sanitize
from ..bins.cameras import make_v4l2_image
from ..utils.ImageCV import ImageCV, ImageStitcher


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
    def __init__(self, cameras, logdir="/home/tng042/logs/videos", **kwargs):
        """
        cameras: list of sensor ids for argus cameras
        """
        self._cams = cameras
        self._logdir = logdir
        os.makedirs(self._logdir, exist_ok=True)
        super().__init__(**kwargs)

    def _create_pipeline(self):

        pipeline = _sanitize(Gst.Pipeline())
        self._cameras = cameras = [
            make_v4l2_image(c) for c in self._cams
        ]

        # self._appsinks = appsinks = [make_appsink_configured() for _ in self._cams]

        for el in [*cameras]:
            pipeline.add(el)

        # # Create muxer
        # mux = _make_element_safe("nvstreammux")
        # mux.set_property("live-source", True)
        # mux.set_property("width", 1280)
        # mux.set_property("height", 720)
        # mux.set_property("sync-inputs", 1)
        # mux.set_property("batch-size", 5)
        # mux.set_property("batched-push-timeout", 4000000)

        # pipeline.add(mux)
        
        # for (idx, source) in enumerate(cameras):
        #     srcpad_or_none = source.get_static_pad(f"src")
        #     sinkpad_or_none = mux.get_request_pad(f"sink_{idx}")
        #     srcpad = _sanitize(srcpad_or_none)
        #     sinkpad = _sanitize(sinkpad_or_none)
        #     srcpad.link(sinkpad)
        
        # self._appsinks = appsinks = make_appsink_configured()
        # pipeline.add(appsinks)
        # mux.link(appsinks)

        self._appsinks = appsinks = [make_appsink_configured() for _ in self._cams]
        for el in [*appsinks]:
            pipeline.add(el)
        
        index = 0
        for sink in appsinks:
            queue = _make_element_safe("queue")
            pipeline.add(queue)
            sinkpad_or_none = queue.get_static_pad("sink")
            cameras[index].link(sink)
            index +=1
        return pipeline

    def read(self, cam_idx):
        """
        Returns np.array or None
        """
        sample1 = self._appsinks[0].emit("pull-sample")
        sample2 = self._appsinks[1].emit("pull-sample")
         
        try:
            image1 = ImageCV(sample1)
            image2 = ImageCV(sample2)
            stitcher = ImageStitcher([image1, image2])
            stitcher.showImage()
        except Exception as e:
            print(e)

def getImageBuffer(gstSample):
    if gstSample is None:
        return None
    
    # get buffer from the Gst.sample object
    buf = gstSample.get_buffer()
    buf2 = buf.extract_dup(0, buf.get_size())
    
    # Get W, H, C:
    # caps = sample.get_caps()
    # caps_format = caps.get_structure(0)  # Gst.Structure
    # w, h = caps_format.get_value("width"), caps_format.get_value("height")
    # c = 4  # RGBA format
    # c = 1.5 # NV12 format
    
    # To check format:
    # print(caps_format.get_value("format"))
    # print(caps.to_string())
    # print(caps_format.get_value("format"))
    # print(caps,"buffer size ",buf.get_size())
    return buf2

def showIm(buffer):
    from PIL import Image
    import io
    image = Image.open(io.BytesIO(buffer))
    image.show()
