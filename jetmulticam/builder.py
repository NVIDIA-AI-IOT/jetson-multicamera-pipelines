import logging  # TODO: print -> logging
import sys
import os
import time
from threading import Thread

import cv2

# Gstreamer imports
import gi
import numpy as np
import pyds

gi.require_version("Gst", "1.0")
from gi.repository import GObject, Gst

from .gstutils import _err_if_none, _make_element_safe, _sanitize, bus_call
from .elements import make_nvenc_bin, make_argus_camera_configured


class MultiCamPipeline(Thread):
    def __init__(self, sensor_id_list, models, *args, **kwargs):
        """
        models parameter can be:
        - `dict`: mapping of models->sensor-ids to infer on
        - `list`: list of models to use on frames from all cameras
        """

        super().__init__()

        # Gstreamer init
        GObject.threads_init()
        Gst.init(None)

        save_h264_path="/home/nx/logs/videos"
        os.makedirs(save_h264_path, exist_ok=True)

        # create an event loop and feed gstreamer bus mesages to it
        self._mainloop = GObject.MainLoop()

        # gst pipeline object
        if type(models) == list:
            self._p = self._create_pipeline_fully_connected(
                sensor_id_list, models, **kwargs
            )
        elif type(models) == dict:
            self._p = self._create_pipeline_sparsely_connected(sensor_id_list, models)

        self._bus = self._p.get_bus()
        self._bus.add_signal_watch()
        self._bus.connect("message", bus_call, self._mainloop)

        # Runtime parameters
        N_CLASSES = 4
        N_CAMS = max(sensor_id_list) + 1
        self.images = [None for _ in range(0, N_CAMS)]
        self.detections = [[0 for n in range(0, N_CLASSES)] for _ in range(0, N_CAMS)]
        self.frame_n = [0 for _ in range(0, N_CAMS)]

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

    def wait_ready(self):
        while not self.running():
            time.sleep(0.1)

    def _create_pipeline_fully_connected(
        self,
        sensor_id_list,
        model_list,
        save_h264=True,
        save_h264_path="/home/nx/logs/videos",
        display=True,
        streaming=False,
    ):
        """
        Images from all sources will go through all DNNs
        """

        pipeline = Gst.Pipeline()
        _err_if_none(pipeline)

        # Create pre-configured sources
        sources = [make_argus_camera_configured(idx) for idx in sensor_id_list]

        # Create muxer
        mux = _make_element_safe("nvstreammux")
        mux.set_property("live-source", 1)
        mux.set_property("width", 1920)
        mux.set_property("height", 1080)
        mux.set_property("batch-size", len(sensor_id_list))
        mux.set_property("batched-push-timeout", 4000000)

        # Create nvinfers
        nvinfers = [_make_element_safe("nvinfer") for _ in model_list]
        for m_path, nvinf in zip(model_list, nvinfers):
            nvinf.set_property("config-file-path", m_path)
            nvinf.set_property("batch-size", 3)
            # nvinf.set_property("interval", 5) # to infer every n batches

        # nvvideoconvert -> nvdsosd -> nvegltransform -> sink
        nvvidconv = _make_element_safe("nvvideoconvert")
        nvosd = _make_element_safe("nvdsosd")

        tiler = _make_element_safe("nvmultistreamtiler")
        tiler.set_property("rows", 1)
        tiler.set_property("columns", 3)
        # Encoder crashes when we attempt encoding 5760 x 1080, so we set it lower
        # TODO: Is that a bug, or hw limitation?

        # tiler.set_property("width", 2 * 1920)
        # tiler.set_property("height", 720)

        tiler.set_property("width", 1920)
        tiler.set_property("height", 360)

        # Render with EGL GLE sink
        # transform = _make_element_safe("nvegltransform")
        # renderer = _make_element_safe("nveglglessink")

        tee = _make_element_safe("tee")

        sinks = []
        if save_h264:
            ts = time.strftime('%Y-%m-%dT%H-%M-%S%z')
            ecodebin = make_nvenc_bin(filepath=f"/home/nx/logs/videos/jetmulticam{ts}.mkv")
            sinks.append(ecodebin)
        if display:
            overlay = _make_element_safe("nvoverlaysink")
            overlay.set_property("sync", 0)  # crucial for performance of the pipeline
            sinks.append(overlay)
        if streaming:
            raise NotImplementedError

        if len(sinks) == 0:
            # If no other sinks are added we erminate with fakesink
            fakesink = _make_element_safe("fakesink")
            sinks.append(fakesink)

        # Add all elements to the pipeline
        elements = [*sources, mux, *nvinfers, nvvidconv, nvosd, tiler, tee, *sinks]
        for el in elements:
            pipeline.add(el)

        for idx, source in enumerate(sources):
            srcpad_or_none = source.get_static_pad(f"src")
            sinkpad_or_none = mux.get_request_pad(f"sink_{idx}")
            srcpad = _sanitize(srcpad_or_none)
            sinkpad = _sanitize(sinkpad_or_none)
            srcpad.link(sinkpad)

        # Chain multiple nvinfers back-to-back
        mux.link(nvinfers[0])
        for i in range(1, len(nvinfers)):
            nvinfers[i - 1].link(nvinfers[i])
        nvinfers[-1].link(nvvidconv)

        nvvidconv.link(tiler)
        tiler.link(nvosd)
        nvosd.link(tee)

        # Link tees to sinks
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

        # Alternative renderer
        # tiler.link(transform)
        # transform.link(renderer)

        # Register callback on OSD sinkpad.
        # This way we get access to object detection results
        osdsinkpad = nvosd.get_static_pad("sink")

        if osdsinkpad is None:
            raise Error  # TODO: narrow down

        osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, self._osd_callback, 0)

        return pipeline

    def _osd_callback(self, pad, info, u_data):
        start = time.perf_counter()

        self._frame_n = 0
        # Intiallizing object counter with 0.
        self._detections = {
            PGIE_CLASS_ID_VEHICLE: 0,
            PGIE_CLASS_ID_PERSON: 0,
            PGIE_CLASS_ID_BICYCLE: 0,
            PGIE_CLASS_ID_ROADSIGN: 0,
        }

        num_rects = 0

        gst_buffer = info.get_buffer()
        if not gst_buffer:
            # TODO: logging.error
            print("Unable to get GstBuffer ")
            return Gst.PadProbeReturn.DROP

        buff_ptr = hash(gst_buffer)  # Memory address of gst_buffer
        batch_meta = pyds.gst_buffer_get_nvds_batch_meta(buff_ptr)

        # Iterate frames in a batch
        l_frame = batch_meta.frame_meta_list
        while l_frame is not None:
            try:
                frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
                cam_id = frame_meta.source_id  # there's also frame_meta.batch_id
                img = pyds.get_nvds_buf_surface(hash(gst_buffer), cam_id)

                # Store images
                # self.images[cam_id] = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
                self.images[cam_id] = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
                self.frame_n[cam_id] = frame_meta.frame_num

            except StopIteration:
                break

            # Iterate objects in a frame
            l_obj = frame_meta.obj_meta_list
            while l_obj is not None:
                try:
                    obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
                except StopIteration:
                    break

                self.detections[cam_id][obj_meta.class_id] += 1
                obj_meta.rect_params.border_color.set(0.0, 0.0, 1.0, 0.0)

                try:
                    l_obj = l_obj.next
                except StopIteration:
                    break

            # display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
            # display_meta.num_labels = 1
            # py_nvosd_text_params = display_meta.text_params[0]

            # py_nvosd_text_params.display_text = "Frame Number={} Number of Objects={} Vehicle_count={} Person_count={}".format(
            #     self._frame_n,
            #     num_rects,
            #     self._detections[PGIE_CLASS_ID_VEHICLE],
            #     self._detections[PGIE_CLASS_ID_PERSON],
            # )

            # # Now set the offsets where the string should appear
            # py_nvosd_text_params.x_offset = 10
            # py_nvosd_text_params.y_offset = 12

            # # Font , font-color and font-size
            # py_nvosd_text_params.font_params.font_name = "Serif"
            # py_nvosd_text_params.font_params.font_size = 10
            # # set(red, green, blue, alpha); set to White
            # py_nvosd_text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)

            # # Text background color
            # py_nvosd_text_params.set_bg_clr = 1
            # # set(red, green, blue, alpha); set to Black
            # py_nvosd_text_params.text_bg_clr.set(0.0, 0.0, 0.0, 1.0)
            # # Using pyds.get_string() to get display_text as string
            # # print(pyds.get_string(py_nvosd_text_params.display_text))
            # pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
            try:
                l_frame = l_frame.next
            except StopIteration:
                break

        # print(f"Callback took {1000 * (time.perf_counter() - start)} ms")
        return Gst.PadProbeReturn.OK


PGIE_CLASS_ID_VEHICLE = 0
PGIE_CLASS_ID_BICYCLE = 1
PGIE_CLASS_ID_PERSON = 2
PGIE_CLASS_ID_ROADSIGN = 3


if __name__ == "__main__":

    pipeline = MultiCamPipeline(n_cams=3)
    pipeline.start()

    while not pipeline.running():
        time.sleep(1)

    try:
        while True:
            print(pipeline.images[0].shape)
            print(pipeline.detections[0])
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
