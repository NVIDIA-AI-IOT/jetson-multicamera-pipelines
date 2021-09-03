# Inference Pipelines

### Simple pipeline with 1 nvarguscamera camera and 1 nvinfer
```shell
gst-launch-1.0 nvarguscamerasrc bufapi-version=1 ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! mx.sink_0 nvstreammux width=1920 height=1080 batch-size=1 name=mx ! nvinfer config-file-path=/home/nx/nv-multi-camera-robot/jetmulticam/models/peoplenet/peoplenet_dla0.txt ! nvvideoconvert ! nvdsosd ! nvoverlaysink sync=0
```

### Simple pipeline with 1 USB camera and 1 nvinfer
```shell
gst-launch-1.0 v4l2src device=/dev/video3 ! videoconvert ! "video/x-raw, format=(string)RGBA" ! nvvideoconvert ! "video/x-raw(memory:NVMM)" ! mx.sink_0 nvstreammux width=640 height=480 batch-size=1 name=mx ! nvinfer config-file-path=/home/nx/nv-multi-camera-robot/jetmulticam/models/peoplenet/peoplenet_dla0.txt ! nvvideoconvert ! nvdsosd ! nvoverlaysink sync=0
```

### Two infers back-to-back on one camera

Two different DNNs running on DLA0 + DLA1 
```shell
gst-launch-1.0 nvarguscamerasrc bufapi-version=1 ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! mx.sink_0 nvstreammux width=1920 height=1080 batch-size=1 name=mx ! \
nvinfer config-file-path=jetmulticam/models/peoplenet/peoplenet_dla1.txt ! \
nvinfer config-file-path=jetmulticam/models/dashcamnet/dashcamnet_dla0.txt ! \
nvvideoconvert ! nvdsosd ! nvoverlaysink sync=0
```

### Run an object detector on a batch from 3 cameras, display everything in a tile grid
```shell
gst-launch-1.0 \
nvarguscamerasrc bufapi-version=1 sensor-id=1 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_0 \
nvarguscamerasrc bufapi-version=1 sensor-id=0 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_1 \
nvarguscamerasrc bufapi-version=1 sensor-id=2 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_2 \
nvstreammux name=m width=1920 height=1080 batch-size=3 ! \
nvinfer config-file-path=jetmulticam/models/peoplenet/peoplenet_gpu.txt ! \
nvmultistreamtiler rows=2 columns=2 width=1920 height=1080 ! \
nvdsosd ! nvoverlaysink sync=0
```


### 3 cameras with 2 DNN inferences in chained configuration 

```bash
gst-launch-1.0 \
nvarguscamerasrc bufapi-version=1 sensor-id=1 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_0 \
nvarguscamerasrc bufapi-version=1 sensor-id=0 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_1 \
nvarguscamerasrc bufapi-version=1 sensor-id=2 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_2 \
nvstreammux name=m width=1920 height=1080 batch-size=3 ! \
nvinfer config-file-path=jetmulticam/models/peoplenet/peoplenet_gpu.txt ! \
nvinfer config-file-path=jetmulticam/models/dashcamnet/dashcamnet_dla0.txt ! \
nvmultistreamtiler rows=2 columns=2 width=1920 height=1080 ! \
nvdsosd ! nvoverlaysink sync=0
```

### 3 cameras with 2 DNN inferences in side-by-side configuration 
```shell
gst-launch-1.0 \
nvarguscamerasrc bufapi-version=1 sensor-id=1 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! tee name=t0 ! queue ! muxA.sink_0 \
nvarguscamerasrc bufapi-version=1 sensor-id=0 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! tee name=t1 ! queue ! muxA.sink_1 \
nvarguscamerasrc bufapi-version=1 sensor-id=2 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! tee name=t2 ! queue ! muxA.sink_2 \
nvstreammux name=muxA width=1920 height=1080 batch-size=3 ! nvinfer config-file-path=jetmulticam/models/peoplenet/peoplenet_dla0.txt ! nvmultistreamtiler rows=2 columns=2 width=1920 height=1080 ! nvdsosd ! nvegltransform ! nveglglessink sync=0 \
t0. ! queue ! muxB.sink_0 \
t1. ! queue ! muxB.sink_1 \
t2. ! queue ! muxB.sink_2 \
nvstreammux name=muxB width=1920 height=1080 batch-size=3 ! nvinfer config-file-path=jetmulticam/models/peoplenet/peoplenet_dla1.txt ! nvmultistreamtiler rows=2 columns=2 width=1920 height=1080 ! fakesink
```