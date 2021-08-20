import gi

gi.require_version("Gst", "1.0")
from gi.repository import GObject, Gst

from gstutils import _make_element_safe, _sanitize

# Standard GStreamer initialization
GObject.threads_init()
Gst.init(None)

pipeline = _sanitize(Gst.Pipeline())

cam = _make_element_safe("nvarguscamerasrc")
cam.set_property("sensor-id", 0)
cam.set_property("bufapi-version", 1)
cam = _make_element_safe("videotestsrc")

conv = _make_element_safe("nvvideoconvert")

enc = _make_element_safe("nvv4l2h264enc")
enc.set_property("bitrate", 10000000)

parser = _make_element_safe("h264parse")
mux = _make_element_safe("matroskamux")

filesink = _make_element_safe("filesink")
filesink.set_property("sync", 1)
filesink.set_property("location", "test.mkv")


elements = [cam, conv, enc, parser, mux, filesink]

for el in elements:
    pipeline.add(el)

cam.link(conv)
conv.link(enc)
enc.link(parser)
parser.link(mux)
mux.link(filesink)

# create an event loop and feed gstreamer bus mesages to it
loop = GObject.MainLoop()
pipeline.set_state(Gst.State.PLAYING)

try:
    loop.run()
except Exception as e:
    print(e)
finally:
    pipeline.set_state(Gst.State.NULL)
