// ===== 单路超声波 + 蜂鸣器 测试 =====
const int trigPin = 9;    // Trig → D9
const int echoPin = 10;   // Echo → D10
const int buzzer  = 12;   // 蜂鸣器 I/O → D12

const float THRESHOLD = 20.0;   // 小于 20cm 报警

void setup() {
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(buzzer, OUTPUT);
  digitalWrite(buzzer, LOW);

  Serial.begin(9600);

  // 上电自检：蜂鸣器响一声
  Serial.println("=== Self test ===");
  digitalWrite(buzzer, HIGH); delay(300);
  digitalWrite(buzzer, LOW);
  Serial.println("=== Start ===");
}

float readDistance() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long dur = pulseIn(echoPin, HIGH, 30000);
  if (dur == 0) return 0;
  return dur * 0.0343 / 2.0;
}

void loop() {
  float d = readDistance();
  bool hit = (d > 0 && d < THRESHOLD);

  Serial.print("D=");
  Serial.print(d, 1);
  Serial.print("cm  ");
  Serial.println(hit ? "OCC -> BEEP" : "--");

  digitalWrite(buzzer, hit ? HIGH : LOW);

  delay(300);
}