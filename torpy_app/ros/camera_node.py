"""Nodo de cámara y fallback cuando ROS2 no está disponible."""

from __future__ import annotations

from torpy_app import config


if config.ROS_DISPONIBLE:
    class CameraSubscriberNode(config.Node):
        """Nodo ROS2 para recibir imágenes comprimidas."""

        def __init__(self):
            super().__init__("camera_gui_node")
            self.last_frame = None
            self.frame_count = 0

            qos_profile = config.QoSProfile(
                reliability=config.QoSReliabilityPolicy.BEST_EFFORT,
                durability=config.QoSDurabilityPolicy.VOLATILE,
                history=config.QoSHistoryPolicy.KEEP_LAST,
                depth=1,
            )

            self.subscription = self.create_subscription(
                config.CompressedImage,
                "/image_raw/compressed",
                self.callback,
                qos_profile,
            )

            self.get_logger().info("✅ CameraNode: /image_raw/compressed")

        def callback(self, msg):
            try:
                np_arr = config.np.frombuffer(msg.data, config.np.uint8)
                frame = config.cv2.imdecode(np_arr, config.cv2.IMREAD_COLOR)

                if frame is not None:
                    self.last_frame = config.cv2.cvtColor(frame, config.cv2.COLOR_BGR2RGB)
                    self.frame_count += 1
                    if self.frame_count % 30 == 0:
                        self.get_logger().info(f"📹 Frames: {self.frame_count}")
            except Exception as error:
                self.get_logger().error(f"Error: {error}")
else:
    class CameraSubscriberNode:
        """Implementación mínima cuando ROS2 no está disponible."""

        def __init__(self):
            self.last_frame = None
            print("⚠️  CameraNode dummy (ROS2 no disponible)")

        def destroy_node(self):
            return None

        def get_name(self):
            return "camera_node_dummy"
