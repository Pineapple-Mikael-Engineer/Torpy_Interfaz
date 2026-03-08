"""API pública de interfaces organizada por dominios."""

Widgets_cameraCV = None
Widget_lidar = None
Modulo_velocidad = None

try:
    from interfaces.widgets import camera_widget as Widgets_cameraCV
except ImportError:
    Widgets_cameraCV = None

try:
    from interfaces.widgets import lidar_widget as Widget_lidar
except ImportError:
    Widget_lidar = None

try:
    from interfaces.widgets import modulo_velocidad as Modulo_velocidad
except ImportError:
    Modulo_velocidad = None

__all__ = ["Widgets_cameraCV", "Widget_lidar", "Modulo_velocidad"]
