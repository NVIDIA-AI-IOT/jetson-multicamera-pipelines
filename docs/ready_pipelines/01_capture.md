# Camera Capture 


## Display single camera
```shell
gst-launch-1.0 nvarguscamerasrc ! 'video/x-raw(memory:NVMM),  width=(int)1920, height=(int)1080, format=(string)NV12,  framerate=(fraction)30/1' ! nvoverlaysink
```

## Display single camera (windowed)
```shell
gst-launch-1.0 nvarguscamerasrc ! 'video/x-raw(memory:NVMM),  width=(int)1920, height=(int)1080, format=(string)NV12,  framerate=(fraction)30/1' ! nvegltransform ! nveglglessink
```

## Display single USB camera (xvimagesink)
```shell
gst-launch-1.0 v4l2src device=/dev/video3 ! videoconvert ! "video/x-raw, format=(string)RGBA" ! videoconvert ! xvimagesink sync=false
```

## Display single USB camera (nvoverlaysink)
```shell
gst-launch-1.0 v4l2src device=/dev/video3 ! videoconvert ! "video/x-raw, format=(string)RGBA" ! nvvidconv ! nvoverlaysink sync=false
```

## Display single USB camera (nvvideoconvert + nvoverlaysink)
Explicitly set memory:NVMM caps
```shell
gst-launch-1.0 v4l2src device=/dev/video3 ! videoconvert ! "video/x-raw, format=(string)RGBA" ! videoconvert ! nvvideoconvert ! "video/x-raw(memory:NVMM)" ! nvoverlaysink sync=false
```

## Display test pattern with nvmultistreamtiler
```shell
gst-launch-1.0 videotestsrc pattern=1 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_0 videotestsrc ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_1 nvstreammux name=m width=1920 height=1080 batch-size=2 ! nvmultistreamtiler rows=2 columns=2 width=1920 height=1080 ! nvdsosd ! nvegltransform ! nveglglessink sync=0
```

## Display test pattern + 1 video
```shell
gst-launch-1.0 \
nvarguscamerasrc bufapi-version=1 sensor-id=0 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_0 \
videotestsrc ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_1 \
nvstreammux name=m width=1920 height=1080 batch-size=2 ! nvmultistreamtiler rows=2 columns=2 width=1920 height=1080 ! nvdsosd ! nvegltransform ! nveglglessink sync=0
```

## Display 3 cameras in tile stream
```shell
gst-launch-1.0 \
nvarguscamerasrc bufapi-version=1 sensor-id=0 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_0 \
nvarguscamerasrc bufapi-version=1 sensor-id=1 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_1 \
nvarguscamerasrc bufapi-version=1 sensor-id=2 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_2 \
nvstreammux name=m width=1920 height=1080 batch-size=3 ! nvmultistreamtiler rows=2 columns=2 width=1920 height=1080 ! nvdsosd ! nvegltransform ! nveglglessink sync=0
```



gst-launch-1.0 \
nvarguscamerasrc bufapi-version=1 sensor-id=0 ! fakesink \
nvarguscamerasrc bufapi-version=1 sensor-id=1 ! fakesink \
nvarguscamerasrc bufapi-version=1 sensor-id=2 ! fakesink ;