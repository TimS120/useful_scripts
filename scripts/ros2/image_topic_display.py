#!/usr/bin/env python3
"""ROS 2 node for converting and displaying image messages using OpenCV.

Usage:
    ./image_converter.py
"""

import cv2
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
import rclpy
from rclpy.node import Node


class ImageConverter(Node):
    """
    A ROS 2 node that subscribes to sensor_msgs/Image messages and displays them using OpenCV.
    """

    def __init__(self):
        """
        Initialize the image converter node, subscription, and CvBridge.
        """
        super().__init__("image_converter")
        self.subscription = self.create_subscription(
            Image,
            "/camera/image",
            self.image_callback,
            10
        )
        self.bridge = CvBridge()

    def image_callback(self, msg):
        """
        Callback function to convert ROS2 image message to OpenCV format and display it.

        Args:
            msg (sensor_msgs.msg.Image): The incoming image message.
        """
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        cv2.imshow("Camera Image", cv_image)
        cv2.waitKey(1)


def main(args=None):
    """
    Initialize the ROS 2 system and start the image converter node.
    """
    rclpy.init(args=args)
    node = ImageConverter()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
