import cv2

# Change this if you move the viewer to another PC
STREAM_URL = "http://127.0.0.1:5001/stream"

cap = cv2.VideoCapture(STREAM_URL)

if not cap.isOpened():
    print("❌ Could not open MJPEG stream.")
    exit()

print("✅ Stream opened. Press ESC to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Frame dropped or not available.")
        continue

    cv2.imshow("Live MJPEG Stream", frame)

    if cv2.waitKey(1) == 27:
        break  # ESC to quit

cap.release()
cv2.destroyAllWindows()
