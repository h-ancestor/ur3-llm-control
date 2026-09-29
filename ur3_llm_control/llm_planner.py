import os
import yaml
import json
import threading
import requests

import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory

from ur3_llm_control.task_validator import validate_plan
from ur3_llm_control.skill_executor import execute_plan
from ur3_llm_control.robot_skills import RobotSkills


# ============================================================
# 9ROUTER CONFIG
# ============================================================

API_URL = "http://localhost:20128/v1/chat/completions"

# ============================================================
# >>> DÁN API KEY CỦA BẠN VÀO ĐÂY <<<
# ============================================================

API_KEY = ""

MODEL_NAME = "oc/muse-spark-1.2-contributor-free"
PROVIDER = "opencode"


# ============================================================
# LOAD YAML
# ============================================================

def load_yaml(file_name):

    pkg_path = get_package_share_directory(
        'ur3_llm_control'
    )

    file_path = os.path.join(
        pkg_path,
        'config',
        file_name
    )

    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


# ============================================================
# LLM PLANNER NODE
# ============================================================

class LLMPlannerNode(Node):

    def __init__(self):

        super().__init__(
            'llm_planner_node'
        )

        # Load scene
        self.scene_config = load_yaml(
            'scene.yaml'
        )

        # Load student configuration
        self.student_config = load_yaml(
            'student_config.yaml'
        )

        # Robot
        self.robot = RobotSkills(
            self,
            self.scene_config
        )

        # Terminal interface
        self.ui_thread = threading.Thread(
            target=self.user_interface_loop
        )

        self.ui_thread.daemon = True
        self.ui_thread.start()


    # ========================================================
    # MOCK FALLBACK
    # ========================================================

    def get_llm_plan_mock(self, command):

        """
        MSSV = 41

        41 mod 6 = 5

        Zone A -> Blue
        Zone B -> Yellow
        Zone C -> Red
        """

        cmd = command.lower()

        if any(k in cmd for k in [
            "student id",
            "student",
            "mã số sinh viên",
            "mssv",
            "arrange",
            "arrange all",
            "sắp xếp"
        ]):

            return {
                "plan": [

                    {
                        "skill": "pick",
                        "object": "blue_cube"
                    },

                    {
                        "skill": "place",
                        "object": "blue_cube",
                        "zone": "zone_a"
                    },

                    {
                        "skill": "pick",
                        "object": "yellow_cube"
                    },

                    {
                        "skill": "place",
                        "object": "yellow_cube",
                        "zone": "zone_b"
                    },

                    {
                        "skill": "pick",
                        "object": "red_cube"
                    },

                    {
                        "skill": "place",
                        "object": "red_cube",
                        "zone": "zone_c"
                    },

                    {
                        "skill": "home"
                    }

                ]
            }

        return {
            "plan": []
        }


    # ========================================================
    # CALL LLM THROUGH 9ROUTER
    # ========================================================

    def get_llm_plan(self, command):

        objects_list = list(
            self.scene_config
            .get('objects', {})
            .keys()
        )

        zones_list = list(
            self.scene_config
            .get('zones', {})
            .keys()
        )

        mapping = self.student_config.get(
            'zone_mapping',
            {}
        )

        mapping_str = json.dumps(
            mapping,
            ensure_ascii=False
        )


        # ----------------------------------------------------
        # SYSTEM PROMPT
        # ----------------------------------------------------

        system_prompt = f"""

You are a task planner for a UR3 robot arm.

Your ONLY job is to convert natural language
into a structured robot skill plan.

You MUST NOT generate:

- joint angles
- joint trajectories
- Cartesian trajectories
- velocity commands
- motor commands
- ROS commands

Available skills:

home()
pick(object)
place(object, zone)

Available objects:

{objects_list}

Available zones:

{zones_list}

Student zone mapping:

{mapping_str}


RULES:

1. Return ONLY valid JSON.

2. The JSON must have this structure:

{{
  "plan": [
    {{
      "skill": "pick",
      "object": "object_name"
    }},
    {{
      "skill": "place",
      "object": "object_name",
      "zone": "zone_name"
    }},
    {{
      "skill": "home"
    }}
  ]
}}

3. Only use:

pick
place
home

4. Only use objects from the available objects list.

5. Only use zones from the available zones list.

6. For pick and place:

pick the object first,
then place the same object.

7. If the user asks to arrange objects
according to student ID, use the student zone mapping.

8. Do not provide explanations.

9. Do not use Markdown.

10. Return only the JSON object.

"""


        # ----------------------------------------------------
        # CHECK API KEY
        # ----------------------------------------------------

        if (
            not API_KEY
            or API_KEY == "DAN_API_KEY_CUA_BAN_VAO_DAY"
        ):

            self.get_logger().error(
                "Bạn chưa nhập API key 9Router!"
            )

            return self.get_llm_plan_mock(
                command
            )


        # ----------------------------------------------------
        # HEADERS
        # ----------------------------------------------------

        headers = {

            "Content-Type":
                "application/json",

            "Authorization":
                f"Bearer {API_KEY}",

            "x-router-provider":
                PROVIDER
        }


        # ----------------------------------------------------
        # REQUEST
        # ----------------------------------------------------

        payload = {

            "model":
                MODEL_NAME,

            "messages": [

                {
                    "role":
                        "system",

                    "content":
                        system_prompt
                },

                {
                    "role":
                        "user",

                    "content":
                        command
                }

            ],

            "temperature":
                0.0
        }


        try:

            self.get_logger().info(
                f"Gọi 9Router: {MODEL_NAME}"
            )


            response = requests.post(

                API_URL,

                headers=headers,

                json=payload,

                timeout=30
            )


            # ------------------------------------------------
            # HTTP ERROR
            # ------------------------------------------------

            if response.status_code != 200:

                self.get_logger().error(

                    f"9Router HTTP "
                    f"{response.status_code}: "
                    f"{response.text}"
                )

                self.get_logger().warn(
                    "Chuyển sang Local Planner..."
                )

                return self.get_llm_plan_mock(
                    command
                )


            # ------------------------------------------------
            # RESPONSE JSON
            # ------------------------------------------------

            response_json = response.json()


            if "choices" not in response_json:

                self.get_logger().error(
                    f"Response không hợp lệ: "
                    f"{response_json}"
                )

                return self.get_llm_plan_mock(
                    command
                )


            content = (
                response_json["choices"][0]
                ["message"]["content"]
                .strip()
            )


            self.get_logger().info(
                f"LLM response: {content}"
            )


            # ------------------------------------------------
            # REMOVE MARKDOWN
            # ------------------------------------------------

            if content.startswith("```"):

                lines = content.splitlines()

                if len(lines) > 0:
                    lines = lines[1:]

                if (
                    len(lines) > 0
                    and lines[-1].strip() == "```"
                ):
                    lines = lines[:-1]

                content = "\n".join(
                    lines
                ).strip()


            # ------------------------------------------------
            # JSON PARSE
            # ------------------------------------------------

            plan_json = json.loads(
                content
            )

            return plan_json


        except requests.exceptions.ConnectionError:

            self.get_logger().error(
                "Không kết nối được tới 9Router!"
            )

            self.get_logger().warn(
                "Kiểm tra 9Router tại "
                "localhost:20128"
            )

            return self.get_llm_plan_mock(
                command
            )


        except requests.exceptions.Timeout:

            self.get_logger().error(
                "9Router timeout!"
            )

            return self.get_llm_plan_mock(
                command
            )


        except json.JSONDecodeError as e:

            self.get_logger().error(
                f"LLM trả JSON lỗi: {e}"
            )

            return self.get_llm_plan_mock(
                command
            )


        except Exception as e:

            self.get_logger().error(
                f"Lỗi gọi LLM: {e}"
            )

            return self.get_llm_plan_mock(
                command
            )


    # ========================================================
    # USER INTERFACE
    # ========================================================

    def user_interface_loop(self):

        while rclpy.ok():

            try:

                command = input(
                    "\nUSER COMMAND:\n"
                )


                if not command.strip():
                    continue


                # ------------------------------------------------
                # GET PLAN
                # ------------------------------------------------

                plan_json = self.get_llm_plan(
                    command
                )


                # ------------------------------------------------
                # PRINT PLAN
                # ------------------------------------------------

                print(
                    "\nLLM PLAN:"
                )

                print(
                    json.dumps(
                        plan_json,
                        indent=2,
                        ensure_ascii=False
                    )
                )


                # ------------------------------------------------
                # VALIDATE
                # ------------------------------------------------

                is_valid, msg = validate_plan(
                    plan_json,
                    self.scene_config
                )


                if not is_valid:

                    print(
                        f"\n[ERROR] "
                        f"Kế hoạch không hợp lệ: "
                        f"{msg}"
                    )

                    continue


                # ------------------------------------------------
                # EXECUTE
                # ------------------------------------------------

                execute_plan(
                    plan_json,
                    self.robot
                )


            except KeyboardInterrupt:

                print(
                    "\nThoát chương trình."
                )

                break


            except Exception as e:

                print(
                    f"\nLỗi thực thi: {e}"
                )


# ============================================================
# MAIN
# ============================================================

def main(args=None):

    rclpy.init(
        args=args
    )

    node = LLMPlannerNode()


    try:

        rclpy.spin(
            node
        )


    except KeyboardInterrupt:

        pass


    finally:

        node.destroy_node()

        rclpy.shutdown()


# ============================================================
# RUN
# ============================================================

if __name__ == '__main__':

    main()