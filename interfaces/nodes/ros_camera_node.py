import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import cv2
from cv_bridge import CvBridge


class ROSCameraNode(Node):
    def __init__(self):
        super().__init__("ros_camera_node")
        self.bridge = CvBridge()
        self.last_frame = None

        # Suscriptor al tópico de la cámara
        self.create_subscription(
            Image,
            "/camera/image_raw",
            self.callback_imagen,
            10
        )

    def callback_imagen(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            self.last_frame = frame
        except Exception as e:
            self.get_logger().error(f"Error decodificando frame: {e}")
