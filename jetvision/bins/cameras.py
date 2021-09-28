def make_argus_camera_configured(sensor_id, bufapi_version=1) -> Gst.Element:
    """
    Make pre-configured camera source, so we have consistent setting across sensors
    Switch off defaults which are not helpful for machine vision like edge-enhancement
    """
    cam = _make_element_safe("nvarguscamerasrc")
    cam.set_property("sensor-id", sensor_id)
    cam.set_property("bufapi-version", bufapi_version)
    cam.set_property("wbmode", 1)  # 1=auto, 0=off,
    cam.set_property("aeantibanding", 3)  # 3=60Hz, 2=50Hz, 1=auto, 0=off
    cam.set_property("tnr-mode", 0)
    cam.set_property("ee-mode", 0)

    return cam


def make_argus_cam_bin(sensor_id) -> Gst.Bin:
    bin = Gst.Bin()

    # Create v4l2 camera
    src = make_argus_camera_configured(sensor_id)
    conv = _make_element_safe("nvvideoconvert")
    conv_cf = _make_element_safe("capsfilter")
    conv_cf.set_property(
        "caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=(string)RGBA")
    )

    # Add elements to bin before linking
    for el in [src, conv, conv_cf]:
        bin.add(el)

    # Link bin elements
    src.link(conv)
    conv.link(conv_cf)

    # We exit via nvvidconv source pad
    exit_pad = _sanitize(conv_cf.get_static_pad("src"))
    gp = _sanitize(Gst.GhostPad.new(name="src", target=exit_pad))
    bin.add_pad(gp)

    return bin


def make_v4l2_cam_bin(dev: str) -> Gst.Bin:
    # dev: v4l2 node e.g. "/dev/video3"
    bin = Gst.Bin()

    # Create v4l2 camera
    src = _make_element_safe("v4l2src")
    src.set_property("device", dev)
    src.set_property("framerate", 30)

    vidconv = _make_element_safe("videoconvert")
    vidconv_cf = _make_element_safe("capsfilter")
    # Ensure we output something nvvideoconvert has caps for
    vidconv_cf.set_property(
        "caps",
        Gst.Caps.from_string(
            "video/x-raw, format=(string)RGBA, framerate=(fraction)30/1"
        ),
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
