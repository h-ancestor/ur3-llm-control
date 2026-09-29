import rclpy
from rclpy.node import Node

from moveit_msgs.msg import CollisionObject
from shape_msgs.msg import SolidPrimitive
from geometry_msgs.msg import Pose


class PlanningSceneManager(Node):

    def __init__(self):
        super().__init__('planning_scene_manager')

        self.publisher = self.create_publisher(
            CollisionObject,
            '/collision_object',
            10
        )

        self.timer = self.create_timer(2.0, self.publish_scene)
        self.published = False

    def add_box(self, name, size, position):
        obj = CollisionObject()
        obj.header.frame_id = "base_link"
        obj.id = name

        primitive = SolidPrimitive()
        primitive.type = SolidPrimitive.BOX
        primitive.dimensions = [
            float(size[0]),
            float(size[1]),
            float(size[2])
        ]

        pose = Pose()
        pose.position.x = float(position[0])
        pose.position.y = float(position[1])
        pose.position.z = float(position[2])
        pose.orientation.w = 1.0

        obj.primitives.append(primitive)
        obj.primitive_poses.append(pose)

        obj.operation = CollisionObject.ADD

        self.publisher.publish(obj)

    def publish_scene(self):

        if self.published:
            return

        # Bàn
        self.add_box(
            "table",
            [0.8, 0.6, 0.1],
            [0.55, 0.0, -0.05]
        )

        # Các hộp
        self.add_box(
            "blue_cube",
            [0.1, 0.1, 0.1],
            [0.35, -0.20, 0.05]
        )

        self.add_box(
            "yellow_cube",
            [0.1, 0.1, 0.1],
            [0.35, 0.00, 0.05]
        )

        self.add_box(
            "red_cube",
            [0.1, 0.1, 0.1],
            [0.35, 0.20, 0.05]
        )

        self.published = True

        self.get_logger().info(
            "Planning Scene: table + 3 cubes added."
        )


def main(args=None):
    rclpy.init(args=args)

    node = PlanningSceneManager()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
