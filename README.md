# Jetson Multicamera Pipelines
Originally forked from [here](https://github.com/NVIDIA-AI-IOT/jetson-multicamera-pipelines.git). This repository was modified for usage with dual USB Cameras and image stitching. The purpose of this modification is meant to support this [NTU URECA project](https://github.com/HiIAmTzeKean/Jetson-Nano-SLAM).

## Testing

### Hardware tested

- Jetson Nano Developer Kit
- Logitech C910 1080P Webcam (2)

### Software tested

OS: Linux Ubuntu 18.04.6 LTS
Packages: Nvidia Jetpack 4.5.1-b17, DeepstreamSDK 5.1.0, OpenCV 4.1.0

## Quick start

### Installation

```shell
git clone https://github.com/HiIAmTzeKean/jetson-multicamera-pipelines
cd jetson-multicamera-pipelines
bash scripts/install_dependencies.sh
pip3 install -e .
```

#### Running program

Check the file permissions of run before attempting to execute the program. There should be execution rights, else grant it as a sudo user.

```shell
./run
```
