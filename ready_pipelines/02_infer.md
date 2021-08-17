# Inference Pipelines

### Simple pipeline with 1 camera and 1 nvinfer
```shell
gst-launch-1.0 nvarguscamerasrc bufapi-version=1 ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! mx.sink_0 nvstreammux width=1920 height=1080 batch-size=1 name=mx ! nvinfer config-file-path=models/resnet10_4class_detector.txt ! nvvideoconvert ! nvdsosd ! nvoverlaysink sync=0
```

### Two infers back-to-back
```shell
gst-launch-1.0 nvarguscamerasrc bufapi-version=1 ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! mx.sink_0 nvstreammux width=1920 height=1080 batch-size=1 name=mx ! nvinfer config-file-path=models/peoplenet.txt ! nvinfer config-file-path=models/resnet10_4class_detector.txt ! nvvideoconvert ! nvdsosd ! nvoverlaysink sync=0
```

### Display 3 cameras, run 2 object detectors in back-to-back configuration
```shell
gst-launch-1.0 \
nvarguscamerasrc bufapi-version=1 sensor-id=1 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_0 \
nvarguscamerasrc bufapi-version=1 sensor-id=0 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_1 \
nvarguscamerasrc bufapi-version=1 sensor-id=2 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_2 \
nvstreammux name=m width=1920 height=1080 batch-size=3 ! \
nvinfer config-file-path=models/peoplenet.txt ! \
nvmultistreamtiler rows=2 columns=2 width=1920 height=1080 ! nvdsosd ! nvegltransform ! nveglglessink sync=0
```

### 3 cameras with 2 DNN inferences in side-by-side configuration 
```shell
gst-launch-1.0 \
nvarguscamerasrc bufapi-version=1 sensor-id=1 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! tee name=t0 ! queue ! m1.sink_0 \
nvarguscamerasrc bufapi-version=1 sensor-id=0 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! tee name=t1 ! queue ! m1.sink_1 \
nvarguscamerasrc bufapi-version=1 sensor-id=2 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! tee name=t2 ! queue ! m1.sink_2 \
nvstreammux name=m1 width=1920 height=1080 batch-size=3 ! nvinfer config-file-path=models/peoplenet.txt ! nvmultistreamtiler rows=2 columns=2 width=1920 height=1080 ! nvdsosd ! nvegltransform ! nveglglessink sync=0 \
t0. ! queue ! m2.sink_0 \
t1. ! queue ! m2.sink_1 \
t2. ! queue ! m2.sink_2 \
nvstreammux name=m2 width=1920 height=1080 batch-size=3 ! nvinfer config-file-path=models/peoplenet.txt ! nvmultistreamtiler rows=2 columns=2 width=1920 height=1080 ! fakesink
```

### 3 cameras with 2 DNN inferences in side-by-side configuration w/ DLA
```shell
gst-launch-1.0 \
nvarguscamerasrc bufapi-version=1 sensor-id=1 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! tee name=t0 ! queue ! m1.sink_0 \
nvarguscamerasrc bufapi-version=1 sensor-id=0 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! tee name=t1 ! queue ! m1.sink_1 \
nvarguscamerasrc bufapi-version=1 sensor-id=2 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! tee name=t2 ! queue ! m1.sink_2 \
nvstreammux name=m1 width=1920 height=1080 batch-size=3 ! nvinfer config-file-path=models/peoplenet_dla_0.txt ! nvmultistreamtiler rows=2 columns=2 width=1920 height=1080 ! nvdsosd ! nvegltransform ! nveglglessink sync=0 \
t0. ! queue ! m2.sink_0 \
t1. ! queue ! m2.sink_1 \
t2. ! queue ! m2.sink_2 \
nvstreammux name=m2 width=1920 height=1080 batch-size=3 ! nvinfer config-file-path=models/peoplenet_dla_1.txt ! nvmultistreamtiler rows=2 columns=2 width=1920 height=1080 ! fakesink
```