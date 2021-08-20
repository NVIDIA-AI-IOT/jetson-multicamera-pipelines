import gi

gi.require_version("Gst", "1.0")
from gi.repository import GObject, Gst
from .gstutils import _make_element_safe, _sanitize


def make_nvenc_bin() -> Gst.Bin:
    h264sink = Gst.Bin()

    # Create video converter
    conv = _make_element_safe("nvvideoconvert")

    # H264 encoder
    enc = _make_element_safe("nvv4l2h264enc")
    enc.set_property("bitrate", 10000000)

    # parser, mux
    parser = _make_element_safe("h264parse")
    mux = _make_element_safe("matroskamux")

    # filesink
    filesink = _make_element_safe("filesink")
    filesink.set_property("sync", 0)
    filesink.set_property("location", "test.mkv")

    # Add elements to bin before linking
    for el in [conv, enc, parser, mux, filesink]:
        h264sink.add(el)

    # Link bin elements
    conv.link(enc)
    enc.link(parser)
    parser.link(mux)
    mux.link(filesink)

    enter_pad = _sanitize(conv.get_static_pad("sink"))
    gp = Gst.GhostPad.new(name="sink", target=enter_pad)
    h264sink.add_pad(gp)

    return h264sink


def make_camera_configured(sensor_id) -> Gst.Bin:
    """
    Make pre-configured camera source, so we have consistent setting across sensors
    Switch off defaults which are not helpful for machine vision like edge-enhancement
    """
    cam = _make_element_safe("nvarguscamerasrc")
    cam.set_property("sensor-id", sensor_id)
    cam.set_property("bufapi-version", 1)
    cam.set_property("wbmode", 1)  # 1=auto, 0=off,
    cam.set_property("aeantibanding", 3)  # 3=60Hz, 2=50Hz, 1=auto, 0=off
    cam.set_property("tnr-mode", 0)
    cam.set_property("ee-mode", 0)

    return cam
