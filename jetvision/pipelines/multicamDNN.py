import logging
import time

# Gstreamer imports
import gi
import numpy as np
import pyds

gi.require_version("Gst", "1.0")
from gi.repository import Gst

from ..gstutils import _err_if_none, _make_element_safe, _sanitize, bus_call
from .bins import (
    make_nvenc_bin,
    make_argus_cam_bin,
    make_v4l2_cam_bin,
)

from .basepipeline import BasePipeline


class CameraPipelineDNN(BasePipeline):
    def __init__(self, cameras, models, *args, **kwargs):
        """
        models parameter can be:
        - `dict`: mapping of models->sensor-ids to infer on
        - `list`: list of models to use on frames from all cameras
        """

        self._m = models
        self._c = cameras

        # Runtime parameters
        N_CAMS = len(cameras) + 1
        self.images = [np.empty((1080, 1920, 3)) for _ in range(0, N_CAMS)]
        self.detections = [[] for _ in range(0, N_CAMS)]  # dets for each camera
        self.frame_n = [-1 for _ in range(0, N_CAMS)]

        super().__init__(**kwargs)

    def _create_pipeline(self, **kwargs) -> Gst.Pipeline:
        # gst pipeline object
        if type(self._m) is list:
            p = self._create_pipeline_fully_connected(self._c, self._m, **kwargs)
        elif type(self._m) is dict:
            p = self._create_pipeline_sparsely_connected(self._c, self._m, **kwargs)

        return p

    def _create_pipeline_fully_connected(
        self,
        cameras,
        model_list,
        save_video=True,
        save_video_folder="/home/nx/logs/videos",
        display=True,
        streaming=False,
    ):
        """
        Images from all sources will go through all DNNs
        """

        pipeline = Gst.Pipeline()
        _err_if_none(pipeline)

        n_cams = len(cameras)
        sources = self._make_sources(cameras)

        # Create muxer
        mux = _make_element_safe("nvstreammux")
        mux.set_property("live-source", True)
        mux.set_property("width", 1920)
        mux.set_property("height", 1080)
        mux.set_property("batch-size", n_cams)
        mux.set_property("batched-push-timeout", 4000000)

        # Create nvinfers
        nvinfers = [_make_element_safe("nvinfer") for _ in model_list]
        for m_path, nvinf in zip(model_list, nvinfers):
            nvinf.set_property("config-file-path", m_path)
            nvinf.set_property("batch-size", n_cams)
            # TODO: expose this
            # nvinf.set_property("interval", 5) # to infer every n batches

        # nvvideoconvert -> nvdsosd -> nvegltransform -> sink
        nvvidconv = _make_element_safe("nvvideoconvert")
        nvosd = _make_element_safe("nvdsosd")

        tiler = _make_element_safe("nvmultistreamtiler")

        n_cols = min(n_cams, 3)  # max 3 cameras in a row. More looks overcrowded.
        tiler.set_property("rows", n_cams // n_cols)
        tiler.set_property("columns", n_cols)
        # Encoder crashes when we attempt encoding 5760 x 1080, so we set it lower
        # TODO: Is that a bug, or hw limitation?

        tiler.set_property("width", 1920)
        tiler.set_property("height", 360)

        # Render with EGL GLE sink
        # transform = _make_element_safe("nvegltransform")
        # renderer = _make_element_safe("nveglglessink")

        tee = _make_element_safe("tee")

        sinks = []
        if save_video:
            ts = time.strftime("%Y-%m-%dT%H-%M-%S%z")
            encodebin = make_nvenc_bin(filepath=save_video_folder + f"/jetvision{ts}.mkv")
            sinks.append(encodebin)
        if display:
            overlay = _make_element_safe("nvoverlaysink")
            overlay.set_property("sync", 0)  # crucial for performance of the pipeline
            sinks.append(overlay)
        if streaming:
            # TODO:
            raise NotImplementedError

        if len(sinks) == 0:
            # If no other sinks are added we terminate with fakesink
            fakesink = _make_element_safe("fakesink")
            sinks.append(fakesink)

        # Add all elements to the pipeline
        elements = [*sources, mux, *nvinfers, nvvidconv, tiler, nvosd, tee, *sinks]
        for el in elements:
            pipeline.add(el)

        for (idx, source) in enumerate(sources):
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
        osdsinkpad = _sanitize(nvosd.get_static_pad("sink"))
        osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, self._parse_dets_callback, 0)

        for idx, source in enumerate(sources):
            sourcepad = _sanitize(source.get_static_pad("src"))
            cb_args = {"image_idx": idx}
            sourcepad.add_probe(
                Gst.PadProbeType.BUFFER, self._get_np_img_callback, cb_args
            )

        return pipeline

    @staticmethod
    def _make_sources(cameras: list) -> list:
        # Create pre-configured sources with appropriate type: argus or v4l
        sources = []
        for c in cameras:
            # int -> bin with arguscamerasrc (e.g. 0)
            # str -> bin with nv4l2src (e.g. '/dev/video0)
            if type(c) is int:
                source = make_argus_cam_bin(c)
            elif type(c) is str:
                source = make_v4l2_cam_bin(c)
            else:
                raise TypeError(
                    f"Error parsing 'cameras' argument. Valid cameras must be either:\n\
                    1) 'str' type for v4l2 (e.g. '/dev/video0')\n\
                    2) 'int' type for argus (0)\n\
                    Got '{type(c)}'"
                )

            sources.append(source)

        return sources

    def _get_np_img_callback(self, pad, info, u_data):
        """
        Callback responsible for extracting the numpy array from image
        """
        cb_start = time.perf_counter()

        gst_buffer = info.get_buffer()
        if not gst_buffer:
            logging.warn(
                "_np._img_callback was unable to get GstBuffer. Dropping frame."
            )
            return Gst.PadProbeReturn.DROP

        buff_ptr = hash(gst_buffer)  # Memory address of gst_buffer
        idx = u_data["image_idx"]
        img = pyds.get_nvds_buf_surface(buff_ptr, 0)
        self.images[idx] = img[:, :, :3]  # RGBA->RGB
        self.frame_n[idx] += 1

        self._log.info(
            f"Image ingest callback for image {idx} took {1000 * (time.perf_counter() - cb_start):0.2f} ms"
        )
        return Gst.PadProbeReturn.OK

    def _parse_dets_callback(self, pad, info, u_data):
        cb_start = time.perf_counter()

        gst_buffer = info.get_buffer()
        if not gst_buffer:
            logging.error("Detection callback unable to get GstBuffer ")
            return Gst.PadProbeReturn.DROP

        buff_ptr = hash(gst_buffer)  # Memory address of gst_buffer
        batch_meta = pyds.gst_buffer_get_nvds_batch_meta(buff_ptr)

        # Iterate frames in a batch
        # TODO: for loop
        l_frame = batch_meta.frame_meta_list
        while l_frame is not None:

            detections = []
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
            cam_id = frame_meta.source_id  # there's also frame_meta.batch_id

            # Iterate objects in a frame
            l_obj = frame_meta.obj_meta_list
            while l_obj is not None:
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)

                # This is all in image frame, e.g.: 1092.7200927734375 93.68058776855469 248.01895141601562 106.38716125488281
                l, w = obj_meta.rect_params.left, obj_meta.rect_params.width
                t, h = obj_meta.rect_params.top, obj_meta.rect_params.height

                position = (l, w, t, h)
                cls_id = obj_meta.class_id
                conf = obj_meta.confidence
                label = obj_meta.obj_label

                detections.append({
                    "class": label,
                    "position": position,
                    "confidence": conf})

                obj_meta.rect_params.border_color.set(0.0, 1.0, 0.0, 0.0)

                l_obj = l_obj.next

            self.detections[cam_id] = detections
            self.det_n[cam_id] += 1

            l_frame = l_frame.next

        self._log.info(
            f"Detection parsing callback took {1000 * (time.perf_counter() - cb_start):0.2f} ms"
        )
        return Gst.PadProbeReturn.OK

    def elapsed_time(self):
        delta = time.perf_counter() - self._start_ts
        return delta

    def fps(self):
        t = self.elapsed_time()
        fps_list = [cnt/t for cnt in self.frame_n]
        return fps_list
