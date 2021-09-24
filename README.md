# JetVision

Realtime CV/AI pipelines on Nvidia Jetson Platform.

https://user-images.githubusercontent.com/26127866/134721058-8378697f-bbf0-4505-be75-f3dba3080c71.mp4


## Quickstart

Install:
```shell
git clone https://github.com/tomek-l/nv-jetvision.git
cd nv-jetvision
bash install-dependencies.sh
pip3 install .
```
Run:
```shell
source exports.sh
python3 example.py
```

## Usage example

```python
import time
from jetvision import CameraPipelineDNN
from jetvision.models import PeopleNet, DashCamNet

if __name__ == "__main__":

    pipeline = CameraPipelineDNN(
        cameras=[2, 5, 8],
        models=[
            PeopleNet.DLA1,
            DashCamNet.DLA0,
            # PeopleNet.GPU
        ],
        save_video=True,
        save_video_folder="/home/nx/logs/videos",
        display=True,
    )

    while pipeline.running():
        arr = pipeline.images[0] # (1080, 1920, 3) np.array (RGB 1080p image)
        dets = pipeline.detections[0] # Detections from the DNNs
        time.sleep(1/30)
```

## Benchmarks

| #   | Scenario                               | # cams | JetVision<br>CPU core util. | argus-deamon<br>CPU core util. | CPU<br>total | GPU % | EMC util % | Power draw | Inference Hardware                                             |
| --- | -------------------------------------- | ------ | --------------------------- | ------------------------------ | ------------ | ----- | ---------- | ---------- | -------------------------------------------------------------- |
| 1.  | 1xGMSL -> 2xDNNs + disp + encode       | 1      | 32%                         | 24%                            | 56%          | <3%   | 57%        | 8.5W       | DLA0: PeopleNet DLA1: DashCamNet                               |
| 2.  | 2xGMSL -> 2xDNNs + disp + encode       | 2      | 43%                         | 46%                            | 89%          | <3%   | 62%        | 9.4W       | DLA0: PeopleNet DLA1: DashCamNet                               |
| 3.  | 3xGMSL -> 2xDNNs + disp + encode       | 3      | 55%                         | 70%                            | 125%         | <3%   | 68%        | 10.1W      | DLA0: PeopleNet DLA1: DashCamNet                               |
| 4.  | Same as _#3_ with CPU @ 1.9GHz         | 3      | 45%                         | 54%                            | 99%          | <3%   | 68%        | 10.4w      | DLA0: PeopleNet DLA1: DashCamNet                               |
| 5.  | 3xGMSL+2xV4L -> 2xDNNs + disp + encode | 5      | 57%                         | 70%                            | 127%         | <3%   | 45%        | 9.1W       | DLA0: PeopleNet _(interval=1)_ DLA1: DashCamNet _(interval=1)_ |
| 6.  | 3xGMSL+2xV4L -> 2xDNNs + disp + encode | 5      | 50%                         | 70%                            | 120%         | <3%   | 25%        | 7.5W       | DLA0: PeopleNet _(interval=6)_ DLA1: DashCamNet _(interval=6)_ |
| 7.  | 3xGMSL -> DNN + disp + encode       | 5      | 62%                         | 77%                            | 139%         | 99%   | 25%        | 15W        | GPU: PeopleNet                                                 |


Notes:
- All CPU numers are per-CPU core. For example, the `45%` for JetVision process in Scenario 4. means we use `45%/6=7.5%` of the entire CPU.
- The residual GPU usage in DLA-accelerated nets is caused by Sigmoid activations being computed with CUDA backend. Remaining layers are computed on DLA.
- CPU usage will vary depending on factors such as camera resolution, framerate, available video formats and driver implementation.
- When reproducing results do: `sudo nvpmodel -m 2; sudo jetson_clocks;`
- Test platform: [Jetson Xavier NX](https://developer.nvidia.com/embedded/jetson-xavier-nx-devkit) and [XNX Box](https://www.leopardimaging.com/product/nvidia-jetson-cameras/nvidia-nx-mipi-camera-kits/li-xnx-box-gmsl2/) running [JetPack](https://developer.nvidia.com/embedded/jetpack) v4.5.1


## More 

### Supported models / acceleratorss
```python
pipeline = CameraPipelineDNN(
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

<!-- ### You can specific images to specific models for inference:
```python
pipeline = CameraPipelineDNN(
    cam_ids = list(range(6)),
    models={
        models.PeopleNet.DLA0: [0, 1],
        models.PeopleNet.DLA1: [2, 3],
        models.DashCamNet.GPU: [0, 1, 2, 3, 4, 5],
        }
    # ...
)
``` -->

<!-- ### Examples showing custom application on top of jetmulticam

How to build your own application using `jetmulticam`

- [examples/00-example-hello-multicam-panorama.ipynb](examples/00-example-hello-multicam-panorama.ipynb)
- [examples/01-example-pytorch-integration-todo.ipynb](examples/01-example-pytorch-integration-todo.ipynb)
- [examples/02-example-pytorch-navigation-todo.ipynb](examples/02-example-pytorch-navigation-todo.ipynb)
- [examples/03-example-inspection-robot-idea.py](examples/03-example-inspection-robot-idea.py)
- [examples/04-example-retail-robot-idea.py](examples/04-example-retail-robot-idea.py) -->

## More

Ready pipelines for specific multicamera usecase deployable via `gst-launch-1.0` are available at: [ready_pipelines](ready_pipelines)

## TODOs:

- [x] Add programatic support for multiple sources
- [x] Add programatic support for multiple models
- [x] Pano stitcher demo
- [x] Robot demo in Endeavor
- [x] `install.sh` -> `setup.py` for easier pip3 install
- [x] `CameraPipelineDNN` and `CameraPipeline` could have the same base class for code re-use
