# Jetson Multicamera Pipelines

Easy-to-use realtime CV/AI pipelines for Nvidia Jetson Platform. This project:
- Builds a typical multi-camera pipeline, i.e. `N×(capture)->preprocess->batch->DNN-> <<your application logic here>> ->encode->file I/O + display`. Uses `gstreamer` and `deepstream`  under-the-hood.
- Gives programatic acces to configure the pipeline in python via `jetmulticam` package.
- Utilizes Nvidia HW accleration for minimal CPU usage. For example, you can perform object detection in real-time on 6 camera streams using as little as `16.5%` CPU. See benchmarks below for details.

## Demos

You can easily build your custom logic in python by accessing image data (via `np.array`), as well object detection results.
See examples of person following below:

#### DashCamNet _(DLA0)_ + PeopleNet _(DLA1)_ on 3 camera streams.
We have 3 intependent cameras with ~270° field of view.
Red Boxes correspond to DashCamNet detections, green ones to PeopleNet.
The PeopleNet detections are used to perform person following logic.

https://user-images.githubusercontent.com/26127866/134718385-9861c206-d5f9-4f67-a383-a80f28904ef1.mp4

#### PeopleNet (GPU) on 3 cameras streams.
Robot is operated in manual mode.

https://user-images.githubusercontent.com/26127866/134720518-bbb98c86-71b0-46ee-a3d1-e2d65acc1b4c.mp4

#### DashCamNet (GPU) on 3 camera streams.
Robot is operated in manual mode.

https://user-images.githubusercontent.com/26127866/134721058-8378697f-bbf0-4505-be75-f3dba3080c71.mp4

(All demos are performed in real-time onboard Nvidia Jetson Xavier NX)

## Quickstart

Install:
```shell
git clone https://github.com/NVIDIA-AI-IOT/jetson-multicamera-pipelines.git
cd jetson-multicamera-pipelines
bash scripts/install_dependencies.sh
pip3 install Cython
pip3 install .
```
Run example with your cameras:
```shell
source scripts/env_vars.sh 
cd examples
python3 example.py
```

## Usage example

```python
import time
from jetmulticam import CameraPipelineDNN
from jetmulticam.models import PeopleNet, DashCamNet

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
        arr = pipeline.images[0] # np.array with shape (1080, 1920, 3), i.e. (1080p RGB image)
        dets = pipeline.detections[0] # Detections from the DNNs
        time.sleep(1/30)
```

## Benchmarks

| #   | Scenario                               | # cams | CPU util. <br> (jetmulticam) | CPU util. <br> (nvargus-deamon) | CPU<br>total | GPU % | EMC util % | Power draw | Inference Hardware                                             |
| --- | -------------------------------------- | ------ | -------------------------- | ------------------------------- | ------------ | ----- | ---------- | ---------- | -------------------------------------------------------------- |
| 1.  | 1xGMSL -> 2xDNNs + disp + encode       | 1      | 5.3%                       | 4%                              | 9.3%         | <3%   | 57%        | 8.5W       | DLA0: PeopleNet DLA1: DashCamNet                               |
| 2.  | 2xGMSL -> 2xDNNs + disp + encode       | 2      | 7.2%                       | 7.7%                            | 14.9%        | <3%   | 62%        | 9.4W       | DLA0: PeopleNet DLA1: DashCamNet                               |
| 3.  | 3xGMSL -> 2xDNNs + disp + encode       | 3      | 9.2%                       | 11.3%                           | 20.5%        | <3%   | 68%        | 10.1W      | DLA0: PeopleNet DLA1: DashCamNet                               |
| 4.  | Same as _#3_ with CPU @ 1.9GHz         | 3      | 7.5%                       | 9.0%                            | 16.5%         | <3%   | 68%        | 10.4w      | DLA0: PeopleNet DLA1: DashCamNet                               |
| 5.  | 3xGMSL+2xV4L -> 2xDNNs + disp + encode | 5      | 9.5%                       | 11.3%                           | 20.8%        | <3%   | 45%        | 9.1W       | DLA0: PeopleNet _(interval=1)_ DLA1: DashCamNet _(interval=1)_ |
| 6.  | 3xGMSL+2xV4L -> 2xDNNs + disp + encode | 5      | 8.3%                       | 11.3%                           | 19.6%        | <3%   | 25%        | 7.5W       | DLA0: PeopleNet _(interval=6)_ DLA1: DashCamNet _(interval=6)_ |
| 7.  | 3xGMSL -> DNN + disp + encode          | 5      | 10.3%                      | 12.8%                           | 23.1%        | 99%   | 25%        | 15W        | GPU: PeopleNet                                                 |


Notes:
- All figures are in `15W 6 core mode`. To reproduce do: `sudo nvpmodel -m 2; sudo jetson_clocks;`
- Test platform: [Jetson Xavier NX](https://developer.nvidia.com/embedded/jetson-xavier-nx-devkit) and [XNX Box](https://www.leopardimaging.com/product/nvidia-jetson-cameras/nvidia-nx-mipi-camera-kits/li-xnx-box-gmsl2/) running [JetPack](https://developer.nvidia.com/embedded/jetpack) v4.5.1
- The residual GPU usage in DLA-accelerated nets is caused by Sigmoid activations being computed with CUDA backend. Remaining layers are computed on DLA.
- CPU usage will vary depending on factors such as camera resolution, framerate, available video formats and driver implementation.

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
