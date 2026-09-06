"""4축 로봇암(ros_arm/jdcobot100)의 조인트를 Tkinter UI로 직접 제어하는 노드.

joint_state_publisher_gui 대신 직접 작성한 파이썬 UI로 각 조인트 각도를 슬라이더로
조절하면, 주기적으로 sensor_msgs/JointState 메시지를 /joint_states 토픽에 발행한다.
robot_state_publisher가 이를 구독해 각 링크의 TF를 갱신하므로 RViz에서 로봇암이
실시간으로 움직이는 것을 확인할 수 있다.

사용법 (직접 실행):
    python3 ros_arm/joint_gui.py
launch 파일(launch/display.launch.py)을 통해 다른 노드와 함께 실행하는 것을 권장.
"""

import math
import tkinter as tk

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

# urdf/ros_arm.urdf 에 정의된 revolute 조인트 이름과 한계값 (모두 -pi ~ pi)
JOINTS = [
    ("base_shoulder", -math.pi, math.pi),
    ("shoulder_arm1", -math.pi, math.pi),
    ("arm1_arm2", -math.pi, math.pi),
    ("arn2_end_arm", -math.pi, math.pi),
]

PUBLISH_PERIOD_MS = 50  # 20 Hz


class JointGui(Node):
    def __init__(self):
        super().__init__("joint_gui")
        self.publisher_ = self.create_publisher(JointState, "joint_states", 10)
        self.positions = {name: 0.0 for name, _, _ in JOINTS}

    def publish_state(self) -> None:
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = [name for name, _, _ in JOINTS]
        msg.position = [self.positions[name] for name in msg.name]
        self.publisher_.publish(msg)


def build_ui(node: JointGui, root: tk.Tk) -> None:
    root.title("ros_arm Joint Controller")

    sliders = []

    def make_row(joint_name: str, lower: float, upper: float, row: int) -> None:
        tk.Label(root, text=joint_name, width=16, anchor="w").grid(
            row=row, column=0, padx=8, pady=4, sticky="w"
        )
        value_label = tk.Label(root, text="0.000 rad", width=10)
        value_label.grid(row=row, column=2, padx=8)

        def on_change(value: str) -> None:
            angle = float(value)
            node.positions[joint_name] = angle
            value_label.config(text=f"{angle:.3f} rad")

        slider = tk.Scale(
            root,
            from_=lower,
            to=upper,
            resolution=0.01,
            orient=tk.HORIZONTAL,
            length=320,
            showvalue=False,
            command=on_change,
        )
        slider.set(0.0)
        slider.grid(row=row, column=1, padx=8, pady=4)
        sliders.append(slider)

    for i, (name, lower, upper) in enumerate(JOINTS):
        make_row(name, lower, upper, i)

    def reset_all() -> None:
        for slider in sliders:
            slider.set(0.0)

    tk.Button(root, text="Zero All", command=reset_all).grid(
        row=len(JOINTS), column=0, columnspan=3, pady=10
    )

    def tick() -> None:
        rclpy.spin_once(node, timeout_sec=0)
        node.publish_state()
        root.after(PUBLISH_PERIOD_MS, tick)

    root.after(PUBLISH_PERIOD_MS, tick)


def main() -> None:
    rclpy.init()
    node = JointGui()

    root = tk.Tk()
    build_ui(node, root)

    try:
        root.mainloop()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
