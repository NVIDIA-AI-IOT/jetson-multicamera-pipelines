import gi
import sys

sys.path.append("/home/nx/nv-multi-camera-robot/")

gi.require_version("Gst", "1.0")
from gi.repository import GObject, Gst
from jetmulticam.gstutils import _make_element_safe, _sanitize


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


def make_v4l2_cam_bin(dev="/dev/video3") -> Gst.Bin:
    bin = Gst.Bin()

    # Create v4l2 camera
    src = _make_element_safe("v4l2src")
    src.set_property("device", dev)

    vidconv = _make_element_safe("videoconvert")
    vidconv_cf = _make_element_safe("capsfilter")
    # Ensure we output something nvvideoconvert has caps for
    vidconv_cf.set_property(
        "caps", Gst.Caps.from_string("video/x-raw, format=(string)RGBA")
    )

    nvvidconv = _make_element_safe("nvvideoconvert")
    nvvidconv_cf = _make_element_safe("capsfilter")
    nvvidconv_cf.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM)"))

    # Add elements to bin before linking
    for el in [src, vidconv, vidconv_cf, nvvidconv, nvvidconv_cf]:
        bin.add(el)

    # Link bin elements
    src.link(vidconv)
    vidconv.link(vidconv_cf)
    vidconv_cf.link(nvvidconv)
    nvvidconv.link(nvvidconv_cf)

    # We exit via nvvidconv source pad
    exit_pad = _sanitize(nvvidconv_cf.get_static_pad("src"))
    gp = Gst.GhostPad.new(name="src", target=exit_pad)
    bin.add_pad(gp)

    return bin


if __name__ == "__main__":
    # Standard GStreamer initialization
    GObject.threads_init()
    Gst.init(None)

    pipeline = _sanitize(Gst.Pipeline())

    cam = make_v4l2_cam_bin()
    # cam = _make_element_safe("videotestsrc")
    h264sink = make_nvenc_bin()

    for el in [cam, h264sink]:
        pipeline.add(el)

    cam.link(h264sink)
    loop = GObject.MainLoop()
    pipeline.set_state(Gst.State.PLAYING)

    try:
        loop.run()
    except Exception as e:
        print(e)
    finally:
        pipeline.set_state(Gst.State.NULL)
