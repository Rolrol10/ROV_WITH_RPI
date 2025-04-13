import socket
from flask import Flask, Response

app = Flask(__name__)

TCP_IP = '127.0.0.1'
TCP_PORT = 9000

@app.route('/stream')
def stream():
    def generate():
        print("Connecting to GStreamer raw stream...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((TCP_IP, TCP_PORT))
        buffer = b""

        while True:
            data = sock.recv(4096)
            if not data:
                break
            buffer += data

            # Find JPEG start and end markers
            while True:
                start = buffer.find(b'\xff\xd8')  # SOI
                end = buffer.find(b'\xff\xd9')    # EOI
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

if __name__ == '__main__':
    print(f"✅ MJPEG HTTP server on http://localhost:5001/stream")
    app.run(host='0.0.0.0', port=5001, threaded=True)
