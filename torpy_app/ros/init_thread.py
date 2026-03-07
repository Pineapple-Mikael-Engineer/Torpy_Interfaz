"""Inicialización asíncrona de componentes ROS."""

from __future__ import annotations

import traceback

from PyQt6.QtCore import QThread, pyqtSignal

from torpy_app import config
from torpy_app.ros.camera_node import CameraSubscriberNode


class InitThread(QThread):
    """Inicializa componentes ROS en segundo plano."""

    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, window):
        super().__init__()
        self.window = window

    def run(self):
        try:
            if not config.ROS_DISPONIBLE:
                print("⚠️  ROS2 no disponible - sin inicialización")
                self.finished_signal.emit()
                return

            print("🔄 Inicializando componentes ROS...")
            self.window.camera_node = CameraSubscriberNode()

            if hasattr(self.window, "widget_camera") and hasattr(self.window.widget_camera, "conectar_nodo_ros"):
                self.window.widget_camera.conectar_nodo_ros(self.window.camera_node)
                self.window.widget_camera.iniciar_camara_real()
                print("  ✅ Cámara conectada")

            if self.window.ros_spin_thread.add_node(self.window.camera_node):
                print("  ✅ Nodo cámara agregado al executor")

            if hasattr(self.window, "widget_lidar") and hasattr(self.window.widget_lidar, "context"):
                if self.window.ros_spin_thread.add_node(self.window.widget_lidar):
                    print("  ✅ Nodo LiDAR agregado al executor")

            self.finished_signal.emit()
        except Exception as error:
            error_msg = f"{error}\n{traceback.format_exc()}"
            self.error_signal.emit(error_msg)
