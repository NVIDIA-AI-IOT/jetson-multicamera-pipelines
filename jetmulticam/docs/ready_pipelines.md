
# Pipeline examples


## Cameras

### Display single camera
```shell
gst-launch-1.0 nvarguscamerasrc ! 'video/x-raw(memory:NVMM),  width=(int)1920, height=(int)1080, format=(string)NV12,  framerate=(fraction)30/1' ! nvoverlaysink
```

### Display single camera (windowed)
```shell
gst-launch-1.0 nvarguscamerasrc ! 'video/x-raw(memory:NVMM),  width=(int)1920, height=(int)1080, format=(string)NV12,  framerate=(fraction)30/1' ! nvegltransform ! nveglglessink
```

### Display test pattern with nvmultistreamtiler
```shell
gst-launch-1.0 videotestsrc pattern=1 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_0 videotestsrc ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_1 nvstreammux name=m width=1920 height=1080 batch-size=2 ! nvmultistreamtiler rows=2 columns=2 width=1920 height=1080 ! nvdsosd ! nvegltransform ! nveglglessink sync=0
```

### Display test pattern + 1 video
```shell
gst-launch-1.0 \
nvarguscamerasrc bufapi-version=1 sensor-id=0 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_0 \
videotestsrc ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_1 \
nvstreammux name=m width=1920 height=1080 batch-size=2 ! nvmultistreamtiler rows=2 columns=2 width=1920 height=1080 ! nvdsosd ! nvegltransform ! nveglglessink sync=0
```

### Display 3 cameras in tile stream
```shell
gst-launch-1.0 \
nvarguscamerasrc bufapi-version=1 sensor-id=1 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_0 \
nvarguscamerasrc bufapi-version=1 sensor-id=0 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_1 \
nvarguscamerasrc bufapi-version=1 sensor-id=2 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_2 \
nvstreammux name=m width=1920 height=1080 batch-size=3 ! nvmultistreamtiler rows=2 columns=2 width=1920 height=1080 ! nvdsosd ! nvegltransform ! nveglglessink sync=0
```

## Inference

### Simple pipeline with nvinfer
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



# Streaming

### Stream videotestsrc to UDP:5000

source:
```shell
gst-launch-1.0 videotestsrc ! nvvideoconvert ! nvv4l2h264enc insert-sps-pps=true bitrate=16000000 ! rtph264pay ! udpsink port=5000 host=127.0.0.1
```

receiver:
```shell
gst-launch-1.0 -v udpsrc port=5000 ! "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96" ! rtph264depay ! h264parse ! decodebin ! videoconvert ! autovideosink sync=false
```

### Ditto, but with h265

source:
```shell
gst-launch-1.0 videotestsrc ! nvvideoconvert ! nvv4l2h265enc insert-sps-pps=true bitrate=16000000 ! rtph265pay ! udpsink port=5000 host=127.0.0.1
```

receiver:
```shell
gst-launch-1.0 -v udpsrc port=5000 ! "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H265, payload=(int)96" ! rtph265depay ! h265parse ! decodebin ! videoconvert ! autovideosink sync=false
```


### H265 streaming between Jetson and remote host

source:
(change `10.0.0.167` to your PC's IP address)
```shell
gst-launch-1.0 videotestsrc ! nvvideoconvert ! nvv4l2h264enc insert-sps-pps=true bitrate=16000000 ! rtph264pay ! udpsink port=5000 host=10.0.0.167
```

host:
```shell
gst-launch-1.0 -v udpsrc port=5000 ! "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H265, payload=(int)96" ! rtph265depay ! h265parse ! decodebin ! videoconvert ! autovideosink sync=false
```
