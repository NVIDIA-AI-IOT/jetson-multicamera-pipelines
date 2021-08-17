# Encoding

### Inferenece -> tiler -> h264 -> mp4

```
gst-launch-1.0 \
nvarguscamerasrc bufapi-version=1 sensor-id=1 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_0 \
nvarguscamerasrc bufapi-version=1 sensor-id=0 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_1 \
nvarguscamerasrc bufapi-version=1 sensor-id=2 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_2 \
nvstreammux name=m width=1920 height=1080 batch-size=3 ! \
nvinfer config-file-path=jetmulticam/models/peoplenet/peoplenet_dla0.txt ! \
nvmultistreamtiler rows=2 columns=2 width=1920 height=1080 ! \
nvdsosd ! nvvideoconvert ! nvv4l2h264enc bitrate=1000000 ! 'video/x-h264, stream-format=(string)byte-stream' ! \
h264parse ! qtmux ! filesink sync=true location=test_apartment_video.mp4 -e;
```