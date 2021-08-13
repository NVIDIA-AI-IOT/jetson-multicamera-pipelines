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
        raise Error(f"Could not create element {el_type}")