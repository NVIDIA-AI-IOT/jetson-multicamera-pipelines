
## Pipeline examples


Simple pipeline with nvinfer
```shell
gst-launch-1.0 nvarguscamerasrc bufapi-version=1 ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! mx.sink_0 nvstreammux width=1920 height=1080 batch-size=1 name=mx ! nvinfer config-file-path=dstest1_pgie_config.txt ! nvvideoconvert ! nvdsosd ! nvoverlaysink sync=0
```