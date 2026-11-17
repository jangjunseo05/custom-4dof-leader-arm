# 커스텀 4축 리더암 — Real-to-Sim 텔레오퍼레이션

[English](README.en.md)

SG90 마이크로 서보를 개조해 만든 저비용 4자유도 마스터("리더") 로봇팔입니다. 서보 내부의 포텐셔미터를 수동 관절 각도 엔코더로 끌어내 MuJoCo 디지털 트윈을 실시간으로 움직입니다. 이 저장소에는 ROS 2 URDF/RViz 시각화 패키지와, LeRobot 형식 데이터셋 파이프라인의 초기 골격도 함께 들어 있습니다.

## 개요

팔의 부품은 Fusion에서 설계해 3D 프린팅했고, 로봇 모델(`jdcobot100`)은 Onshape에서 `onshape-to-robot`으로 URDF로 내보냈습니다. 회전 관절 4개 — `base_shoulder`, `shoulder_arm1`, `arm1_arm2`, `arn2_end_arm` — 로 이루어져 있고, 각 관절의 범위는 ±180°(±π rad)이며 SG90 마이크로 서보로 구동됩니다. 같은 URDF를 `meshes/`의 메시와 함께 MuJoCo 장면(`scene.xml`, `ros_arm.xml`)으로 감싸, 동일한 기구학 구조를 ROS 2/RViz에서 시각화하거나 MuJoCo에서 시뮬레이션할 수 있습니다.

외장 로터리 엔코더를 사는 대신 SG90 서보 4개를 분해해 내부 포텐셔미터 와이퍼에 점퍼선을 직접 납땜했고, 덕분에 팔에 달린 서보 포텐셔미터를 저렴한 관절 각도 센서로 함께 쓸 수 있게 되었습니다. 이렇게 실물 팔은 수동형 "리더" 장치가 됩니다. 사람이 손으로 관절을 움직이면, 포텐셔미터 전압 원시값을 관절 각도로 읽어 들입니다.

## 핵심 작업

- **서보를 엔코더로 쓰는 하드웨어 개조** — `arduino/teleop_encoder/teleop_encoder.ino`가 포텐셔미터 탭 4개(`A0`–`A3`)를 약 50 Hz(8샘플 평균)로 읽어, ADC 원시값(0–1023)을 `a0,a1,a2,a3\n` 형식으로 시리얼 전송합니다.
- **호밍·캘리브레이션 도구** — `arduino/motor_homing/motor_homing.ino`와 호스트 CLI `home_motors.py`가 시리얼 명령(`H`ome / `D`etach / `A`ttach / `S`et-joint)으로 각 관절을 정해진 홈 자세로 보낸 뒤, 홈 각도와 기준 ADC 값을 `motor_home_calibration.json`에 기록합니다.
- **관절별 ADC 캘리브레이션** — `teleop.py --calibrate`는 각 관절을 손으로 끝에서 끝까지 움직이는 동안 ADC 원시값의 최솟값·최댓값을 추적해, ADC 원시값을 라디안 단위 관절 각도로 선형 변환하는 데 쓰는 `adc_min`/`adc_max` 값을 만듭니다(`teleop.py`의 `CALIBRATION` 딕셔너리).
- **Real-to-sim 텔레오퍼레이션** — `teleop.py`가 실시간 ADC 값을 받아 캘리브레이션 표로 관절 각도로 바꾸고, 포텐셔미터 잡음을 줄이기 위해 지수 평활(`SMOOTHING_ALPHA = 0.3`)을 적용한 뒤, `scene.xml`에서 불러온 MuJoCo 모델의 `qpos`에 바로 써 넣어 `mujoco.viewer`에서 디지털 트윈을 실시간으로 렌더링합니다.
- **ROS 2 시각화 패키지(`ros_arm`)** — `URDF` 기반 로봇 description(`urdf/ros_arm.urdf`)과, `joint_state_publisher_gui` 대신 `sensor_msgs/JointState`를 발행하는 자체 Tkinter 관절 각도 GUI(`ros_arm/joint_gui.py`)로 구성되며, `launch/display.launch.py`로 `robot_state_publisher`, RViz2와 함께 실행됩니다.
- **LeRobot 데이터셋 파이프라인 골격(`lerobot-project/`)** — 앞으로 만들 LeRobot 형식 데이터셋 녹화 파이프라인(ROS 토픽 → 원시 데이터 → 에피소드 → 내보내기)을 위한 디렉터리 구조와 소스 스텁(`config_loader`, `data_loader`, `synchronizer`, `episode_builder`, `exporter`, `validator`, `stats`)입니다. 이 부분은 초기 골격 단계로, `raw_data/`, `datasets/`, `notebooks/`, `preprocess/`, `rosbag/` 폴더는 현재 비어 있습니다.

## 사용법

**MuJoCo real-to-sim 텔레오퍼레이션**
```bash
python teleop.py --list-ports                # 아두이노 시리얼 포트 찾기
python teleop.py --port COM3 --calibrate      # 각 관절을 손으로 끝까지 움직여 ADC 최솟값/최댓값 측정
python teleop.py --port COM3                  # 실시간 관절 각도를 MuJoCo 뷰어로 전송
```

**하드웨어 없이 MuJoCo에서 팔 보기**
```bash
python view_robot.py
```

**서보 호밍 / 캘리브레이션**
```bash
python home_motors.py --list-ports
python home_motors.py --port COM3             # 대화형 home / detach / attach / set / save
```

**ROS 2 URDF 시각화**
```bash
ros2 launch ros_arm display.launch.py         # robot_state_publisher + joint_gui + RViz2
```

## 기술 스택

- **하드웨어**: SG90 마이크로 서보(포텐셔미터 엔코더로 개조), Arduino(Uno/Nano), 3D 프린팅 구조물
- **펌웨어**: Arduino C++(`Servo` 라이브러리, 아날로그 샘플링/평균)
- **시뮬레이션**: MuJoCo, `mujoco.viewer`
- **로보틱스 미들웨어**: ROS 2(`rclpy`, `robot_state_publisher`, `RViz2`, `sensor_msgs`), URDF
- **호스트 소프트웨어**: Python(`pyserial`, `mujoco`, `tkinter`)
- **CAD / 모델링**: Fusion(부품 설계), Onshape + `onshape-to-robot`(URDF + 메시 내보내기)
