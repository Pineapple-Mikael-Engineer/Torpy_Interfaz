import math

from PyQt6.QtCore import QPointF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QRadialGradient
from PyQt6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

try:
    from sensor_msgs.msg import LaserScan
    from rclpy.node import Node

    LIDAR_ROS_OK = True
except ImportError:
    LaserScan = None
    Node = object
    LIDAR_ROS_OK = False


if LIDAR_ROS_OK:
    class LidarWidget(Node, QWidget):
        scan_data_received = pyqtSignal(list, float, float)

        def __init__(self, topic_name="/Torpy/scan", scale=60, debug=False):
            Node.__init__(self, "Mikael_rplidar_composition")
            QWidget.__init__(self)

            self.debug = debug
            self.ranges = []
            self.angle_min = 0.0
            self.angle_increment = 0.0
            self.scale = scale
            self.point_size = 3
            self.show_grid = True
            self.show_axes = True

            self.setup_ui()
            self.create_subscription(LaserScan, topic_name, self.scan_callback, 10)
            self.scan_data_received.connect(self.update_scan_data)

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update)
            self.timer.start(50)

        def setup_ui(self):
            root = QVBoxLayout(self)
            header = QLabel("LiDAR Viewer")
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            root.addWidget(header)

            self.canvas = QWidget()
            self.canvas.setMinimumSize(400, 400)
            self.canvas.paintEvent = self._paint_lidar
            root.addWidget(self.canvas)

        def scan_callback(self, msg):
            self.scan_data_received.emit(list(msg.ranges), msg.angle_min, msg.angle_increment)

        def update_scan_data(self, ranges, angle_min, angle_increment):
            self.ranges = ranges
            self.angle_min = angle_min
            self.angle_increment = angle_increment
            self.canvas.update()

        def _paint_lidar(self, event):
            painter = QPainter(self.canvas)
            painter.fillRect(self.canvas.rect(), QColor(20, 20, 20))
            cx = self.canvas.width() / 2
            cy = self.canvas.height() / 2

            painter.setPen(QPen(QColor(60, 60, 60), 1))
            for r in (50, 100, 150):
                painter.drawEllipse(QPointF(cx, cy), r, r)

            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.setBrush(QBrush(QColor(255, 100, 100)))
            painter.drawEllipse(QPointF(cx, cy), 6, 6)

            painter.setPen(QPen(QColor(0, 255, 120), 2))
            for i, dist in enumerate(self.ranges):
                if not math.isfinite(dist) or dist <= 0:
                    continue
                a = self.angle_min + i * self.angle_increment
                px = cx + math.cos(a) * dist * self.scale
                py = cy + math.sin(a) * dist * self.scale
                painter.drawPoint(QPointF(px, py))
else:
    class LidarWidget(QWidget):
        """Fallback sin ROS: mantiene el importable y muestra estado."""

        def __init__(self, topic_name="/Torpy/scan", scale=60, debug=False):
            super().__init__()
            layout = QVBoxLayout(self)
            title = QLabel("⚠️ LiDAR no disponible")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            info = QLabel("Falta ROS2/sensor_msgs en el entorno.\nSe muestra modo visual fallback.")
            info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info.setStyleSheet("color: #bbb;")
            layout.addWidget(title)
            layout.addWidget(info)
