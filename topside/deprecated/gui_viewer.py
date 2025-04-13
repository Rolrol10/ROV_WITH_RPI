import sys
import threading
import cv2
from PyQt5 import QtWidgets, QtGui, QtCore

TYPE = "gui"

STREAM_URL = "http://10.253.0.10:8889/cam"  # Change if needed

class VideoWidget(QtWidgets.QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setScaledContents(True)

    def update_image(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qt_image)
        self.setPixmap(pixmap)

class VideoApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔴 Live ROV Feed")
        self.setGeometry(100, 100, 800, 600)

        self.video_label = VideoWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.video_label)
        self.setLayout(layout)

        self.cap = cv2.VideoCapture(STREAM_URL)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~33ms for ~30 FPS

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            self.video_label.update_image(frame)

    def closeEvent(self, event):
        self.cap.release()
        event.accept()

def run_gui():
    app = QtWidgets.QApplication(sys.argv)
    window = VideoApp()
    window.show()
    sys.exit(app.exec_())

# Required by the modular system
def run(_url=None):
    threading.Thread(target=run_gui, daemon=True).start()
