import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer

class CameraApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.points = []  # クリックした点の座標を格納するリスト

    def initUI(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.label = QLabel(self)
        self.layout.addWidget(self.label)

        self.setWindowTitle('Camera App')
        self.setGeometry(100, 100, 800, 600)

        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(50)

        self.image = None

        self.label.mousePressEvent = self.get_pixel_color

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            self.image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # HSV範囲内の色のみを抽出
            if len(self.points) == 4:
                hsv_image = cv2.cvtColor(self.image, cv2.COLOR_RGB2HSV)
                lower_bound = np.min(self.points, axis=0)
                upper_bound = np.max(self.points, axis=0)
                mask = cv2.inRange(hsv_image, lower_bound, upper_bound)
                self.image = cv2.bitwise_and(self.image, self.image, mask=mask)

            h, w, ch = self.image.shape
            bytes_per_line = ch * w
            qt_image = QImage(self.image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            self.label.setPixmap(pixmap)

    def get_pixel_color(self, event):
        if len(self.points) < 4:
            x = event.pos().x()
            y = event.pos().y()
            pixel_color = self.image[y, x]
            hsv_color = cv2.cvtColor(np.uint8([[pixel_color]]), cv2.COLOR_RGB2HSV)[0][0]
            self.points.append(hsv_color)
            print(f"Clicked Pixel HSV: {hsv_color}")

def main():
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
