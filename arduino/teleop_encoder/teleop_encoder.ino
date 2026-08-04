// SG90 내부 포지션 감지용 가변저항(포텐셔미터)을 엔코더로 재활용해
// 4개 관절(base_shoulder, shoulder_arm1, arm1_arm2, arn2_end_arm)의 각도를
// 아날로그로 읽어 PC(Python)로 스트리밍한다.
//
// 배선: 각 가변저항의 저항 양 끝 2가닥 -> 5V / GND (공용 레일)
//       가변저항 와이퍼(가운데) 1가닥 -> A0 ~ A3 (관절 1개당 1핀)
//
// 출력 포맷: "a0,a1,a2,a3\n" (0~1023 raw ADC 값, 콤마 구분)
// Arduino Uno/Nano 기준, Serial 115200bps

const int NUM_JOINTS = 4;
const int ANALOG_PINS[NUM_JOINTS] = {A0, A1, A2, A3};
const int SAMPLES_PER_READ = 8;      // 노이즈 감소용 평균 샘플 수
const unsigned long SEND_INTERVAL_MS = 20; // 약 50Hz

unsigned long lastSendTime = 0;

int readAveraged(int pin) {
  long sum = 0;
  for (int i = 0; i < SAMPLES_PER_READ; i++) {
    sum += analogRead(pin);
  }
  return sum / SAMPLES_PER_READ;
}

void setup() {
  Serial.begin(115200);
}

void loop() {
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
    if (i < NUM_JOINTS - 1) {
      Serial.print(',');
    }
  }
  Serial.print('\n');
}
