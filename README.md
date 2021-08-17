# Multi Camera Robot

An easy-to-use library for handling multiple cameras on Nvidia Jetson.

## Installation and quickstart

Install
```bash
git clone ssh://git@gitlab-master.nvidia.com:12051/tlewicki/multicamera-robot.git
cd multicamera-robot
bash install.sh
source exports.sh
```

Run demo
```
python3 run.py
```

## Quickstart

### Instantiating the pipeline
```python
from jetmulticam import MultiCamPipeline, models
import vehicle

pipeline = MultiCamPipeline(
    # dynamically create pipeline for n cameras 1..6
    n_cams=3, 
    models=[models.PeopleNet.DLA0, models.DashCamNet.DLA1]
    # Saving stills
    save_jpgs=True,
    save_jpgs_path="/home/nx/logs/images/", 
    # Saving h264 stream
    save_h264=True,
    save_h264_path="/home/nx/logs/videos",
    # Streaming
    publish_rtsp_cam=0,
    publish_rtsp_port=5000
)
pipeline.start()
pipeline.wait_ready()
```

### Getting the images and detection results
```python
# Ready image mapped to CPU memory
img = pipeline.cameras[0].image  # np.array with shape (1080, 1920, 3)
# Detection results from the models
detections = pipeline.cameras[0].obj_dets
pipeline.cameras[0].face_dets
```

## More advanced/specific uses

### Specify cameras by their sensors id
```python
pipeline = MultiCamPipeline(
    # n_cams=3, 
    cam_ids = [4, 5, 6] # Cameras 0-3 are stereo pairs and are used for something else
    models=[models.PeopleNet.DLA0, models.DashCamNet.DLA1]
    # ...
)
```

### Specify which models should run inference on which cameras:
```python
pipeline = MultiCamPipeline(
    cam_ids = list(range(6)),
    models={
        models.PeopleNet.DLA0: [0, 1, 2],
        models.PeopleNet.DLA1: [3, 4, 5],
        models.DashCamNet.GPU: [0, 1, 2, 3, 4, 5],
        }
    # ...
)
```

## Examples showing custom application on top of jetmulticam

How to build your own application using `jetmulticam`

- [examples/00-example-hello-multicam-panorama.ipynb](examples/00-example-hello-multicam-panorama.ipynb)
- [examples/01-example-pytorch-integration-todo.ipynb](examples/01-example-pytorch-integration-todo.ipynb)
- [examples/02-example-pytorch-navigation-todo.ipynb](examples/02-example-pytorch-navigation-todo.ipynb)
- [examples/03-example-inspection-robot-idea.py](examples/03-example-inspection-robot-idea.py)
- [examples/04-example-retail-robot-idea.py](examples/04-example-retail-robot-idea.py)

## More

Ready pipelines for specific multicamera usecase deployable via `gst-launch-1.0` are available at: [ready_pipelines](ready_pipelines)

## TODOs:

- [x] Add programatic support for multiple sources
- [x] Add programatic support for multiple models
- [ ] Add the diagram of the underlying gstreamer pipeline
- [x] Pano stitcher demo
- [ ] Robot demo in Endeavor
- [ ] `install.sh` -> `setup.py` for easier pip3 install
