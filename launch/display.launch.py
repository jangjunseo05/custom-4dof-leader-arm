"""문제 1-3: 필요한 모든 노드를 한 번에 실행하는 launch 파일.

실행 노드:
    - robot_state_publisher : urdf/ros_arm.urdf 를 읽어 robot_description 파라미터와
      /joint_states 기반 TF를 발행한다.
    - joint_gui              : 문제 1-2에서 작성한 파이썬 UI 노드. 슬라이더로 조인트를
      제어하며 /joint_states 를 발행한다 (joint_state_publisher/_gui 대체).
    - rviz2                  : rviz/ros_arm.rviz 설정으로 로봇을 시각화한다.

사용법:
    ros2 launch ros_arm display.launch.py
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    pkg_share = get_package_share_directory("ros_arm")
    urdf_path = os.path.join(pkg_share, "urdf", "ros_arm.urdf")
    rviz_config_path = os.path.join(pkg_share, "rviz", "ros_arm.rviz")

    with open(urdf_path, "r", encoding="utf-8") as f:
        robot_description = f.read()

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[{"robot_description": robot_description}],
    )

    joint_gui_node = Node(
        package="ros_arm",
        executable="joint_gui",
        name="joint_gui",
        output="screen",
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config_path],
    )

    return LaunchDescription([
        robot_state_publisher_node,
        joint_gui_node,
        rviz_node,
    ])
