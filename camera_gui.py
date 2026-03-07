#!/usr/bin/env python3
import sys
import rclpy
from rclpy.node import Node
import numpy as np
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy

from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer

from sensor_msgs.msg import Image
from sensor_msgs.msg import CompressedImage
from cv_bridge import CvBridge
import cv2


class CameraViewer(Node):
    def __init__(self, qt_label=None):
        super().__init__('camera_viewer_node')

        self.qt_label = qt_label
        self.last_frame = None  # <--- Aquí guardaremos el último frame

        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )

        self.subscription = self.create_subscription(
            CompressedImage,
            '/image_raw/compressed',
            self.callback,
            qos_profile
        )

    def callback(self, msg):
        # ROS2 → OpenCV
        frame = cv2.imdecode(np.frombuffer(msg.data, np.uint8), cv2.IMREAD_COLOR)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        self.last_frame = frame  # <--- Guardar el frame

        if self.qt_label is not None:
            h, w, ch = frame.shape
            qimg = QImage(frame.data, w, h, frame.strides[0], QImage.Format.Format_RGB888).copy()
            self.qt_label.setPixmap(QPixmap.fromImage(qimg))
            self.qt_label.repaint()

        


class CameraApp(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ROS2 Camera Viewer - PyQt6")
        self.resize(640, 480)

        # QLabel para mostrar la imagen
        self.label = QLabel("Esperando imagen...")
        self.label.setStyleSheet("background-color: black; color: white;")
        self.label.setScaledContents(True)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Inicializa ROS2
        rclpy.init()
        self.node = CameraViewer(self.label)

        # Timer para integrar ROS en PyQt6 sin congelar el GUI
        self.timer = QTimer()
        self.timer.timeout.connect(self.spin_ros)
        self.timer.start(10)  # cada 10 ms

    def spin_ros(self):
        rclpy.spin_once(self.node, timeout_sec=0.01)


def main():
    app = QApplication(sys.argv)
    gui = CameraApp()
    gui.show()
    sys.exit(app.exec())  # PyQt6 usa exec(), no exec_()


if __name__ == '__main__':
    main()
