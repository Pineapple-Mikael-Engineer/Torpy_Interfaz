import math

from PyQt6.QtCore import QPointF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
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


def _draw_lidar_scene(
    painter,
    canvas,
    ranges,
    angle_min,
    angle_increment,
    point_size,
    show_grid,
    show_axes,
    scale_factor,
):
    painter.fillRect(canvas.rect(), QColor(20, 20, 20))
    cx = canvas.width() / 2
    cy = canvas.height() / 2

    if show_grid:
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        for r in (50, 100, 150, 200):
            painter.drawEllipse(QPointF(cx, cy), r, r)

    if show_axes:
        painter.setPen(QPen(QColor(70, 70, 70), 1, Qt.PenStyle.DashLine))
        painter.drawLine(0, int(cy), canvas.width(), int(cy))
        painter.drawLine(int(cx), 0, int(cx), canvas.height())

    painter.setPen(QPen(QColor(255, 255, 255), 2))
    painter.setBrush(QColor(255, 100, 100))
    painter.drawEllipse(QPointF(cx, cy), 6, 6)

    painter.setPen(QPen(QColor(0, 255, 120), max(1, int(point_size))))

    if ranges and angle_increment > 0:
        for i, dist in enumerate(ranges):
            if not math.isfinite(dist) or dist <= 0:
                continue
            angle = angle_min + i * angle_increment
            draw_dist = min(dist * scale_factor, min(cx, cy) - 10)
            px = cx + math.cos(angle) * draw_dist
            py = cy + math.sin(angle) * draw_dist
            painter.drawPoint(QPointF(px, py))
    else:
        samples = 90
        for i in range(samples):
            angle = (2 * math.pi / samples) * i
            pulse = (math.sin(i * 0.35) + 1) / 2
            draw_dist = 50 + pulse * (min(cx, cy) - 20)
            px = cx + math.cos(angle) * draw_dist
            py = cy + math.sin(angle) * draw_dist
            painter.drawPoint(QPointF(px, py))


class _LidarUiMixin:
    def _setup_common_ui(self, title_text: str):
        root = QVBoxLayout(self)

        header = QLabel(title_text)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        root.addWidget(header)

        content = QHBoxLayout()
        root.addLayout(content)

        self.canvas = QWidget()
        self.canvas.setMinimumSize(360, 360)
        self.canvas.paintEvent = self._paint_lidar
        content.addWidget(self.canvas, stretch=6)

        side = QGroupBox("Controles LiDAR")
        side_layout = QVBoxLayout(side)

        self.label_estado = QLabel("Estado: Simulado" if not LIDAR_ROS_OK else "Estado: Activo")
        self.label_puntos = QLabel("Puntos: 0")
        self.label_escala = QLabel("Escala: 60")

        self.chk_grid = QCheckBox("Mostrar rejilla")
        self.chk_grid.setChecked(True)
        self.chk_axes = QCheckBox("Mostrar ejes")
        self.chk_axes.setChecked(True)

        self.slider_escala = QSlider(Qt.Orientation.Horizontal)
        self.slider_escala.setRange(10, 120)
        self.slider_escala.setValue(60)

        self.slider_point_size = QSlider(Qt.Orientation.Horizontal)
        self.slider_point_size.setRange(1, 6)
        self.slider_point_size.setValue(2)

        self.btn_limpiar = QPushButton("Limpiar puntos")

        side_layout.addWidget(self.label_estado)
        side_layout.addWidget(self.label_puntos)
        side_layout.addWidget(self.label_escala)
        side_layout.addWidget(self.chk_grid)
        side_layout.addWidget(self.chk_axes)
        side_layout.addWidget(QLabel("Escala"))
        side_layout.addWidget(self.slider_escala)
        side_layout.addWidget(QLabel("Tamaño de punto"))
        side_layout.addWidget(self.slider_point_size)
        side_layout.addWidget(self.btn_limpiar)
        side_layout.addStretch()

        content.addWidget(side, stretch=4)

        self.chk_grid.toggled.connect(self._on_toggle_grid)
        self.chk_axes.toggled.connect(self._on_toggle_axes)
        self.slider_escala.valueChanged.connect(self._on_scale_changed)
        self.slider_point_size.valueChanged.connect(self._on_point_size_changed)
        self.btn_limpiar.clicked.connect(self._clear_points)

    def _on_toggle_grid(self, checked):
        self.show_grid = checked
        self.canvas.update()

    def _on_toggle_axes(self, checked):
        self.show_axes = checked
        self.canvas.update()

    def _on_scale_changed(self, value):
        self.scale_factor = value
        self.label_escala.setText(f"Escala: {value}")
        self.canvas.update()

    def _on_point_size_changed(self, value):
        self.point_size = value
        self.canvas.update()

    def _clear_points(self):
        self.ranges = []
        self.label_puntos.setText("Puntos: 0")
        self.canvas.update()


if LIDAR_ROS_OK:
    class LidarWidget(Node, QWidget, _LidarUiMixin):
        scan_data_received = pyqtSignal(list, float, float)

        def __init__(self, topic_name="/Torpy/scan", scale=60, debug=False):
            Node.__init__(self, "mikael_rplidar_composition")
            QWidget.__init__(self)

            self.debug = debug
            self.ranges = []
            self.angle_min = 0.0
            self.angle_increment = 0.0
            self.point_size = 2
            self.show_grid = True
            self.show_axes = True
            self.scale_factor = scale

            self._setup_common_ui("LiDAR Viewer")
            self.label_estado.setText(f"Estado: Escuchando {topic_name}")

            self.create_subscription(LaserScan, topic_name, self.scan_callback, 10)
            self.scan_data_received.connect(self.update_scan_data)

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.canvas.update)
            self.timer.start(50)

        def scan_callback(self, msg):
            self.scan_data_received.emit(list(msg.ranges), msg.angle_min, msg.angle_increment)

        def update_scan_data(self, ranges, angle_min, angle_increment):
            self.ranges = ranges
            self.angle_min = angle_min
            self.angle_increment = angle_increment
            self.label_puntos.setText(f"Puntos: {len(ranges)}")
            self.canvas.update()

        def _paint_lidar(self, event):
            painter = QPainter(self.canvas)
            _draw_lidar_scene(
                painter,
                self.canvas,
                self.ranges,
                self.angle_min,
                self.angle_increment,
                self.point_size,
                self.show_grid,
                self.show_axes,
                self.scale_factor,
            )
else:
    class LidarWidget(QWidget, _LidarUiMixin):
        """Fallback sin ROS: siempre grafica patrón LiDAR simulado con controles."""

        def __init__(self, topic_name="/Torpy/scan", scale=60, debug=False):
            super().__init__()
            self.ranges = []
            self.angle_min = 0.0
            self.angle_increment = 0.0
            self.point_size = 2
            self.show_grid = True
            self.show_axes = True
            self.scale_factor = scale

            self._setup_common_ui("⚠️ LiDAR sin ROS (modo simulado)")
            self.label_estado.setText("Estado: Simulación local")

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
                self.point_size,
                self.show_grid,
                self.show_axes,
                self.scale_factor,
            )
