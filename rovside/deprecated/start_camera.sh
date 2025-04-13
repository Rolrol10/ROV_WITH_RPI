libcamera-vid --mode 1640:1232:30/1 --codec yuv420 --timeout 0 -o - | \
gst-launch-1.0 fdsrc ! \
rawvideoparse width=1640 height=1232 format=i420 framerate=30/1 ! \
videoscale ! video/x-raw,width=640,height=480 ! \
x264enc tune=zerolatency bitrate=500 speed-preset=ultrafast ! \
h264parse config-interval=1 ! rtph264pay pt=96 config-interval=1 ! \
udpsink host=127.0.0.1 port=9000

