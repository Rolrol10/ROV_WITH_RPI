import os
import subprocess
from flask import Flask, Response

app = Flask(__name__)

# ✅ Adjust this to where GStreamer is installed on your Windows machine
gst_path = r"C:\gstreamer\1.0\msvc_x86_64\bin"
gst_exe = os.path.join(gst_path, "gst-launch-1.0.exe")

# 🔍 Check that GStreamer is available
if not os.path.exists(gst_exe):
    raise FileNotFoundError(f"GStreamer not found at: {gst_exe}")

# Add to PATH so DLLs can be found too
os.environ["PATH"] += os.pathsep + gst_path

# ✅ GStreamer command that sends MJPEG over stdout
gst_cmd = [
    gst_exe,
    "udpsrc", "port=8004",
    "caps=application/x-rtp,media=video,encoding-name=H264,payload=96",
    "!", "rtph264depay",
    "!", "avdec_h264",
    "!", "videoconvert",
    "!", "jpegenc",
    "!", "multipartmux", "boundary=frame",
    "!", "fdsink", "fd=1"
]

# Launch GStreamer subprocess
try:
    gst_proc = subprocess.Popen(
        gst_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,  # or subprocess.STDOUT for debugging
        bufsize=0
    )
except Exception as e:
    print(f"Failed to launch GStreamer: {e}")
    exit(1)

@app.route('/stream')
def stream():
    def generate():
        while True:
            chunk = gst_proc.stdout.readline()
            if not chunk:
                break
            yield chunk

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("✅ Flask MJPEG proxy running at http://localhost:5001/stream")
    app.run(host='0.0.0.0', port=5001, threaded=True)
