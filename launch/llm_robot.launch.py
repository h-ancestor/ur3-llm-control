from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='ur3_llm_control',
            executable='llm_planner',
            name='llm_planner_node',
            output='screen'
        ),
        Node(
            package='ur3_llm_control',
            executable='planning_scene',
            name='planning_scene_node',
            output='screen'
        ),
    ])
