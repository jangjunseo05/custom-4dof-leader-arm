"""실물 소형 로봇암(가변저항 엔코더)으로 MuJoCo 가상 로봇암을 텔레오퍼레이션한다.

사전 준비:
    1. Arduino에 arduino/teleop_encoder/teleop_encoder.ino 업로드
    2. 아래 SERIAL_PORT를 실제 포트로 수정 (모르면 --list-ports 로 확인)
    3. 반드시 --calibrate 로 각 관절의 ADC min/max 값을 먼저 측정해서
       CALIBRATION 딕셔너리를 실제 값으로 채워넣을 것 (기본값은 추정치일 뿐 부정확함)

사용법:
    python teleop.py --list-ports          # 사용 가능한 시리얼 포트 확인
    python teleop.py --port COM3 --calibrate   # 캘리브레이션 모드 (raw ADC 값만 출력)
    python teleop.py --port COM3               # 실제 텔레오퍼레이션 실행
"""

import argparse
import math
import sys
import time

import mujoco
import mujoco.viewer
import serial
import serial.tools.list_ports

MODEL_PATH = "scene.xml"
BAUD_RATE = 115200

# 관절 이름 순서는 Arduino 스케치의 A0~A3 배선 순서와 반드시 일치해야 한다.
JOINT_NAMES = ["base_shoulder", "shoulder_arm1", "arm1_arm2", "arn2_end_arm"]

# --calibrate 로 측정한 실제 min/max ADC 값으로 반드시 교체할 것.
# adc_min/adc_max: 관절을 물리적 최소~최대로 움직였을 때 읽힌 raw ADC 값 (0~1023)
# angle_min/angle_max: 그 ADC 값에 대응하는 라디안 각도 (URDF 조인트 range 참고, 기본 -pi~pi)
CALIBRATION = {
    "base_shoulder":  {"adc_min": 0,   "adc_max": 672, "angle_min": -2.3562, "angle_max": 2.3562},
    "shoulder_arm1":  {"adc_min": 0,   "adc_max": 666, "angle_min": -1.5708, "angle_max": 1.5708},
    "arm1_arm2":      {"adc_min": 0,   "adc_max": 672, "angle_min": -2.0944, "angle_max": 2.0944},
    "arn2_end_arm":   {"adc_min": 0,   "adc_max": 663, "angle_min": -3.14159, "angle_max": 3.14159},
}

SMOOTHING_ALPHA = 0.3  # 0(느림/부드러움) ~ 1(빠름/노이즈에 민감)


def list_ports() -> None:
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("연결된 시리얼 포트가 없습니다. Arduino가 USB로 연결되어 있는지 확인하세요.")
        return
    for p in ports:
        print(f"{p.device}\t{p.description}")


def adc_to_angle(joint: str, adc_value: float) -> float:
    cal = CALIBRATION[joint]
    adc_span = cal["adc_max"] - cal["adc_min"]
    if adc_span == 0:
        return cal["angle_min"]
    t = (adc_value - cal["adc_min"]) / adc_span
    t = max(0.0, min(1.0, t))  # clip
    return cal["angle_min"] + t * (cal["angle_max"] - cal["angle_min"])


def run_calibration(ser: serial.Serial) -> None:
    print("캘리브레이션 모드: 각 관절을 손으로 최소~최대까지 천천히 왕복하며 움직이세요.")
    print("min/max는 지금까지 관찰된 raw ADC 극값을 자동으로 추적해 실시간으로 갱신됩니다.")
    print("angle(참고용)은 현재 CALIBRATION 딕셔너리 값 기준 추정치이니, 아직 정확하지 않아도 됩니다.")
    print("  -> 관절을 원하는 방향으로 움직였을 때 angle이 그 방향으로 커지는지/줄어드는지만 확인하세요.")
    print("     반대로 움직이면 그 관절의 adc_min/adc_max를 서로 바꿔 넣어야 합니다.")
    print("Ctrl+C 로 종료하면 지금까지 측정된 min/max 값을 정리해서 보여줍니다.\n")

    running_min = {name: None for name in JOINT_NAMES}
    running_max = {name: None for name in JOINT_NAMES}

    try:
        while True:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue

            parts = line.split(",")
            if len(parts) != len(JOINT_NAMES):
                continue

            try:
                raw_values = [float(p) for p in parts]
            except ValueError:
                continue

            fields = []
            for name, raw in zip(JOINT_NAMES, raw_values):
                if running_min[name] is None or raw < running_min[name]:
                    running_min[name] = raw
                if running_max[name] is None or raw > running_max[name]:
                    running_max[name] = raw
                angle_deg = math.degrees(adc_to_angle(name, raw))
                fields.append(
                    f"{name}: raw={raw:4.0f} min={running_min[name]:4.0f} "
                    f"max={running_max[name]:4.0f} angle~={angle_deg:6.1f}deg"
                )
            print(" | ".join(fields) + "   ", end="\r", flush=True)
    except KeyboardInterrupt:
        print("\n\n측정된 min/max (아래 값을 CALIBRATION 딕셔너리의 adc_min/adc_max에 채워넣으세요):\n")
        for name in JOINT_NAMES:
            lo = running_min[name]
            hi = running_max[name]
            if lo is None or hi is None:
                print(f'    "{name}": 데이터 없음 (해당 관절을 움직이지 않았습니다)')
            else:
                print(f'    "{name}": adc_min={lo:.0f}, adc_max={hi:.0f}')


def run_teleop(ser: serial.Serial) -> None:
    model = mujoco.MjModel.from_xml_path(MODEL_PATH)
    data = mujoco.MjData(model)

    joint_qpos_idx = []
    for name in JOINT_NAMES:
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
        if jid == -1:
            raise ValueError(f"모델에 '{name}' 조인트가 없습니다.")
        joint_qpos_idx.append(model.jnt_qposadr[jid])

    smoothed = [0.0] * len(JOINT_NAMES)
    initialized = False

    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue

            parts = line.split(",")
            if len(parts) != len(JOINT_NAMES):
                continue  # 깨진 프레임 무시

            try:
                raw_values = [float(p) for p in parts]
            except ValueError:
                continue

            for i, (name, raw) in enumerate(zip(JOINT_NAMES, raw_values)):
                angle = adc_to_angle(name, raw)
                if not initialized:
                    smoothed[i] = angle
                else:
                    smoothed[i] = (SMOOTHING_ALPHA * angle
                                    + (1 - SMOOTHING_ALPHA) * smoothed[i])
                data.qpos[joint_qpos_idx[i]] = smoothed[i]

            initialized = True

            mujoco.mj_forward(model, data)
            viewer.sync()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=str, default=None, help="Arduino 시리얼 포트 (예: COM3)")
    parser.add_argument("--list-ports", action="store_true", help="사용 가능한 시리얼 포트 목록 출력")
    parser.add_argument("--calibrate", action="store_true", help="캘리브레이션 모드로 실행")
    args = parser.parse_args()

    if args.list_ports:
        list_ports()
        return

    if not args.port:
        print("에러: --port 를 지정하세요. 포트를 모르면 --list-ports 로 확인하세요.", file=sys.stderr)
        sys.exit(1)

    ser = serial.Serial(args.port, BAUD_RATE, timeout=1)
    time.sleep(2)  # Arduino 리셋 후 부팅 대기

    if args.calibrate:
        run_calibration(ser)
    else:
        run_teleop(ser)


if __name__ == "__main__":
    main()
