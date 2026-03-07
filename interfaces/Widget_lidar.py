import math
import uuid
import subprocess
import os
from sensor_msgs.msg import LaserScan
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QSlider, QGroupBox, QCheckBox)
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QRadialGradient, QBrush
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF
from rclpy.node import Node

# ------------------ WIDGET LIDAR ------------------
class LidarWidget(Node, QWidget):
    scan_data_received = pyqtSignal(list, float, float)

    def __init__(self, topic_name="/Torpy/scan", scale=60, debug=False):
        unique_node_name = f"Mikael_rplidar_composition"
        Node.__init__(self, unique_node_name)
        QWidget.__init__(self)

        self.debug = debug
        self.ranges = []
        self.angle_min = 0.0
        self.angle_increment = 0.0
        self.scale = scale
        self.point_size = 3
        self.show_grid = True
        self.show_axes = True
        self.points_count = 0
        self.min_distance = 0.0
        self.max_distance = 0.0
        self.recording = False

        self.setup_ui()

        # Suscripción a LiDAR
        self.create_subscription(LaserScan, topic_name, self.scan_callback, 10)
        self.scan_data_received.connect(self.update_scan_data)

        # Timer GUI solo para refresco de pantalla
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(33)  # ~30 FPS
        
        self.get_logger().info(f"LidarWidget iniciado. Escuchando en: {topic_name}")

    # ----------------- INTERFAZ -----------------
    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        self.lidar_display = QWidget()
        self.lidar_display.setMinimumSize(400, 400)
        self.lidar_display.paintEvent = self.lidar_paint_event

        controls_group = QGroupBox("Controles LiDAR")
        controls_layout = QVBoxLayout()

        buttons_layout = QHBoxLayout()
        self.rviz_btn = QPushButton("Abrir RVIZ")
        self.rviz_btn.clicked.connect(self.launch_rviz)
        self.record_btn = QPushButton("Grabar Scan")
        self.record_btn.setCheckable(True)
        self.record_btn.clicked.connect(self.toggle_recording)
        self.reset_btn = QPushButton("Reset View")
        self.reset_btn.clicked.connect(self.reset_view)
        buttons_layout.addWidget(self.rviz_btn)
        buttons_layout.addWidget(self.record_btn)
        buttons_layout.addWidget(self.reset_btn)

        visual_layout = QHBoxLayout()
        self.grid_check = QCheckBox("Mostrar Grid")
        self.grid_check.setChecked(True)
        self.grid_check.toggled.connect(self.toggle_grid)
        self.axes_check = QCheckBox("Mostrar Ejes")
        self.axes_check.setChecked(True)
        self.axes_check.toggled.connect(self.toggle_axes)
        visual_layout.addWidget(self.grid_check)
        visual_layout.addWidget(self.axes_check)

        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("Escala:"))
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(10, 200)
        self.scale_slider.setValue(self.scale)
        self.scale_slider.valueChanged.connect(self.change_scale)
        scale_layout.addWidget(self.scale_slider)
        self.scale_label = QLabel(f"{self.scale} px/m")
        scale_layout.addWidget(self.scale_label)

        point_layout = QHBoxLayout()
        point_layout.addWidget(QLabel("Tamaño Puntos:"))
        self.point_slider = QSlider(Qt.Orientation.Horizontal)
        self.point_slider.setRange(1, 10)
        self.point_slider.setValue(self.point_size)
        self.point_slider.valueChanged.connect(self.change_point_size)
        point_layout.addWidget(self.point_slider)

        self.stats_label = QLabel("Puntos: 0 | Min: 0.0m | Max: 0.0m")
        self.stats_label.setStyleSheet("QLabel { background-color: #2a2a2a; color: #00ff00; padding: 5px; }")
        self.stats_label.setFont(QFont("Monospace", 9))

        controls_layout.addLayout(buttons_layout)
        controls_layout.addLayout(visual_layout)
        controls_layout.addLayout(scale_layout)
        controls_layout.addLayout(point_layout)
        controls_layout.addWidget(self.stats_label)
        controls_group.setLayout(controls_layout)

        main_layout.addWidget(self.lidar_display)
        main_layout.addWidget(controls_group)
        self.setLayout(main_layout)
        self.setWindowTitle("LiDAR Visualizer - ROS2")

    # ----------------- PINTADO -----------------
    def lidar_paint_event(self, event):
        painter = QPainter(self.lidar_display)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.draw_background(painter)

        cx, cy = self.lidar_display.width()//2, self.lidar_display.height()//2
        max_radius = int(min(cx, cy) * 0.85)

        if self.show_grid:
            self.draw_grid(painter, cx, cy, max_radius)
        if self.show_axes:
            self.draw_axes(painter, cx, cy, max_radius)

        self.draw_lidar_points(painter, cx, cy, max_radius)
        self.draw_center_info(painter, cx, cy)

    def draw_background(self, painter):
        """Dibuja el fondo degradado"""
        painter.fillRect(self.lidar_display.rect(), QColor(20, 20, 30))

    def draw_grid(self, painter, cx, cy, max_radius):
        """Dibuja la cuadrícula circular"""
        painter.setPen(QPen(QColor(50, 50, 70), 1, Qt.PenStyle.DotLine))
        for i in range(1, 6):
            radius = int(max_radius * i / 5)
            painter.drawEllipse(QPointF(cx, cy), radius, radius)
            
        # Líneas radiales cada 30 grados
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            x = cx + int(max_radius * math.cos(rad))
            y = cy - int(max_radius * math.sin(rad))
            painter.drawLine(cx, cy, x, y)

    def draw_axes(self, painter, cx, cy, max_radius):
        """Dibuja los ejes principales"""
        painter.setPen(QPen(QColor(100, 100, 150), 2))
        painter.drawLine(cx - max_radius, cy, cx + max_radius, cy)
        painter.drawLine(cx, cy - max_radius, cx, cy + max_radius)
        
        # Etiquetas de ángulos
        painter.setPen(QColor(150, 150, 200))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(cx + max_radius - 30, cy - 10, "0°")
        painter.drawText(cx + 10, cy - max_radius + 20, "90°")
        painter.drawText(cx - max_radius + 10, cy - 10, "180°")
        painter.drawText(cx + 10, cy + max_radius - 10, "270°")

    def draw_lidar_points(self, painter, cx, cy, max_radius):
        """Dibuja los puntos del LiDAR con color según distancia"""
        if not self.ranges:
            return

        for i, r in enumerate(self.ranges):
            # Filtrar valores inválidos
            if math.isinf(r) or math.isnan(r) or r <= 0.0:
                continue

            angle = self.angle_min + i * self.angle_increment
            
            # Convertir coordenadas polares a cartesianas
            # En ROS, 0° apunta hacia adelante (eje X positivo)
            x = cx + int(r * self.scale * math.cos(angle))
            y = cy - int(r * self.scale * math.sin(angle))

            # Color según distancia
            if r < 0.5:
                color = QColor(255, 0, 0)  # Rojo: muy cerca (peligro)
            elif r < 2.0:
                color = QColor(255, 255, 0)  # Amarillo: cerca (advertencia)
            else:
                color = QColor(0, 255, 0)  # Verde: lejos (seguro)

            painter.setPen(QPen(color, self.point_size))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(x, y), self.point_size/2, self.point_size/2)

    def draw_center_info(self, painter, cx, cy):
        """Dibuja el robot en el centro"""
        # Robot (círculo central azul)
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(QColor(100, 100, 255)))
        painter.drawEllipse(QPointF(cx, cy), 8, 8)
        
        # Indicador de dirección frontal (línea amarilla)
        painter.setPen(QPen(QColor(255, 255, 0), 3))
        painter.drawLine(cx, cy, cx + 15, cy)

    # ----------------- SLOTS (CONTROLES) -----------------
    def launch_rviz(self):
        """Abre RVIZ2 para visualización adicional"""
        try:
            config_path = "/home/mikael/.rviz2/config_rp_lidar.rviz"
            env = os.environ.copy()
            env['ROS_DISTRO'] = env.get('ROS_DISTRO','humble')
            if os.path.exists(config_path):
                subprocess.Popen(['rviz2','-d',config_path], env=env)
            else:
                subprocess.Popen(['rviz2'], env=env)
            self.get_logger().info("RVIZ2 lanzado")
        except Exception as e:
            self.get_logger().error(f"Error al lanzar RVIZ2: {e}")

    def toggle_recording(self, checked):
        """Activa/desactiva la grabación de scans"""
        self.recording = checked
        if checked:
            self.record_btn.setText("⏺ Grabando...")
            self.record_btn.setStyleSheet("background-color: red; color: white;")
            self.get_logger().info("Iniciando grabación de scans")
        else:
            self.record_btn.setText("Grabar Scan")
            self.record_btn.setStyleSheet("")
            self.get_logger().info("Grabación detenida")

    def reset_view(self):
        """Resetea la vista a valores por defecto"""
        self.scale = 60
        self.scale_slider.setValue(self.scale)
        self.point_size = 3
        self.point_slider.setValue(self.point_size)
        self.update()

    def toggle_grid(self, checked):
        """Muestra/oculta la cuadrícula"""
        self.show_grid = checked
        self.update()

    def toggle_axes(self, checked):
        """Muestra/oculta los ejes"""
        self.show_axes = checked
        self.update()

    def change_scale(self, value):
        """Cambia la escala de visualización"""
        self.scale = value
        self.scale_label.setText(f"{value} px/m")
        self.update()

    def change_point_size(self, value):
        """Cambia el tamaño de los puntos"""
        self.point_size = value
        self.update()

    # ----------------- ROS CALLBACKS -----------------
    def scan_callback(self, msg: LaserScan):
        """Callback cuando se recibe un mensaje LaserScan del LiDAR"""
        if self.debug:
            self.get_logger().info(f"Scan recibido: {len(msg.ranges)} puntos")
        
        # Emitir señal para actualizar en el hilo principal de Qt
        self.scan_data_received.emit(
            list(msg.ranges),
            msg.angle_min,
            msg.angle_increment
        )

    def update_scan_data(self, ranges, angle_min, angle_increment):
        """Actualiza los datos del scan (ejecutado en hilo principal Qt)"""
        self.ranges = ranges
        self.angle_min = angle_min
        self.angle_increment = angle_increment
        
        # Calcular estadísticas
        valid_ranges = [r for r in ranges if not math.isinf(r) and not math.isnan(r) and r > 0]
        
        if valid_ranges:
            self.points_count = len(valid_ranges)
            self.min_distance = min(valid_ranges)
            self.max_distance = max(valid_ranges)
            
            # Actualizar etiqueta de estadísticas
            self.stats_label.setText(
                f"Puntos: {self.points_count} | "
                f"Min: {self.min_distance:.2f}m | "
                f"Max: {self.max_distance:.2f}m"
            )
        else:
            self.points_count = 0
            self.stats_label.setText("Puntos: 0 | Sin datos válidos")

    def closeEvent(self, event):
        """Limpieza al cerrar el widget"""
        self.get_logger().info("Cerrando LidarWidget...")
        self.update_timer.stop()
        super().closeEvent(event)