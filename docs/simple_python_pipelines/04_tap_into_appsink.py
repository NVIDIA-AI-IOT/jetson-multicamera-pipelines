import gi

gi.require_version("Gst", "1.0")
from gi.repository import GObject, Gst
from jetvision.gstutils import _make_element_safe, _sanitize


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


if __name__ == "__main__":
    # Standard GStreamer initialization
    GObject.threads_init()
    Gst.init(None)

    pipeline = _sanitize(Gst.Pipeline())

    cam = _make_element_safe("nvarguscamerasrc")
    cam.set_property("sensor-id", 0)
    cam.set_property("bufapi-version", 1)

    tee = _make_element_safe("tee")

    # cam = _make_element_safe("videotestsrc")
    h264sink = make_nvenc_bin()
    appsink = _make_element_safe("appsink")

    for el in [cam, tee, h264sink, appsink]:
        pipeline.add(el)

    sinks = [h264sink, appsink]
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

    sample = self.appsink.emit("pull-sample")  # blocks until sample avaialable
    buf = sample.get_buffer()
    (result, mapinfo) = buf.map(Gst.MapFlags.READ)

    cam.link(tee)
    loop = GObject.MainLoop()
    pipeline.set_state(Gst.State.PLAYING)

    try:
        loop.run()
    except Exception as e:
        print(e)
    finally:
        pipeline.set_state(Gst.State.NULL)
