"""Punto de entrada de la aplicación."""

from __future__ import annotations

import signal
import sys

from PyQt6.QtWidgets import QApplication

from torpy_app import config


def _signal_handler(sig, frame):
    print("\n🛑 Señal recibida, cerrando limpiamente...")
    sys.exit(0)


def run() -> int:
    """Inicializa dependencias y ejecuta la GUI principal."""
    signal.signal(signal.SIGINT, _signal_handler)

    config.cargar_dependencias()

    from torpy_app.ui import VentanaTurtlebot

    app = QApplication(sys.argv)
    window = VentanaTurtlebot()
    window.show()
    return app.exec()
