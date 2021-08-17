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

### The same, but with h265

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
