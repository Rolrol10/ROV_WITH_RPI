#!/bin/bash

echo "📡 Starting MediaMTX..."
./mediamtx &

sleep 1  # give MediaMTX a second to initialize

libcamera-vid --inline --codec h264 --width 640 --height 480 -t 0 -o - | \
gst-launch-1.0 fdsrc ! h264parse config-interval=1 ! rtph264pay pt=96 ! \
rtspclientsink location=rtsp://localhost:8554/cam

wait
