# Multi Camera Robot

An easy-to-use library for handling multiple cameras on Nvidia Jetson.

## Installation
```
git clone ssh://git@gitlab-master.nvidia.com:12051/tlewicki/multicamera-robot.git
cd multicamera-robot
bash install.sh
```

## Quickstart

```python
from jetmulticam import MultiCamPipeline, models

pipeline = MultiCamPipeline(
    n_cams=3,  # dynamically create pipeline for n cameras 1..6
    models=[
        models.PeopleNet.DLA0,
        models.DashCamNet.DLA1
        ],
    save_images_path="/home/nx/logs/",
    save_h264_path="/home/nx/logs/",
    publish_rtsp_cam_id=0,
    publish_rtsp_port=5000,
)

img = pipeline.cameras[0].image  # (1080, 1920, 3) buffer mapped to np.array
detections = pipeline.cameras[0].obj_dets # Detection results from the models


# Even though we're running 3 camera streams through 2 models, 
# GPU usage near 0% - we're free to run our DNN application
import torch
from navigation import NavDNN, transform

net = NavDNN()
net = net.to("cuda:0")
net.eval()


# For example, we can run end-to-end DNN navigation loop
while True:
    arr = pipeline.cameras[0].image
    img = Image.fromarray(arr)
    batch_in = transform(img)
    theta = net(batch_in)[0]
    vehicle.set_steering(theta)
```

### Advanced DNN configuration

We can choose  on selected streams

```python
pipeline = MultiCamPipeline(
    n_cams=3,  # dynamically create pipeline for n cameras 1..6
    models={
            models.DashCamNet.GPU: [0,1], # mapping from model -> list of sensor-id
            models.PeopleNet.DLA0: [2],
            models.PeopleNet.DLA1: [3]
            }
)
```

## See also

See also ready pipeline examples in [ready_pipelines/](ready_pipelines/)


## TODOs:

- [x] Add programatic support for multiple sources
- [x] Add programatic support for multiple models
- [ ] Pano stitcher demo
- [ ] Add the diagram of the underlying gstreamer pipeline
- [ ] Inspection robot demo
- [ ] `install.sh` -> `setup.py`
