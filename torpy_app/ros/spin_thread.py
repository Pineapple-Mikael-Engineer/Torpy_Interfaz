"""Hilo para procesar nodos ROS2."""

from __future__ import annotations

from PyQt6.QtCore import QThread

from torpy_app import config


class UnifiedRosSpinThread(QThread):
    """Hilo para procesar ROS2 sin bloquear GUI."""

    def __init__(self):
        super().__init__()
        self.running = True
        self.executor = None

        if config.ROS_DISPONIBLE and config.rclpy.ok():
            try:
                self.executor = config.MultiThreadedExecutor()
                print("✅ MultiThreadedExecutor creado")
            except Exception as error:
                print(f"⚠️  Error creando executor: {error}")
        else:
            print("⚠️  No se creará executor (ROS2 no disponible o no inicializado)")

    def add_node(self, node):
        if not self.executor:
            print("⚠️  Sin executor - no se puede agregar nodo")
            return False

        if not hasattr(node, "context"):
            print(f"⚠️  {node} no es un nodo ROS válido")
            return False

        try:
            self.executor.add_node(node)
            print(f"✅ Nodo agregado: {node.get_name()}")
            return True
        except Exception as error:
            print(f"⚠️  Error agregando nodo {node.get_name()}: {error}")
            return False

    def run(self):
        if not self.executor:
            print("⚠️  Sin executor - hilo ROS inactivo")
            return

        print("🔄 Hilo ROS iniciado")
        while self.running:
            try:
                self.executor.spin_once(timeout_sec=0.01)
            except Exception as error:
                print(f"⚠️  Error en spin: {error}")
                break
        print("🛑 Hilo ROS detenido")

    def stop(self):
        self.running = False
        if self.executor:
            try:
                self.executor.shutdown()
            except Exception:
                pass
