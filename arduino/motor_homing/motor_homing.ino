// 4축 SG90 서보 모터의 원점(Home) 위치를 맞추기 위한 스케치.
// teleop_encoder.ino와 동일한 가변저항 엔코더 배선(A0~A3)을 그대로 사용해
// 서보를 특정 각도로 움직인 뒤, 실제 관절이 그 위치에 도달했는지
// 가변저항 값으로 확인할 수 있도록 한다.
//
// 배선:
//   가변저항(엔코더): teleop_encoder.ino와 동일 (A0~A3)
//   서보 신호선: base_shoulder->D3, shoulder_arm1->D5, arm1_arm2->D6, arn2_end_arm->D9
//   (실제 배선이 다르면 아래 SERVO_PINS 값을 반드시 수정할 것)
//
// 시리얼 명령 (115200bps, 개행문자로 종료):
//   H                 -> 4개 서보 모두 HOME_ANGLE(기본 90도)로 이동
//   D                 -> 모든 서보 detach (토크 해제, 손으로 혼(horn) 위치 조정 가능)
//   A                 -> 모든 서보 다시 attach (마지막 명령 각도로 복귀)
//   S,<idx>,<angle>   -> idx(0~3)번 서보만 angle(0~180도)로 이동 (미세 조정용)
//
// 출력: 위 명령과 무관하게 "a0,a1,a2,a3\n" (raw ADC 0~1023) 를 계속 스트리밍한다.

#include <Servo.h>

const int NUM_JOINTS = 4;
const int ANALOG_PINS[NUM_JOINTS] = {A0, A1, A2, A3};
const int SERVO_PINS[NUM_JOINTS] = {3, 5, 6, 9};   // 실제 배선에 맞게 수정
const int HOME_ANGLE = 90;                          // 모든 관절의 기본 원점 각도(도)
const int SAMPLES_PER_READ = 8;
const unsigned long SEND_INTERVAL_MS = 20;

Servo servos[NUM_JOINTS];
int currentAngle[NUM_JOINTS];
bool attached[NUM_JOINTS];
unsigned long lastSendTime = 0;
String inputLine = "";

int readAveraged(int pin) {
  long sum = 0;
  for (int i = 0; i < SAMPLES_PER_READ; i++) {
    sum += analogRead(pin);
  }
  return sum / SAMPLES_PER_READ;
}

void attachAll() {
  for (int i = 0; i < NUM_JOINTS; i++) {
    if (!attached[i]) {
      servos[i].attach(SERVO_PINS[i]);
      attached[i] = true;
    }
    servos[i].write(currentAngle[i]);
  }
}

void detachAll() {
  for (int i = 0; i < NUM_JOINTS; i++) {
    servos[i].detach();
    attached[i] = false;
  }
}

void goHome() {
  for (int i = 0; i < NUM_JOINTS; i++) {
    currentAngle[i] = HOME_ANGLE;
  }
  attachAll();
}

void setServo(int idx, int angle) {
  if (idx < 0 || idx >= NUM_JOINTS) return;
  angle = constrain(angle, 0, 180);
  currentAngle[idx] = angle;
  if (!attached[idx]) {
    servos[idx].attach(SERVO_PINS[idx]);
    attached[idx] = true;
  }
  servos[idx].write(angle);
}

void handleCommand(String line) {
  line.trim();
  if (line.length() == 0) return;

  char cmd = line.charAt(0);
  if (cmd == 'H' || cmd == 'h') {
    goHome();
  } else if (cmd == 'D' || cmd == 'd') {
    detachAll();
  } else if (cmd == 'A' || cmd == 'a') {
    attachAll();
  } else if (cmd == 'S' || cmd == 's') {
    int firstComma = line.indexOf(',');
    int secondComma = line.indexOf(',', firstComma + 1);
    if (firstComma > 0 && secondComma > firstComma) {
      int idx = line.substring(firstComma + 1, secondComma).toInt();
      int angle = line.substring(secondComma + 1).toInt();
      setServo(idx, angle);
    }
  }
}

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < NUM_JOINTS; i++) {
    currentAngle[i] = HOME_ANGLE;
    attached[i] = false;
  }
  goHome();  // 전원 인가 시 바로 원점으로 이동
}

void loop() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      handleCommand(inputLine);
      inputLine = "";
    } else if (c != '\r') {
      inputLine += c;
    }
  }

  unsigned long now = millis();
  if (now - lastSendTime < SEND_INTERVAL_MS) {
    return;
  }
  lastSendTime = now;

  int values[NUM_JOINTS];
  for (int i = 0; i < NUM_JOINTS; i++) {
    values[i] = readAveraged(ANALOG_PINS[i]);
  }

  for (int i = 0; i < NUM_JOINTS; i++) {
    Serial.print(values[i]);
    if (i < NUM_JOINTS - 1) Serial.print(',');
  }
  Serial.print('\n');
}
