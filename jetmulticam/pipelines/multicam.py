# SPDX-License-Identifier: MIT

import os
import multiprocessing as mp

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
        self._imageCV = [ImageCV(), ImageCV()]
        self._stitcher = ImageStitcher(self._imageCV)
        self.sharedMem = mp.SimpleQueue()
        self._logdir = logdir
        os.makedirs(self._logdir, exist_ok=True)
        super().__init__(**kwargs)

    def _create_pipeline(self):

        pipeline = _sanitize(Gst.Pipeline())
        self._cameras = cameras = [
            make_v4l2_image(c) for c in self._cams
        ]

        for el in [*cameras]:
            pipeline.add(el)

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
        sample1 = self._appsinks[0].emit("pull-sample")
        sample2 = self._appsinks[1].emit("pull-sample")
         
        try:
            ##########################################################
            ############ single thread try ###########################
            ##########################################################
            # # Update ImageCV objects with new samples
            # self._imageCV[0].updateCVImage(sample1)
            # self._imageCV[1].updateCVImage(sample2)
            # # Display stitched image
            # self._stitcher.showImage()

            #########################################################
            ############## multiprocessing implementation ###########
            #########################################################
            jobs = []
            for objectCV,sample in zip(self._imageCV, [sample1,sample2]):
                p = mp.Process(target=worker, args=(objectCV,sample,self.sharedMem))
                jobs.append(p)
                p.start()

            # get item out of queue first before deadlock happends
            buffer = [self.sharedMem.get(), self.sharedMem.get()]
            for process in jobs:
                process.join()

            self._stitcher.showImage(buffer)
        except Exception as e:
            print(e)

def worker(CVobject, sample, sharedMem):
    sharedMem.put(CVobject.updateCVImage(sample))
