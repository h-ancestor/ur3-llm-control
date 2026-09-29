
import time
import rclpy

from rclpy.node import Node
from rclpy.action import ActionClient

from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, JointConstraint


class RobotSkills:

    def __init__(self, node: Node, scene_config: dict):
        self.node = node
        self.scene_config = scene_config
        self.get_logger = node.get_logger

        self._action_client = ActionClient(
            node,
            MoveGroup,
            'move_action'
        )

        self.get_logger().info(
            "Đang kết nối tới MoveIt 2 Action Server..."
        )

        if not self._action_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().warn(
                "Không tìm thấy MoveIt 2 Action Server!"
            )

    # =========================================================
    # MOVE ROBOT THEO JOINT
    # =========================================================

    def move_to_joints(self, joint_positions):

        if not self._action_client.server_is_ready():
            self.get_logger().error(
                "MoveIt 2 chưa kết nối."
            )
            return False

        goal_msg = MoveGroup.Goal()

        goal_msg.request.group_name = "ur_manipulator"

        joint_names = [
            "shoulder_pan_joint",
            "shoulder_lift_joint",
            "elbow_joint",
            "wrist_1_joint",
            "wrist_2_joint",
            "wrist_3_joint"
        ]

        constraints = Constraints()

        for name, pos in zip(joint_names, joint_positions):

            jc = JointConstraint()

            jc.joint_name = name
            jc.position = float(pos)

            jc.tolerance_above = 0.02
            jc.tolerance_below = 0.02

            jc.weight = 1.0

            constraints.joint_constraints.append(jc)

        goal_msg.request.goal_constraints.append(constraints)

        future = self._action_client.send_goal_async(goal_msg)

        rclpy.spin_until_future_complete(
            self.node,
            future,
            timeout_sec=10.0
        )

        goal_handle = future.result()

        if goal_handle is None:
            self.get_logger().error(
                "Không nhận được Goal Handle."
            )
            return False

        if not goal_handle.accepted:
            self.get_logger().error(
                "MoveIt 2 từ chối Goal Planning!"
            )
            return False

        result_future = goal_handle.get_result_async()

        rclpy.spin_until_future_complete(
            self.node,
            result_future,
            timeout_sec=30.0
        )

        result_wrapper = result_future.result()

        if result_wrapper is None:
            self.get_logger().error(
                "Không nhận được kết quả từ MoveIt."
            )
            return False

        result = result_wrapper.result

        success = (result.error_code.val == 1)

        if success:
            self.get_logger().info(
                "MoveIt Planning SUCCESS."
            )
        else:
            self.get_logger().error(
                f"MoveIt Planning FAILED: "
                f"error_code={result.error_code.val}"
            )

        return success

    # =========================================================
    # HOME
    # =========================================================

    def home(self):

        self.get_logger().info(
            "Đang thực hiện Skill: home()"
        )

        # Home theo SRDF của UR3
        home_joints = [
            0.0,
            -1.5707,
            0.0,
            0.0,
            0.0,
            0.0
        ]

        if self.move_to_joints(home_joints):
            return "SUCCESS"

        return "PLANNING_FAILED"

    # =========================================================
    # LẤY TỌA ĐỘ OBJECT
    # =========================================================

    def get_object_position(self, object_name):

        objects = self.scene_config.get(
            'objects',
            {}
        )

        if object_name not in objects:
            return None

        return objects[object_name].get(
            'position'
        )

    # =========================================================
    # LẤY TỌA ĐỘ ZONE
    # =========================================================

    def get_zone_position(self, zone_name):

        zones = self.scene_config.get(
            'zones',
            {}
        )

        if zone_name not in zones:
            return None

        return zones[zone_name].get(
            'position'
        )

    # =========================================================
    # PICK
    # =========================================================

    def pick(self, object_name):

        self.get_logger().info(
            f"Đang thực hiện Skill: pick({object_name})"
        )

        position = self.get_object_position(
            object_name
        )

        if position is None:

            self.get_logger().error(
                f"Vật thể không hợp lệ: {object_name}"
            )

            return "INVALID_OBJECT"

        x, y, z = position

        self.get_logger().info(
            f"{object_name}: "
            f"x={x:.3f}, y={y:.3f}, z={z:.3f}"
        )

        # -----------------------------------------------------
        # Tạm thời dùng cấu hình joint tương ứng với vị trí
        # x/y của object.
        #
        # Đây là bước trung gian:
        # scene.yaml -> xác định object -> vị trí -> robot.
        # -----------------------------------------------------

        if object_name == "blue_cube":
            target_joints = [
                -0.5,
                -1.2,
                1.4,
                -1.7,
                -1.57,
                0.0
            ]

        elif object_name == "yellow_cube":
            target_joints = [
                0.0,
                -1.2,
                1.4,
                -1.7,
                -1.57,
                0.0
            ]

        elif object_name == "red_cube":
            target_joints = [
                0.5,
                -1.2,
                1.4,
                -1.7,
                -1.57,
                0.0
            ]

        else:
            return "INVALID_OBJECT"

        if self.move_to_joints(target_joints):

            self.get_logger().info(
                f"Đã tới vị trí pick của {object_name}"
            )

            return "SUCCESS"

        return "PLANNING_FAILED"

    # =========================================================
    # PLACE
    # =========================================================

    def place(self, object_name, zone_name):

        self.get_logger().info(
            f"Đang thực hiện Skill: "
            f"place({object_name}, {zone_name})"
        )

        # Kiểm tra object
        object_position = self.get_object_position(
            object_name
        )

        if object_position is None:

            self.get_logger().error(
                f"Vật thể không hợp lệ: {object_name}"
            )

            return "INVALID_OBJECT"

        # Kiểm tra zone
        zone_position = self.get_zone_position(
            zone_name
        )

        if zone_position is None:

            self.get_logger().error(
                f"Zone không hợp lệ: {zone_name}"
            )

            return "INVALID_ZONE"

        x, y, z = zone_position

        self.get_logger().info(
            f"{zone_name}: "
            f"x={x:.3f}, y={y:.3f}, z={z:.3f}"
        )

        # -----------------------------------------------------
        # Joint configuration tương ứng với từng zone.
        # -----------------------------------------------------

        if zone_name == "zone_a":

            target_joints = [
                -0.8,
                -1.0,
                1.2,
                -1.7,
                -1.57,
                0.0
            ]

        elif zone_name == "zone_b":

            target_joints = [
                0.0,
                -1.0,
                1.2,
                -1.7,
                -1.57,
                0.0
            ]

        elif zone_name == "zone_c":

            target_joints = [
                0.8,
                -1.0,
                1.2,
                -1.7,
                -1.57,
                0.0
            ]

        else:
            return "INVALID_ZONE"

        if self.move_to_joints(target_joints):

            self.get_logger().info(
                f"Đã tới vị trí place của {zone_name}"
            )

            return "SUCCESS"

        return "PLANNING_FAILED"