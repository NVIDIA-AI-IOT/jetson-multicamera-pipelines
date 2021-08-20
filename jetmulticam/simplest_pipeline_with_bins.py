import gi

gi.require_version("Gst", "1.0")
from gi.repository import GObject, Gst
from gstutils import _make_element_safe, _sanitize


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
    filesink.set_property("sync", 1)
    filesink.set_property("location", "test.mp4")

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


if __name__ == "__main__":
    # Standard GStreamer initialization
    GObject.threads_init()
    Gst.init(None)

    pipeline = _sanitize(Gst.Pipeline())

    cam = _make_element_safe("nvarguscamerasrc")
    cam.set_property("sensor-id", 0)
    cam.set_property("bufapi-version", 1)

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
