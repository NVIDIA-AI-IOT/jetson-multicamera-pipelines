# Multi Camera Robot

An easy-to-use library for handling multiple cameras on Nvidia Jetson.

## Installation
```
git clone 
bash install.sh
```

## Quickstart

```python
from jetmulticam import MultiCamPipelinem, models
import vehicle

pipeline = MultiCamPipeline(
    n_cams=3,  # dynamically create pipeline for n cameras 1..6
    models=[models.PeopleNet.DLA0, models.DashCamNet.DLA1]
    save_images_path="/home/nx/logs/",  # much better than cv2.imsave
    save_h264_path="/home/nx/logs/",
    publish_rtsp=True,
    copy=True,  # returns views (more memory efficient, but readonly) or copies (convenient, ok to r/w).
)

# Ready image mapped to CPU memory
img = pipeline.cameras[0].image  # (1080, 1920, 3) np array already mapped to host

# Detection results from the models
detections = pipeline.cameras[0].obj_dets
pipeline.cameras[0].face_dets
```

## Runing custom application on top of the pipeline
```python
from navigation import NavDNN
net = NavDNN()

while True:
    arr = pipeline.cameras[0].image
    img = Image.fromarray(arr)
    theta = net(img) 
    vehicle.set_seering(theta)
```

## TODOs:

- [x] Add programatic support for multiple sources
- [x] Add programatic support for multiple models
- [ ] Add the diagram of the underlying gstreamer pipeline
- [ ] Pano stitcher demo
- [ ] Inspection robot demo
- [ ] `install.sh` -> `setup.py`
