# Multi Camera Robot

An easy-to-use library for handling multiple cameras on Nvidia Jetson.

## Installation
```
git clone 
bash install.sh
```

## Quickstart

```python
from jetmulticam import MultiCamPipeline
import vehicle

pipeline = MultiCamPipeline(
    n_cams=3,  # dynamically create pipeline for n cameras 1..6
    detect_objects=True,  # choose the components we need a la carte / one-by-one
    detect_faces=True,
    save_images=True,  # much better than cv2.imsave
    save_h264=True,
    publish_rtsp=True,
    copy=True,  # returns views (more memory efficient, but readonly) or copies (convenient, ok to r/w).
)

pipeline.cameras[0].image  # (1080, 1920, 3) np array already mapped to host
pipeline.cameras[0].obj_dets
pipeline.cameras[0].face_dets
```

## TODOs:

- [x] Add programatic support for multiple sources
- [x] Add programatic support for multiple models
- [ ] Add the diagram of the underlying gstreamer pipeline
- [ ] Pano stitcher demo
- [ ] Inspection robot demo
- [ ] `install.sh` -> `setup.py`
