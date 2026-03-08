"""Ventana principal y composición de widgets."""

from __future__ import annotations

import traceback

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget

from torpy_app import config
from torpy_app.ros import InitThread, UnifiedRosSpinThread


class VentanaTurtlebot(QMainWindow):
    """Ventana principal de control del TurtleBot."""

    def __init__(self):
        super().__init__()

        print("\n" + "=" * 50)
        print("🚀 Iniciando TurtleBot Control Center")
        print("=" * 50 + "\n")

        self.setWindowTitle("TurtleBot Control Center 🤖")
        self.resize(1200, 800)

        self.camera_node = None
        self.ros_spin_thread = None
        self.init_thread = None

        self.widget_velocidad = None
        self.widget_camera = None
        self.widget_lidar = None

        self._inicializar_ros2()
        self._crear_hilo_ros()
        self._crear_widgets()
        self._construir_ui()
        self._iniciar_componentes_ros()

        print("\n✅ Ventana principal lista\n")

    def _inicializar_ros2(self):
        if not config.ROS_DISPONIBLE:
            print("⚠️  ROS2 no disponible - modo sin ROS\n")
            return

        if not config.rclpy.ok():
            try:
                config.rclpy.init()
                print("✅ ROS2 inicializado\n")
            except Exception as error:
                print(f"❌ Error inicializando ROS2: {error}\n")
        else:
            print("✅ ROS2 ya estaba inicializado\n")

    def _crear_hilo_ros(self):
        self.ros_spin_thread = UnifiedRosSpinThread()
        print("✅ Hilo ROS creado (aún no iniciado)\n")

    def _crear_widgets(self):
        print("🔄 Creando widgets...")

        self.widget_velocidad = self._instanciar_widget_velocidad()
        self.widget_camera = self._instanciar_widget_camara()
        self.widget_lidar = self._instanciar_widget_lidar()

        print()

    def _instanciar_widget_velocidad(self):
        if config.Modulo_velocidad:
            try:
                print("  ✅ Widget velocidad")
                return config.Modulo_velocidad.Widget_Modulo_velocidad()
            except Exception as error:
                print(f"  ⚠️  Error widget velocidad: {error}")
                traceback.print_exc()
        else:
            print("  ⚠️  Modulo_velocidad no disponible")
        return self._crear_widget_placeholder("Velocidad")

    def _instanciar_widget_camara(self):
        if config.Widgets_cameraCV:
            try:
                print("  ✅ Widget cámara")
                return config.Widgets_cameraCV.CameraDiagramWidget()
            except Exception as error:
                print(f"  ⚠️  Error widget cámara: {error}")
                traceback.print_exc()
        else:
            print("  ⚠️  Widgets_cameraCV no disponible")
        return self._crear_widget_placeholder("Cámara")

    def _instanciar_widget_lidar(self):
        if config.Widget_lidar:
            try:
                print("  ✅ Widget LiDAR")
                return config.Widget_lidar.LidarWidget(topic_name="/scan", scale=100, debug=True)
            except Exception as error:
                print(f"  ⚠️  Error widget LiDAR: {error}")
                traceback.print_exc()
        else:
            print("  ⚠️  Widget_lidar no disponible")
        return self._crear_widget_placeholder("LiDAR")

    def _crear_widget_placeholder(self, nombre):
        widget = QWidget()
        layout = QVBoxLayout()
        label = QLabel(f"⚠️ {nombre}\nNo disponible")
        label.setStyleSheet(
            """
            QLabel {
                font-size: 20px;
                color: #888;
                background: #f0f0f0;
                padding: 20px;
                border-radius: 10px;
            }
            """
        )
        layout.addWidget(label)
        widget.setLayout(layout)
        return widget

    def _construir_ui(self):
        print("🔄 Construyendo UI...")

        central_widget = QWidget()
        layout_total = QHBoxLayout()

        left_widget = QWidget()
        layout_left = QVBoxLayout()
        layout_left.addWidget(self.widget_velocidad, stretch=20)
        layout_left.addWidget(self.widget_camera, stretch=30)
        left_widget.setLayout(layout_left)

        layout_total.addWidget(left_widget, stretch=40)
        layout_total.addWidget(self.widget_lidar, stretch=50)

        central_widget.setLayout(layout_total)
        self.setCentralWidget(central_widget)

        print("  ✅ UI construida\n")

    def _iniciar_componentes_ros(self):
        if not config.ROS_DISPONIBLE:
            print("⚠️  Sin ROS2 - no hay componentes que iniciar\n")
            return

        print("🔄 Iniciando componentes ROS en segundo plano...\n")
        self.ros_spin_thread.start()
        QTimer.singleShot(100, self._iniciar_nodos)

    def _iniciar_nodos(self):
        self.init_thread = InitThread(self)
        self.init_thread.finished_signal.connect(self.on_init_finished)
        self.init_thread.error_signal.connect(self.on_init_error)
        self.init_thread.start()

    def on_init_finished(self):
        print("\n✅ Inicialización ROS completa")
        print("📹 Esperando frames de cámara...\n")

    def on_init_error(self, error_msg):
        print(f"\n❌ Error en inicialización:\n{error_msg}\n")

    def closeEvent(self, event):
        print("\n" + "=" * 50)
        print("🛑 Cerrando aplicación")
        print("=" * 50 + "\n")

        if self.ros_spin_thread:
            print("  - Deteniendo hilo ROS...")
            self.ros_spin_thread.stop()
            self.ros_spin_thread.wait(1000)

        if self.camera_node:
            try:
                self.camera_node.destroy_node()
                print("  - Nodo cámara destruido")
            except Exception as error:
                print(f"    Error: {error}")

        if hasattr(self.widget_lidar, "destroy_node"):
            try:
                self.widget_lidar.destroy_node()
                print("  - Nodo LiDAR destruido")
            except Exception as error:
                print(f"    Error: {error}")

        if config.ROS_DISPONIBLE and config.rclpy.ok():
            try:
                config.rclpy.shutdown()
                print("  - ROS2 shutdown")
            except Exception as error:
                print(f"    Error: {error}")

        print("\n✅ Limpieza completa\n")
        event.accept()
