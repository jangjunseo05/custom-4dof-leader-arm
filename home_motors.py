"""4축 SG90 로봇암의 모터 원점(Home)을 맞추기 위한 호스트 스크립트.

사전 준비:
    1. Arduino에 arduino/motor_homing/motor_homing.ino 업로드
       (스케치 상단의 SERVO_PINS가 실제 배선과 일치하는지 반드시 확인)
    2. 아래 명령 실행 시 --port 를 실제 포트로 지정 (모르면 --list-ports 로 확인)

사용법:
    python home_motors.py --list-ports
    python home_motors.py --port COM3
"""

import argparse
import json
import sys
import time

import serial
import serial.tools.list_ports

BAUD_RATE = 115200
JOINT_NAMES = ["base_shoulder", "shoulder_arm1", "arm1_arm2", "arn2_end_arm"]
HOME_ANGLE_DEFAULT = 90
OUTPUT_FILE = "motor_home_calibration.json"


def list_ports() -> None:
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("연결된 시리얼 포트가 없습니다. Arduino가 USB로 연결되어 있는지 확인하세요.")
        return
    for p in ports:
        print(f"{p.device}\t{p.description}")


def read_latest_adc(ser: serial.Serial, timeout: float = 0.5):
    """짧은 시간 동안 버퍼에 쌓인 줄 중 가장 최근 값을 읽어 반환한다."""
    deadline = time.time() + timeout
    latest = None
    while time.time() < deadline:
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        if not line:
            continue
        parts = line.split(",")
        if len(parts) != len(JOINT_NAMES):
            continue
        try:
            latest = [float(p) for p in parts]
        except ValueError:
            continue
    return latest


def print_status(ser: serial.Serial) -> None:
    values = read_latest_adc(ser)
    if values is None:
        print("  (ADC 값을 읽지 못했습니다. 배선/포트를 확인하세요.)")
        return
    fields = [f"{name}={v:.0f}" for name, v in zip(JOINT_NAMES, values)]
    print("  " + " | ".join(fields))


def send(ser: serial.Serial, line: str) -> None:
    ser.write((line + "\n").encode("utf-8"))


def cmd_home(ser: serial.Serial, angles: dict) -> None:
    for name in JOINT_NAMES:
        angles[name] = HOME_ANGLE_DEFAULT
    send(ser, "H")
    time.sleep(0.5)
    print("모든 관절을 HOME 각도로 이동했습니다. 실제 팔 자세를 확인하세요.")
    print_status(ser)


def cmd_set(ser: serial.Serial, angles: dict, joint: str, angle: int) -> None:
    if joint not in JOINT_NAMES:
        print(f"알 수 없는 관절명입니다: {joint} (가능한 값: {', '.join(JOINT_NAMES)})")
        return
    idx = JOINT_NAMES.index(joint)
    angle = max(0, min(180, angle))
    angles[joint] = angle
    send(ser, f"S,{idx},{angle}")
    time.sleep(0.2)
    print(f"{joint} -> {angle}도")
    print_status(ser)


def cmd_save(angles: dict, adc_snapshot) -> None:
    data = {
        "servo_home_angle_deg": angles,
        "adc_at_home": dict(zip(JOINT_NAMES, adc_snapshot)) if adc_snapshot else None,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"저장 완료: {OUTPUT_FILE}")


def interactive_loop(ser: serial.Serial) -> None:
    angles = {name: HOME_ANGLE_DEFAULT for name in JOINT_NAMES}

    print("\n명령어:")
    print("  home                  - 모든 관절을 원점(90도)으로 이동")
    print("  detach                - 모든 서보 토크 해제 (손으로 혼 위치 조정)")
    print("  attach                - 모든 서보 토크 재인가 (마지막 각도로 복귀)")
    print("  set <joint> <angle>   - 특정 관절만 각도 미세조정 (0~180)")
    print("  status                - 현재 ADC 값 확인")
    print("  save                  - 현재 각도/ADC 값을 파일로 저장")
    print("  quit                  - 종료\n")

    while True:
        try:
            raw = input(">> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw:
            continue
        parts = raw.split()
        cmd = parts[0].lower()

        if cmd == "home":
            cmd_home(ser, angles)
        elif cmd == "detach":
            send(ser, "D")
            print("서보 토크를 해제했습니다. 손으로 관절을 원하는 원점 자세로 맞추세요.")
        elif cmd == "attach":
            send(ser, "A")
            time.sleep(0.3)
            print("서보 토크를 재인가했습니다.")
            print_status(ser)
        elif cmd == "set" and len(parts) == 3:
            try:
                cmd_set(ser, angles, parts[1], int(parts[2]))
            except ValueError:
                print("각도는 정수로 입력하세요. 예: set base_shoulder 92")
        elif cmd == "status":
            print_status(ser)
        elif cmd == "save":
            adc = read_latest_adc(ser)
            cmd_save(angles, adc)
        elif cmd in ("quit", "exit", "q"):
            break
        else:
            print("알 수 없는 명령입니다.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=str, default=None, help="Arduino 시리얼 포트 (예: COM3)")
    parser.add_argument("--list-ports", action="store_true", help="사용 가능한 시리얼 포트 목록 출력")
    args = parser.parse_args()

    if args.list_ports:
        list_ports()
        return

    if not args.port:
        print("에러: --port 를 지정하세요. 포트를 모르면 --list-ports 로 확인하세요.", file=sys.stderr)
        sys.exit(1)

    ser = serial.Serial(args.port, BAUD_RATE, timeout=1)
    time.sleep(2)  # Arduino 리셋 후 부팅 대기

    interactive_loop(ser)
    ser.close()


if __name__ == "__main__":
    main()
