import math

from PyQt6.QtCore import QPointF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

try:
    from sensor_msgs.msg import LaserScan
    from rclpy.node import Node

    LIDAR_ROS_OK = True
except ImportError:
    LaserScan = None
    Node = object
    LIDAR_ROS_OK = False


def _draw_lidar_scene(painter, canvas, ranges, angle_min, angle_increment, point_size=2):
    """Dibuja rejilla + robot + puntos LiDAR o patrón simulado si no hay datos."""
    painter.fillRect(canvas.rect(), QColor(20, 20, 20))
    cx = canvas.width() / 2
    cy = canvas.height() / 2

    # Rejilla
    painter.setPen(QPen(QColor(60, 60, 60), 1))
    for r in (50, 100, 150, 200):
        painter.drawEllipse(QPointF(cx, cy), r, r)

    # Ejes
    painter.setPen(QPen(QColor(70, 70, 70), 1, Qt.PenStyle.DashLine))
    painter.drawLine(0, int(cy), canvas.width(), int(cy))
    painter.drawLine(int(cx), 0, int(cx), canvas.height())

    # Robot (centro)
    painter.setPen(QPen(QColor(255, 255, 255), 2))
    painter.setBrush(QColor(255, 100, 100))
    painter.drawEllipse(QPointF(cx, cy), 6, 6)

    # Puntos reales o simulados
    painter.setPen(QPen(QColor(0, 255, 120), point_size))

    if ranges and angle_increment > 0:
        for i, dist in enumerate(ranges):
            if not math.isfinite(dist) or dist <= 0:
                continue
            angle = angle_min + i * angle_increment
            draw_dist = min(dist * 60, min(cx, cy) - 10)
            px = cx + math.cos(angle) * draw_dist
            py = cy + math.sin(angle) * draw_dist
            painter.drawPoint(QPointF(px, py))
    else:
        # Patrón simulado para visualizar incluso sin datos
        samples = 90
        for i in range(samples):
            angle = (2 * math.pi / samples) * i
            pulse = (math.sin(i * 0.35) + 1) / 2
            draw_dist = 50 + pulse * (min(cx, cy) - 20)
            px = cx + math.cos(angle) * draw_dist
            py = cy + math.sin(angle) * draw_dist
            painter.drawPoint(QPointF(px, py))


if LIDAR_ROS_OK:
    class LidarWidget(Node, QWidget):
        scan_data_received = pyqtSignal(list, float, float)

        def __init__(self, topic_name="/Torpy/scan", scale=60, debug=False):
            Node.__init__(self, "mikael_rplidar_composition")
            QWidget.__init__(self)

            self.debug = debug
            self.ranges = []
            self.angle_min = 0.0
            self.angle_increment = 0.0
            self.point_size = 2

            self._setup_ui()
            self.create_subscription(LaserScan, topic_name, self.scan_callback, 10)
            self.scan_data_received.connect(self.update_scan_data)

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.canvas.update)
            self.timer.start(50)

        def _setup_ui(self):
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
            _draw_lidar_scene(
                painter,
                self.canvas,
                self.ranges,
                self.angle_min,
                self.angle_increment,
                point_size=self.point_size,
            )
else:
    class LidarWidget(QWidget):
        """Fallback sin ROS: siempre grafica patrón LiDAR simulado."""

        def __init__(self, topic_name="/Torpy/scan", scale=60, debug=False):
            super().__init__()
            self.ranges = []
            self.angle_min = 0.0
            self.angle_increment = 0.0
            self.point_size = 2

            root = QVBoxLayout(self)
            title = QLabel("⚠️ LiDAR sin ROS (modo simulado)")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            title.setStyleSheet("color: #e0e0e0;")
            root.addWidget(title)

            self.canvas = QWidget()
            self.canvas.setMinimumSize(400, 400)
            self.canvas.paintEvent = self._paint_lidar
            root.addWidget(self.canvas)

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.canvas.update)
            self.timer.start(80)

        def _paint_lidar(self, event):
            painter = QPainter(self.canvas)
            _draw_lidar_scene(
                painter,
                self.canvas,
                self.ranges,
                self.angle_min,
                self.angle_increment,
                point_size=self.point_size,
            )
