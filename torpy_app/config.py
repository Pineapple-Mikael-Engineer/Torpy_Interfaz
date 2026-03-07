"""Configuración y detección de dependencias para la app."""

from __future__ import annotations

import traceback

ROS_DISPONIBLE = False
INTERFACES_OK = False

rclpy = None
Node = None
MultiThreadedExecutor = None
QoSProfile = None
QoSReliabilityPolicy = None
QoSHistoryPolicy = None
QoSDurabilityPolicy = None
CompressedImage = None
np = None
cv2 = None

Widget_lidar = None
Widgets_cameraCV = None
Modulo_velocidad = None


def cargar_dependencias() -> None:
    """Intenta cargar dependencias opcionales y actualiza flags globales."""
    global ROS_DISPONIBLE, INTERFACES_OK
    global rclpy, Node, MultiThreadedExecutor
    global QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy, QoSDurabilityPolicy
    global CompressedImage, np, cv2
    global Widget_lidar, Widgets_cameraCV, Modulo_velocidad

    try:
        import rclpy as _rclpy
        from rclpy.node import Node as _Node
        from rclpy.executors import MultiThreadedExecutor as _MultiThreadedExecutor
        from rclpy.qos import (
            QoSProfile as _QoSProfile,
            QoSReliabilityPolicy as _QoSReliabilityPolicy,
            QoSHistoryPolicy as _QoSHistoryPolicy,
            QoSDurabilityPolicy as _QoSDurabilityPolicy,
        )
        from sensor_msgs.msg import CompressedImage as _CompressedImage
        import numpy as _np
        import cv2 as _cv2

        rclpy = _rclpy
        Node = _Node
        MultiThreadedExecutor = _MultiThreadedExecutor
        QoSProfile = _QoSProfile
        QoSReliabilityPolicy = _QoSReliabilityPolicy
        QoSHistoryPolicy = _QoSHistoryPolicy
        QoSDurabilityPolicy = _QoSDurabilityPolicy
        CompressedImage = _CompressedImage
        np = _np
        cv2 = _cv2
        ROS_DISPONIBLE = True
        print("✅ ROS2 disponible")
    except ImportError as error:
        print(f"⚠️  ROS2 no disponible: {error}")
        ROS_DISPONIBLE = False

    try:
        from interfaces.widgets import lidar_widget as _Widget_lidar
        from interfaces.widgets import camera_widget as _Widgets_cameraCV
        from interfaces.widgets import modulo_velocidad as _Modulo_velocidad

        Widget_lidar = _Widget_lidar
        Widgets_cameraCV = _Widgets_cameraCV
        Modulo_velocidad = _Modulo_velocidad
        INTERFACES_OK = True
        print("✅ Interfaces importadas correctamente")
    except ImportError as error:
        print(f"⚠️  Error importando interfaces: {error}")
        traceback.print_exc()
        INTERFACES_OK = False
