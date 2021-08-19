import sys

import gi
gi.require_version("Gst", "1.0")
from gi.repository import GObject, Gst

def _err_if_none(element):
    if element is None:
        raise Exception("Element is none!")
    else:
        return True


def _sanitize(element) -> Gst.Element:
    """
    Passthrough function which sure element is not `None`
    Returns `Gst.Element` or raises Error
    """
    if element is None:
        raise Exception("Element is none!")
    else:
        return element


def _make_element_safe(el_type: str, el_name=None) -> Gst.Element:
    """
    Creates a gstremer element using el_type factory.
    Returns Gst.Element or throws an error if we fail.
    This is to avoid `None` elements in our pipeline
    """

    # name=None parameter asks Gstreamer to uniquely name the elements for us
    el = Gst.ElementFactory.make(el_type, name=el_name)

    if el is not None:
        return el
    else:
        print(f"Pipeline element is None!")
        # TODO: narrow down the error
        # TODO: use Gst.ElementFactory.find to generate a more informative error message
        raise NameError(f"Could not create element {el_type}")

def bus_call(bus, message, loop):
    # Taken from:
    # https://github.com/NVIDIA-AI-IOT/deepstream_python_apps/blob/6aabcaf85a9e8f11e9a4c39ab1cd46554de7c578/apps/common/bus_call.py
    
    t = message.type
    if t == Gst.MessageType.EOS:
        sys.stdout.write("End-of-stream\n")
        loop.quit()
    elif t==Gst.MessageType.WARNING:
        err, debug = message.parse_warning()
        sys.stderr.write("Warning: %s: %s\n" % (err, debug))
    elif t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        sys.stderr.write("Error: %s: %s\n" % (err, debug))
        loop.quit()
    return True

    
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