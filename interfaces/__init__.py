"""API pública de interfaces organizada por dominios."""

from interfaces.widgets import camera_widget as Widgets_cameraCV
from interfaces.widgets import lidar_widget as Widget_lidar
from interfaces.widgets import modulo_velocidad as Modulo_velocidad

__all__ = ["Widgets_cameraCV", "Widget_lidar", "Modulo_velocidad"]
