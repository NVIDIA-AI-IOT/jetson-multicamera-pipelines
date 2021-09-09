# JetVision

https://user-images.githubusercontent.com/26127866/131947398-59a12a95-82f6-4b48-8af7-34a325f0c0f4.mp4

## Quickstart

Install with:
```shell
bash install-dependencies.sh --with-ds
pip3 install jetvision
```


```python
from jetvision import MultiCamPipeline, models
import vehicle

pipeline = MultiCamPipeline(
    cam_ids = [0, 1, 2]  #  dynamically create pipeline for n cameras 1..6
    models=[
        models.PeopleNet.DLA0, # DNNs to perform inference with
        models.DashCamNet.DLA1
        ]
    # Saving h264 stream # TODO: add option for jpg stills?
    save_h264=True,
    save_h264_path="/home/nx/logs/videos",
    # Streaming
    publish_rtsp_cam=True,
    publish_rtsp_port=5000
)
pipeline.start()
pipeline.wait_ready()
```

### Consuming the frames / detection results
```python
# Ready image mapped to CPU memory as
# np.array with shape (1080, 1920, 3)
img = pipeline.cameras[0].image  
# Detection results from the models as python dicts
detections = pipeline.cameras[0].obj_dets
```

## More advanced/specific uses

### Supported models / acceleratorss
```python
pipeline = MultiCamPipeline(
    cam_ids = [0, 1, 2]
    models=[
        models.PeopleNet.DLA0,
        models.PeopleNet.DLA1,
        models.PeopleNet.GPU,
        models.DashCamNet.DLA0,
        models.DashCamNet.DLA1,
        models.DashCamNet.GPU
        ]
    # ...
)
```

### Map specific images to specific models for inference:
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
- [x] Robot demo in Endeavor
- [x] `install.sh` -> `setup.py` for easier pip3 install
- [ ] `MultiCamPipeline` and `CameraPipeline` could have the same base class for code re-use

 gst-launch-1.0 -v udpsrc port=5000 ! \
 "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96" ! \
 rtph264depay ! h264parse ! decodebin ! videoconvert ! autovideosink sync=false
