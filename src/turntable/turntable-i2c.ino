#include <Servo.h>
#include <math.h>
#include <Wire.h>

// ===== Status- und Befehlskonstanten =====
const byte ROBO_BUSY       = 104;
const byte ROBO_IDLE       = 116;
const byte ROBO_MOVE_A     = 10;
const byte ROBO_MOVE_TEST  = 20;
const byte CMD_CALIBRATE   = 90;
const byte CMD_STOP        = 99;
const byte CMD_CONTINUE    = 98;

// ===== Servo-Konfiguration =====
Servo servos[6];
int initAngles[6] = {90, 20, 70, 90, 112, 30};
int preAngles[6]  = {77, 20, 70, 85, 112, 30};
int asmAngles[6]  = {77, 8, 61, 85, 112, 30};
int asm2Angles[6] = {45, 8, 61, 85, 112, 30};
int asm3Angles[6] = {58, 8, 61, 85, 112, 30};

// ===== Steuerdaten =====
String input;
int stueckzahl = 0;
int s1_winkel[11] = {58, 72, 77, 82, 87, 92, 97, 102, 107, 112, 117}; // Index 1–10

// ===== I2C-Kommunikation =====
volatile byte i2c_command = 0;
volatile byte i2c_status = ROBO_IDLE;
volatile byte pending_status = 1;  // 1 = leer, sonst: Rückgabe
volatile bool stop_requested = false;

// ===== Bewegungshilfen =====
bool waitWithStop(unsigned long ms) {
  unsigned long start = millis();
  while (millis() - start < ms) {
    checkSerialControl();
    if (checkStop()) return true;
    delay(1);
  }
  return false;
}

bool checkStop() {
  if (stop_requested) {
    Serial.println("NOTAUS erkannt – Bewegung gestoppt");
    i2c_status = ROBO_IDLE;
    pending_status = CMD_STOP;
    return true;
  }
  return false;
}

void checkSerialControl() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.equalsIgnoreCase("STOP")) {
      stop_requested = true;
      Serial.println("STOP erkannt (Serial)");
    } else if (cmd.equalsIgnoreCase("CONTINUE")) {
      stop_requested = false;
      Serial.println("CONTINUE erkannt (Serial)");
    }
  }
}

// ===== Gleichzeitige Bewegung aller Servos mit sanfter Kurve =====
void smoothMoveAll(int targets[6]) {
  const int steps = 50;
  const int delayPerStep = 15;

  int start[6];
  for (int i = 0; i < 6; i++) start[i] = initAngles[i];

  for (int i = 0; i <= steps; i++) {
    checkSerialControl();
    if (checkStop()) return;

    float t = (float)i / steps;
    float eased = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;

    for (int j = 0; j < 6; j++) {
      int pos = start[j] + (targets[j] - start[j]) * eased;
      servos[j].write(pos);
    }

    if (waitWithStop(delayPerStep)) return;
  }

  for (int i = 0; i < 6; i++) initAngles[i] = targets[i];
}

// ===== Bewegungsabläufe =====
void moveA() {
  Serial.println("Starte Move A");
  i2c_status = ROBO_BUSY;

  if (stueckzahl >= 1 && stueckzahl <= 10) {
    int s1 = s1_winkel[stueckzahl];
    preAngles[0] = s1;
    asmAngles[0] = s1;
  }

  smoothMoveAll(preAngles);
  if (waitWithStop(200)) return;
  smoothMoveAll(asmAngles);
  if (waitWithStop(200)) return;
  smoothMoveAll(asm2Angles);
  if (waitWithStop(300)) return;
  smoothMoveAll(asm3Angles);
  if (waitWithStop(200)) return;
  smoothMoveAll(preAngles);
  if (waitWithStop(1000)) return;

  i2c_status = ROBO_IDLE;
  pending_status = 115;
  Serial.println("Move A abgeschlossen");
}

void moveCAL() {
  Serial.println("Starte Kalibrierung");
  i2c_status = ROBO_BUSY;

  int target[6] = {90, 20, 70, 84, 110, 30};
  smoothMoveAll(target);
  if (waitWithStop(1000)) return;

  for (int i = 0; i < 6; i++) initAngles[i] = target[i];

  i2c_status = ROBO_IDLE;
  pending_status = CMD_CALIBRATE;
  Serial.println("Kalibrierung abgeschlossen");
}

void moveTest() {
  Serial.println("Starte moveTest");
  i2c_status = ROBO_BUSY;

  for (int st = 1; st <= 10; st++) {
    if (checkStop()) return;

    int pos_pre[6], pos_asm[6], pos_reset[6];
    for (int i = 0; i < 6; i++) {
      pos_pre[i] = preAngles[i];
      pos_asm[i] = asmAngles[i];
      pos_reset[i] = preAngles[i];
    }

    pos_pre[0] = s1_winkel[st];
    pos_asm[0] = s1_winkel[st];
    pos_reset[0] = 58;

    smoothMoveAll(pos_pre);
    if (waitWithStop(300)) return;
    smoothMoveAll(pos_asm);
    if (waitWithStop(500)) return;
    smoothMoveAll(pos_pre);
    if (waitWithStop(500)) return;
    smoothMoveAll(pos_reset);
    if (waitWithStop(500)) return;
  }

  i2c_status = ROBO_IDLE;
  pending_status = ROBO_MOVE_TEST;
  Serial.println("moveTest abgeschlossen");
}

// ===== I2C-Kommunikation =====
void receiveEvent(int howMany) {
  while (Wire.available()) {
    byte value = Wire.read();

    if (value == CMD_STOP) {
      stop_requested = true;
      Serial.println("STOP erkannt (I2C)");
    } else if (value == CMD_CONTINUE) {
      stop_requested = false;
      Serial.println("CONTINUE erkannt (I2C)");
    } else {
      i2c_command = value;
      Serial.print("I2C Befehl empfangen: ");
      Serial.println(i2c_command);
    }
  }
}

void requestEvent() {
  if (pending_status != 1) {
    Wire.write(pending_status);
    Serial.print("I2C Antwort gesendet (done): ");
    Serial.println(pending_status);
    pending_status = 1;
  } else {
    Wire.write(i2c_status);
    Serial.print("I2C Antwort gesendet (status): ");
    Serial.println(i2c_status);
  }
}

// ===== Setup & Loop =====
void setup() {
  Serial.begin(9600);
  Serial.println("Bereit. Sende CAL, A1–10, TEST, STOP oder CONTINUE");

  Wire.begin(0x08);
  Wire.onReceive(receiveEvent);
  Wire.onRequest(requestEvent);

  servos[0].attach(3);
  servos[1].attach(5);
  servos[2].attach(6);
  servos[3].attach(10);
  servos[4].attach(9);
  servos[5].attach(11);

  moveCAL(); // Initiale Kalibrierung
}

void loop() {
  checkSerialControl();

  if (Serial.available()) {
    input = Serial.readStringUntil('\n');
    input.trim();

    if (input.equalsIgnoreCase("CAL")) moveCAL();
    else if (input.equalsIgnoreCase("TEST")) moveTest();
    else if (input.startsWith("A") && input.length() >= 2) {
      int num = input.substring(1).toInt();
      if (num >= 1 && num <= 10) {
        stueckzahl = num;
        moveA();
      }
    }
  }

  if (i2c_command != 0) {
    Serial.print("Handling Command: ");
    Serial.println(i2c_command);
    if (i2c_command == CMD_CALIBRATE) moveCAL();
    else if (i2c_command >= ROBO_MOVE_A && i2c_command <= ROBO_MOVE_A + 9) {
      stueckzahl = i2c_command - ROBO_MOVE_A + 1;
      moveA();
    } else if (i2c_command == ROBO_MOVE_TEST) moveTest();
    i2c_command = 0;
  }
}
