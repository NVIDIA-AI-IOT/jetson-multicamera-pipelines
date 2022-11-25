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
from ..bins.cameras import make_v4l2_cam_bin


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
    appsink.set_property("max-buffers", 2)
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
        cameras = [
            make_v4l2_cam_bin(c) for c in self._cams
        ]

        # self._appsinks = appsinks = [make_appsink_configured() for _ in self._cams]

        for el in [*cameras]:
            pipeline.add(el)


        # Create muxer
        mux = _make_element_safe("nvstreammux")
        mux.set_property("live-source", True)
        mux.set_property("width", 1280)
        mux.set_property("height", 720)
        mux.set_property("sync-inputs", 1)
        mux.set_property("batch-size", 5)
        mux.set_property("batched-push-timeout", 4000000)

        pipeline.add(mux)
        
        for (idx, source) in enumerate(cameras):
            srcpad_or_none = source.get_static_pad(f"src")
            sinkpad_or_none = mux.get_request_pad(f"sink_{idx}")
            srcpad = _sanitize(srcpad_or_none)
            sinkpad = _sanitize(sinkpad_or_none)
            srcpad.link(sinkpad)
        
        self._appsinks = appsinks = make_appsink_configured()
        pipeline.add(appsinks)
        mux.link(appsinks)

        return pipeline

    def read(self, cam_idx):
        """
        Returns np.array or None
        """
        sample = self._appsinks.emit("pull-sample")
        # sample = self._appsinks[cam_idx].emit("pull-sample")
        if sample is None:
            return None
        
        # get buffer from the Gst.sample object
        buf = sample.get_buffer()
        buf2 = buf.extract_dup(0, buf.get_size())
        
        # Get W, H, C:
        caps = sample.get_caps()
        caps_format = caps.get_structure(0)  # Gst.Structure
        w, h = caps_format.get_value("width"), caps_format.get_value("height")
        c = 4  # RGBA format
        c = 1.5 # NV12 format
        
        # To check format: print(caps_format.get_value("format"))
        print(caps.to_string())
        print(caps_format.get_value("format"))
        print(caps,"buffer size ",buf.get_size())
         
        try:
            # arr = np.ndarray(shape=(h, w, c), buffer=buf2, dtype=np.uint8)
            # buf2 is YUV data
            arr=None
            toImage(w,h,buf2)
            #yuv_data = np.frombuffer(buf2, np.uint8).reshape() 
        except Exception as e:
            print(e)
            arr = None
        return arr

def toImage(width, height, buffer):
    from PIL import Image
    import numpy as np
    y_end = width*height

    yuv = np.frombuffer(buffer, dtype='uint8')

    y = yuv[0:y_end].reshape(height,width)
    u = yuv[y_end::2].reshape(height//2, width//2)
    v = yuv[y_end+1::2].reshape(height//2, width//2)

    u = u.repeat(2, axis=0).repeat(2, axis=1)
    v = v.repeat(2, axis=0).repeat(2, axis=1)

    y = y.reshape((y.shape[0], y.shape[1], 1))
    u = u.reshape((u.shape[0], u.shape[1], 1))
    v = v.reshape((v.shape[0], v.shape[1], 1))

    yuv_array = np.concatenate((y, u, v), axis=2)

    # Overflow: yuv_array.dtype = 'uint8', so subtracting 128 overflows.
    #yuv_array[:, :, 0] = yuv_array[:, :, 0].clip(16, 235).astype(yuv_array.dtype) - 16
    #yuv_array[:, :, 1:] = yuv_array[:, :, 1:].clip(16, 240).astype(yuv_array.dtype) - 128

    # Convert from uint8 to float32 before subtraction
    yuv_array = yuv_array.astype(np.float32)
    yuv_array[:, :, 0] = yuv_array[:, :, 0].clip(16, 235) - 16
    yuv_array[:, :, 1:] = yuv_array[:, :, 1:].clip(16, 240) - 128


    convert = np.array([#[1.164,  0.000,  1.793],[1.164, -0.213, -0.533],[1.164,  2.112,  0.000]
                        [1.164,  0.000,  2.018], [1.164, -0.813, -0.391],[1.164,  1.596,  0.000]
                    ])
    rgb = np.matmul(yuv_array, convert.T).clip(0,255).astype('uint8')


    rgb_image = Image.fromarray(rgb)

    rgb_image.save('numpyout.bmp')