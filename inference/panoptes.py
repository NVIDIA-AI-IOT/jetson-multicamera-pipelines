import logging  # TODO: print -> logging
import sys
import time
from threading import Thread

import cv2
# Gstreamer imports
import gi
import numpy as np
import pyds

gi.require_version("Gst", "1.0")
from gi.repository import GObject, Gst

from common.bus_call import bus_call
from common.is_aarch_64 import is_aarch64


def _err_if_none(element):
    if element is None:
        raise ElementNotCreatedError
    else:
        return True


def _make_element_safe(el_type: str) -> Gst.Element:
    """
    Creates a gstremer element using el_type factory.
    Returns Gst.Element or throws an error if we fail.
    This is to avoid `None` elements in our pipeline
    """

    # name=None parameter asks Gstreamer to uniquely name the elements for us
    el = Gst.ElementFactory.make(el_type, name=None)

    if el is not None:
        return el
    else:
        print(f"Pipeline element is None!\n Exiting.")
        # TODO: narrow down the error
        # TODO: use Gst.ElementFactory.find to generate a more informative error message
        raise Error(f"Could not create element {el_type}")


class MultiCamPipeline(Thread):
    def __init__(self, n_cams, *args, **kwargs):

        super().__init__()

        self._gobj_init = GObject.threads_init()
        Gst.init(None)

        # create an event loop and feed gstreamer bus mesages to it
        self._mainloop = GObject.MainLoop()

        # gst pipeline object
        self._ncams = n_cams
        self._p = self._create_pipeline(n_cams)

        self._bus = self._p.get_bus()
        self._bus.add_signal_watch()
        self._bus.connect("message", bus_call, self._mainloop)

        self._pipeline = self._p

        # Runtime parameters
        N_CLASSES = 4
        self.images = [np.zeros((10, 10)) for _ in range(0, n_cams)]
        self.detections = [[0 for n in range(0, N_CLASSES)] for _ in range(0, n_cams)]
        self.frame_n = [0 for _ in range(0, n_cams)]

    def run(self):
        # start play back and listen to events
        print("Starting pipeline...")

        self._p.set_state(Gst.State.PLAYING)
        try:
            self._mainloop.run()
        except Exception as e:
            print(e)
        finally:
            self._p.set_state(Gst.State.NULL)

    def _create_pipeline(self, n_cams):

        pipeline = Gst.Pipeline()
        _err_if_none(pipeline)

        # Create sources
        sources = [_make_element_safe("nvarguscamerasrc") for _ in range(n_cams)]

        # Configure sources
        for idx, source in enumerate(sources):
            source.set_property("sensor-id", idx)
            source.set_property("bufapi-version", 1)

        # Configure streammux
        streammux = _make_element_safe("nvstreammux")
        streammux.set_property("width", 1920)
        streammux.set_property("height", 1080)
        streammux.set_property("batch-size", 3)
        streammux.set_property("batched-push-timeout", 4000000)

        # Configure nvinfer
        pgie = _make_element_safe("nvinfer")
        pgie.set_property("config-file-path", "dstest1_pgie_config.txt")

        # nvvideoconvert -> nvdsosd -> nvegltransform -> sink
        nvvidconv = _make_element_safe("nvvideoconvert")
        nvosd = _make_element_safe("nvdsosd")
        transform = _make_element_safe("nvegltransform")
        sink = _make_element_safe("fakesink")

        # Add everything to the pipeline
        elements = [*sources, streammux, pgie, nvvidconv, nvosd, transform, sink]
        for el in elements:
            pipeline.add(el)

        # Link elements
        for idx, source in enumerate(sources):
            srcpad = source.get_static_pad("src")
            sinkpad = streammux.get_request_pad(f"sink_{idx}")
            srcpad.link(sinkpad)

        streammux.link(pgie)
        pgie.link(nvvidconv)
        nvvidconv.link(nvosd)
        nvosd.link(sink)
        nvosd.link(transform)
        transform.link(sink)

        # Register callback on OSD sinkpad.
        # This way we get access to object detection results
        osdsinkpad = nvosd.get_static_pad("sink")

        if osdsinkpad is None:
            raise Error  # TODO: narrow down

        osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, self._osd_callback, 0)

        return pipeline

    def _osd_callback(self, pad, info, u_data):

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
                self.images[cam_id] = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
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

            display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
            display_meta.num_labels = 1
            py_nvosd_text_params = display_meta.text_params[0]

            py_nvosd_text_params.display_text = "Frame Number={} Number of Objects={} Vehicle_count={} Person_count={}".format(
                self._frame_n,
                num_rects,
                self._detections[PGIE_CLASS_ID_VEHICLE],
                self._detections[PGIE_CLASS_ID_PERSON],
            )

            # Now set the offsets where the string should appear
            py_nvosd_text_params.x_offset = 10
            py_nvosd_text_params.y_offset = 12

            # Font , font-color and font-size
            py_nvosd_text_params.font_params.font_name = "Serif"
            py_nvosd_text_params.font_params.font_size = 10
            # set(red, green, blue, alpha); set to White
            py_nvosd_text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)

            # Text background color
            py_nvosd_text_params.set_bg_clr = 1
            # set(red, green, blue, alpha); set to Black
            py_nvosd_text_params.text_bg_clr.set(0.0, 0.0, 0.0, 1.0)
            # Using pyds.get_string() to get display_text as string
            # print(pyds.get_string(py_nvosd_text_params.display_text))
            pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
            try:
                l_frame = l_frame.next
            except StopIteration:
                break

        return Gst.PadProbeReturn.OK


PGIE_CLASS_ID_VEHICLE = 0
PGIE_CLASS_ID_BICYCLE = 1
PGIE_CLASS_ID_PERSON = 2
PGIE_CLASS_ID_ROADSIGN = 3


class GListIterator:
    """
    Implements python iterator protocol for pyds.GList type
    This is not perfect, but concise than the altenative of manually iterating the list using l_obj.next
    https://github.com/NVIDIA-AI-IOT/deepstream_python_apps/blob/6aabcaf85a9e8f11e9a4c39ab1cd46554de7c578/apps/deepstream-imagedata-multistream/deepstream_imagedata-multistream.py#L112
    """

    def __init__(self, pyds_glist):
        self._head = pyds_glist
        self._curr = pyds_glist

    def __iter__(self):
        self._curr = self._head
        return self

    def __next__(self):
        # Advance the _curr node of linked list
        self._curr = self._curr.next

        if self._curr is None:
            # TODO: can we take care of the type cast here?
            raise StopIteration("Glist object reached termination node")
        else:
            return self._curr


if __name__ == "__main__":

    pipeline = MultiCamPipeline(n_cams=3)
    pipeline.start()

    try:
        while True:
            print(pipeline.images[0])
            print(pipeline.detections[0])
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
