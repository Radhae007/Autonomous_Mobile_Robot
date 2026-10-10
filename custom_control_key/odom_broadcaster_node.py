#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
import tf2_ros

class OdomStamperNode(Node):
    def __init__(self):
        super().__init__('odom_stamper_node')
        
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)
        
        self.create_subscription(Odometry, '/odom_esp', self.odom_callback, 10)
        
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)

    def odom_callback(self, msg):
        # Stamp with Pi's clock right as message arrives
        now = self.get_clock().now().to_msg()
        
        # Forward everything from ESP32, just replace the stamp
        msg.header.stamp = now
        self.odom_pub.publish(msg)
        
        # Broadcast TF with same stamp
        t = TransformStamped()
        t.header.stamp = now
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_footprint'
        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.translation.z = 0.0
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = msg.pose.pose.orientation.z
        t.transform.rotation.w = msg.pose.pose.orientation.w
        self.tf_broadcaster.sendTransform(t)

def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(OdomStamperNode())
    rclpy.shutdown()

if __name__ == '__main__':
    main()
