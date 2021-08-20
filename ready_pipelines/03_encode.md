# Encoding

### Record video from one camera
```shell
gst-launch-1.0 \
nvarguscamerasrc bufapi-version=1 sensor-id=0 ! \
nvvideoconvert ! \
nvv4l2h264enc bitrate=10000000 ! \
h264parse ! qtmux ! filesink sync=true location=test.mp4 -e;
```

### Inference + encode + save to mp4
```shell
gst-launch-1.0 nvarguscamerasrc bufapi-version=1 ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! mx.sink_0 nvstreammux width=1920 height=1080 batch-size=1 name=mx ! \
nvinfer config-file-path=jetmulticam/models/peoplenet/peoplenet_dla0.txt ! nvvideoconvert ! nvdsosd ! \
nvvideoconvert ! nvv4l2h264enc bitrate=10000000 ! 'video/x-h264, stream-format=(string)byte-stream' ! \
h264parse ! qtmux ! filesink sync=true location=output.mp4 -e;
```

### Same, but with matroskamux
If the pipeline is killed abruptly (without end-of-stream signal) qtmux will output a corrput file.
Matroskamux does not have this issue (notice no `-e` switch)

```shell
gst-launch-1.0 nvarguscamerasrc bufapi-version=1 ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! mx.sink_0 nvstreammux width=1920 height=1080 batch-size=1 name=mx ! \
nvinfer config-file-path=jetmulticam/models/peoplenet/peoplenet_dla0.txt ! nvvideoconvert ! nvdsosd ! \
nvvideoconvert ! nvv4l2h264enc bitrate=10000000 ! 'video/x-h264, stream-format=(string)byte-stream' ! \
h264parse ! matroskamux ! filesink sync=true location=output.mkv;
```

### Inferenece -> tiler -> h264 -> mp4

```
gst-launch-1.0 \
nvarguscamerasrc bufapi-version=1 sensor-id=1 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_0 \
nvarguscamerasrc bufapi-version=1 sensor-id=0 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_1 \
nvarguscamerasrc bufapi-version=1 sensor-id=2 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_2 \
nvstreammux name=m width=1920 height=1080 batch-size=3 ! \
nvinfer config-file-path=jetmulticam/models/peoplenet/peoplenet_dla0.txt ! \
nvmultistreamtiler rows=2 columns=2 width=1920 height=1080 ! \
nvdsosd ! nvvideoconvert ! nvv4l2h264enc bitrate=10000000 ! 'video/x-h264, stream-format=(string)byte-stream' ! \
h264parse ! qtmux ! filesink sync=true location=test_apartment_video.mp4 -e;
```


### Infer and save to mp4
```bash
gst-launch-1.0 \
nvarguscamerasrc bufapi-version=1 sensor-id=0 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_0 \
nvarguscamerasrc bufapi-version=1 sensor-id=1 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_1 \
nvarguscamerasrc bufapi-version=1 sensor-id=2 ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! m.sink_2 \
nvstreammux name=m width=640 height=360 batch-size=3 ! \
nvinfer config-file-path=jetmulticam/models/peoplenet/peoplenet_dla0.txt ! \
nvmultistreamtiler rows=1 columns=3 width=2880 height=360 ! \
nvdsosd !  nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA, width=1920, height=1080, framerate=30/1" ! \
nvvideoconvert ! nvv4l2h264enc bitrate=10000000 ! 'video/x-h264, stream-format=(string)byte-stream' ! \
h264parse ! qtmux ! filesink sync=true location=pano.mp4 -e;
```
