"""jdcobot100 (ros_arm) 로봇을 MuJoCo 인터랙티브 뷰어로 띄운다.

사용법:
    python view_robot.py
"""

import mujoco
import mujoco.viewer

MODEL_PATH = "scene.xml"


def main() -> None:
    model = mujoco.MjModel.from_xml_path(MODEL_PATH)
    data = mujoco.MjData(model)

    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            mujoco.mj_step(model, data)
            viewer.sync()


if __name__ == "__main__":
    main()
