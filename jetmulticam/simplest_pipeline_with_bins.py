import gi

gi.require_version("Gst", "1.0")
from gi.repository import GObject, Gst

from gstutils import _make_element_safe, _sanitize

# Standard GStreamer initialization
GObject.threads_init()
Gst.init(None)

pipeline = _sanitize(Gst.Pipeline())

# cam = _make_element_safe("nvarguscamerasrc")
# cam.set_property('sensor-id', 0)
# cam.set_property('bufapi-version', 1)

cam = _make_element_safe("videotestsrc")

conv = _make_element_safe("nvvideoconvert")

enc = _make_element_safe("nvv4l2h264enc")
enc.set_property("bitrate", 10000000)

parser = _make_element_safe("h264parse")
qtmux = _make_element_safe("qtmux")

filesink = _make_element_safe("filesink")
filesink.set_property("sync", 1)
filesink.set_property("location", "test.mp4")

h264sink = Gst.Bin()

h264sink.add(conv)
h264sink.add(enc)
h264sink.add(parser)
h264sink.add(qtmux)
h264sink.add(filesink)


enter_pad = _sanitize(conv.get_static_pad("sink"))
gp = Gst.GhostPad.new(name="sink", target=enter_pad)
h264sink.add_pad(gp)


elements = [cam, h264sink]

for el in elements:
    pipeline.add(el)

cam.link(h264sink)

# Inside bin
conv.link(enc)
enc.link(parser)
parser.link(qtmux)
qtmux.link(filesink)

# create an event loop and feed gstreamer bus mesages to it
loop = GObject.MainLoop()
pipeline.set_state(Gst.State.PLAYING)

try:
    loop.run()
except Exception as e:
    print(e)
finally:
    pipeline.set_state(Gst.State.NULL)
