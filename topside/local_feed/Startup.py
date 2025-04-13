import os
import socket
import subprocess
import threading
from flask import Flask, Response
import webbrowser
import time
import sys

# --- CONFIG ---

GSTREAMER_PATH = r"C:\gstreamer\1.0\msvc_x86_64\bin"
GSTREAMER_PORT = 8004
TCP_STREAM_PORT = 9000
FLASK_PORT = 5001
AUTO_OPEN_BROWSER = False
AUTO_LAUNCH_VIEWER = True
PS4_CONTROLLER = True
XBOX_CONTROLLER = False

# --- Setup PATH ---
os.environ["PATH"] += os.pathsep + GSTREAMER_PATH
gst_exe = os.path.join(GSTREAMER_PATH, "gst-launch-1.0.exe")

# --- Start GStreamer pipeline as subprocess ---
gst_cmd = [
    gst_exe,
    "udpsrc", f"port={GSTREAMER_PORT}",
    "caps=application/x-rtp,media=video,encoding-name=H264,payload=96",
    "!", "rtph264depay",
    "!", "avdec_h264",
    "!", "videoconvert",
    "!", "jpegenc",
    "!", "tcpserversink", f"host=127.0.0.1", f"port={TCP_STREAM_PORT}"
]

# print("📡 Starting GStreamer...")
# gst_proc = subprocess.Popen(gst_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def detect_stream_sender(port=8004):
    print(f"🎯 Waiting for UDP stream on port {port}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(10.0)  # Optional timeout so it doesn't hang forever
    try:
        s.bind(("", port))
        data, addr = s.recvfrom(65535)
        print(f"📡 Video stream detected from: {addr[0]}")
    except socket.timeout:
        print("⚠️  No video stream detected within 10 seconds.")
    finally:
        s.close()

# Optional: detect stream source first
threading.Thread(target=detect_stream_sender, daemon=True).start()

# Start GStreamer after a short delay
time.sleep(1)
print("📡 Starting GStreamer...")
gst_proc = subprocess.Popen(gst_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# --- Flask app setup ---
app = Flask(__name__)

@app.route('/stream')
def stream():
    def generate():
        print("🧠 Connecting to GStreamer TCP stream...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", TCP_STREAM_PORT))
        buffer = b""

        while True:
            data = sock.recv(4096)
            if not data:
                break
            buffer += data

            while True:
                start = buffer.find(b'\xff\xd8')
                end = buffer.find(b'\xff\xd9')
                if start != -1 and end != -1 and end > start:
                    frame = buffer[start:end+2]
                    buffer = buffer[end+2:]
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" +
                        frame +
                        b"\r\n"
                    )
                else:
                    break
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

# --- Start everything ---
def start_flask():
    print(f"🌐 Starting Flask MJPEG server at http://localhost:{FLASK_PORT}/stream")
    app.run(host='0.0.0.0', port=FLASK_PORT, threaded=True)



if __name__ == "__main__":
    threading.Thread(target=start_flask, daemon=True).start()

    # Launch the OpenCV viewer
    if AUTO_LAUNCH_VIEWER:
        print("🎥 Launching OpenCV viewer...")
        subprocess.Popen([sys.executable, "viewer_opencv.py"])
        # detect_stream_sender()

    # Open stream in browser
    if AUTO_OPEN_BROWSER:
        time.sleep(2)
        webbrowser.open(f"http://localhost:{FLASK_PORT}/stream")

    # Start controller setup
    # PS4 Controller
    if PS4_CONTROLLER:
        print("Connecting PS4 Controller")
        subprocess.Popen([sys.executable, "ps4_gamepad.py"])
    # XBOX Controller
    elif XBOX_CONTROLLER:
        print("XBOX controller module not made yet")

    

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        gst_proc.terminate()
