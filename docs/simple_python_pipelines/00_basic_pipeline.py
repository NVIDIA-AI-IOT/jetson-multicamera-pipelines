import gi
import sys

gi.require_version("Gst", "1.0")
from gi.repository import GObject, Gst

sys.path.append("../..")
from jetmulticam.gstutils import _make_element_safe, _sanitize

# Standard GStreamer initialization
GObject.threads_init()
Gst.init(None)

pipeline = _sanitize(Gst.Pipeline())
cam = _make_element_safe("nvarguscamerasrc")
display = _make_element_safe("nvoverlaysink")
fakesink = _make_element_safe("fakesink")

sink = display
# sink = fakesink

pipeline.add(cam)
pipeline.add(sink)
cam.link(sink)

# create an event loop and feed gstreamer bus mesages to it
loop = GObject.MainLoop()
pipeline.set_state(Gst.State.PLAYING)

try:
    loop.run()
except:
    pass
finally:
    pipeline.set_state(Gst.State.NULL)
