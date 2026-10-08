# Custom 4-DOF Leader Arm — Real-to-Sim Teleoperation

A low-cost, 4-DOF master ("leader") robot arm built from repurposed SG90 micro servos, whose internal potentiometers are tapped as manual joint-angle encoders to drive a MuJoCo digital twin in real time. The repository also includes a ROS 2 URDF/RViz visualization package and an early-stage scaffold for a LeRobot-style dataset pipeline.

## Overview

The arm's CAD model (`jdcobot100`) was designed in Onshape and exported to URDF via `onshape-to-robot`. It has 4 revolute joints — `base_shoulder`, `shoulder_arm1`, `arm1_arm2`, `arn2_end_arm` — each with a ±180° (±π rad) range, actuated by SG90 micro servos. The same URDF is wrapped into a MuJoCo scene (`scene.xml`, `ros_arm.xml`) using the meshes in `meshes/`, so the identical kinematic structure can be visualized either in ROS 2/RViz or simulated in MuJoCo.

Instead of buying external rotary encoders, the four SG90 servos were disassembled and jumper wires were soldered directly onto their internal potentiometer wipers, letting the arm's own servo potentiometers double as a cheap joint-angle sensor. This turns the physical arm into a passive "leader" device: a human moves the joints by hand, and the raw potentiometer voltage is read back as the joint angle.

## Core Work

- **Servo-as-encoder hardware hack** — `arduino/teleop_encoder/teleop_encoder.ino` reads the 4 potentiometer taps (`A0`–`A3`) at ~50 Hz (8-sample averaging) and streams them over serial as `a0,a1,a2,a3\n` raw ADC values (0–1023).
- **Homing & calibration tooling** — `arduino/motor_homing/motor_homing.ino` plus the `home_motors.py` host CLI drive each joint to a known home pose over serial (`H`ome / `D`etach / `A`ttach / `S`et-joint commands), then record the home angle and baseline ADC reading to `motor_home_calibration.json`.
- **Per-joint ADC calibration** — `teleop.py --calibrate` tracks the running min/max raw ADC value as each joint is swept by hand, producing the `adc_min`/`adc_max` values used to linearly map raw ADC to a joint angle in radians (`CALIBRATION` dict in `teleop.py`).
- **Real-to-sim teleoperation** — `teleop.py` streams live ADC readings, converts them to joint angles via the calibration table, applies exponential smoothing (`SMOOTHING_ALPHA = 0.3`) to reduce potentiometer noise, and writes the result directly into `qpos` of a MuJoCo model loaded from `scene.xml`, rendering the live-updated digital twin in `mujoco.viewer`.
- **ROS 2 visualization package (`ros_arm`)** — a `URDF`-based robot description (`urdf/ros_arm.urdf`) with a custom Tkinter joint-angle GUI (`ros_arm/joint_gui.py`) that publishes `sensor_msgs/JointState` in place of `joint_state_publisher_gui`, brought up together with `robot_state_publisher` and RViz2 via `launch/display.launch.py`.
- **LeRobot dataset pipeline scaffold (`lerobot-project/`)** — directory layout and source stubs (`config_loader`, `data_loader`, `synchronizer`, `episode_builder`, `exporter`, `validator`, `stats`) laid out for a future LeRobot-format dataset recording pipeline (ROS topics → raw data → episodes → export). This part is early-stage scaffolding: the `raw_data/`, `datasets/`, `notebooks/`, `preprocess/`, and `rosbag/` folders are currently empty.

## Usage

**MuJoCo real-to-sim teleoperation**
```bash
python teleop.py --list-ports                # find the Arduino serial port
python teleop.py --port COM3 --calibrate      # sweep each joint by hand to measure ADC min/max
python teleop.py --port COM3                  # stream live joint angles into the MuJoCo viewer
```

**View the arm in MuJoCo without hardware**
```bash
python view_robot.py
```

**Servo homing / calibration**
```bash
python home_motors.py --list-ports
python home_motors.py --port COM3             # interactive home / detach / attach / set / save
```

**ROS 2 URDF visualization**
```bash
ros2 launch ros_arm display.launch.py         # robot_state_publisher + joint_gui + RViz2
```

## Tech Stack

- **Hardware**: SG90 micro servos (repurposed as potentiometer encoders), Arduino (Uno/Nano), 3D-printed structure
- **Firmware**: Arduino C++ (`Servo` library, analog sampling/averaging)
- **Simulation**: MuJoCo, `mujoco.viewer`
- **Robotics middleware**: ROS 2 (`rclpy`, `robot_state_publisher`, `RViz2`, `sensor_msgs`), URDF
- **Host software**: Python (`pyserial`, `mujoco`, `tkinter`)
- **CAD / modeling**: Onshape, `onshape-to-robot` (URDF + mesh export)
