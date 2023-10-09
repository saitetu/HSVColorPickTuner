import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QPushButton,QListWidgetItem,QListWidget,QHBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPixmap, QColor
import colorsys


class CameraApp(QMainWindow):

    _isHsv = False
    def __init__(self):
        super().__init__()

        self.initUI()
        self.points = []

    def initUI(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.label = QLabel(self)

        self.setWindowTitle('HSV Color Pick Tuner')
        self.setGeometry(100, 100, 1000, 600)

        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(50)

        self.image = None

        self.label.mousePressEvent = self.get_pixel_color
        self.hsv_ranges_list = QListWidget(self)
        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.label)
        main_layout.addWidget(self.hsv_ranges_list)
        widget = QWidget(self)
        widget.setLayout(main_layout)
        self.layout.addWidget(widget)

        self.info_label = QLabel(self)
        self.info_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.layout.addWidget(self.info_label, alignment=Qt.AlignTop | Qt.AlignLeft)

        self.change_image = QPushButton("Change Image View", self)
        self.change_image.clicked.connect(self.change_image_view)
        self.layout.addWidget(self.change_image)

        self.delete_button = QPushButton("Delete select color", self)
        self.delete_button.clicked.connect(self.delete_selected_range)
        self.layout.addWidget(self.delete_button)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            self.image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.frame = self.image

            if len(self.points) > 4 and self._isHsv:
                hsv_image = cv2.cvtColor(self.image, cv2.COLOR_RGB2HSV)
                lower_bound = np.min(self.points, axis=0)
                upper_bound = np.max(self.points, axis=0)
                if upper_bound[0] > 180:
                    upper_bound2 = np.array([upper_bound[0] - 180, upper_bound[1], upper_bound[2]])
                    upper_bound[0] = 180
                    mask1 = cv2.inRange(hsv_image, lower_bound, upper_bound)
                    mask2 = cv2.inRange(hsv_image, np.array([0, lower_bound[1], lower_bound[2]]), upper_bound2)
                    self.mask = cv2.bitwise_or(mask1, mask2)
                    text_to_display = f"Lower Bound: H({lower_bound[0]}), S({lower_bound[1]}), V({lower_bound[2]})\nUpper Bound: H({upper_bound[0]}), S({upper_bound[1]}), V({upper_bound[2]}\nLower Bound2: H({0}), S({lower_bound[1]}), V({lower_bound[2]})\nUpper Bound2: H({upper_bound2[0]}), S({upper_bound2[1]}), V({upper_bound2[2]}"
                else:
                    self.mask = cv2.inRange(hsv_image, lower_bound, upper_bound)
                    text_to_display = f"Lower Bound: H({lower_bound[0]}), S({lower_bound[1]}), V({lower_bound[2]})\nUpper Bound: H({upper_bound[0]}), S({upper_bound[1]}), V({upper_bound[2]})"
                self.image = cv2.bitwise_and(self.image, self.image, mask=self.mask)
            else:
                text_to_display = "Select 5 points"

            self.info_label.setText(text_to_display)
            h, w, ch = self.image.shape
            bytes_per_line = ch * w
            qt_image = QImage(self.image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            self.label.setPixmap(pixmap)

    def get_pixel_color(self, event):
            x = event.pos().x()
            y = event.pos().y()
            pixel_color = self.frame[y, x]
            hsv_color = cv2.cvtColor(np.uint8([[pixel_color]]), cv2.COLOR_RGB2HSV)[0][0]
            if hsv_color[0] < 20:
                hsv_color[0] += 180
            self.points.append(hsv_color)
            print(f"Clicked Pixel HSV: {hsv_color}")
            self.update_info_label()
    
    def change_image_view(self):
        self._isHsv = not self._isHsv
        if self._isHsv:
            self.change_image.setText("View ORG image")
        else:
            self.change_image.setText("View HSV image")
    
    def update_info_label(self):
        self.hsv_ranges_list.clear()
        for idx, hsv_color in enumerate(self.points, start=1):
            color_preview = ColorPreviewWidget(hsv_color)
            item = QListWidgetItem(f"Range {idx}: H({hsv_color[0]}), S({hsv_color[1]}), V({hsv_color[2]})")
            item.setSizeHint(color_preview.sizeHint())
            self.hsv_ranges_list.addItem(item)
            self.hsv_ranges_list.setItemWidget(item, color_preview)


    def delete_selected_range(self):
        selected_items = self.hsv_ranges_list.selectedItems()
        for item in selected_items:
            row = self.hsv_ranges_list.row(item)
            self.hsv_ranges_list.takeItem(row)
            del self.points[row]



class ColorPreviewWidget(QWidget):
    def __init__(self, hsv_color, parent=None):
        super().__init__(parent)
        print(hsv_color)
        self.rgb_color = self.hsv_to_rgb(hsv_color)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(QColor(*self.rgb_color))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())

    def hsv_to_rgb(self, rgb_color):
        rgb_color = colorsys.hsv_to_rgb(rgb_color[0] / 179, rgb_color[1] / 255, rgb_color[2] / 255)
        return [int(255 * i) for i in rgb_color]


def main():
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
