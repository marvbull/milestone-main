#include <Servo.h>
#include <math.h>

Servo servos[6];
int currentAngles[6] = {90, 70, 70, 90, 90, 90};

const float L1 = 127.026;
const float L2 = 119.980;
const float L3 = 122.308;
const float L4 = 129.823;

String input;
float dx, dy, dz, phi;

void smoothMoveAll(int targets[6]) {
  const int steps = 50;
  const int delayPerStep = 15;

  int start[6];
  for (int i = 0; i < 6; i++) start[i] = currentAngles[i];

  for (int i = 0; i <= steps; i++) {
    float t = (float)i / steps;
    float eased = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;

    for (int j = 0; j < 6; j++) {
      int pos = start[j] + (targets[j] - start[j]) * eased;
      servos[j].write(pos);
    }

    delay(delayPerStep);
  }

  for (int i = 0; i < 6; i++) currentAngles[i] = targets[i];
}

void executeCommand(String cmd) {
  cmd.trim();

  // Wartebefehl WAIT:ms
  if (cmd.startsWith("WAIT:")) {
    int waitTime = cmd.substring(5).toInt();
    Serial.print("Warte ");
    Serial.print(waitTime);
    Serial.println(" ms");
    delay(waitTime);
    return;
  }

  // Inverse Kinematik (Pxxxx yyyy zzzz ppp)
  if (cmd.startsWith("P") && cmd.length() >= 16) {
    dx = cmd.substring(1, 5).toFloat();
    dy = cmd.substring(5, 9).toFloat();
    dz = cmd.substring(9, 13).toFloat();
    phi = radians(cmd.substring(13, 16).toFloat());

    float theta1 = atan2(dy, dx);
    if (degrees(theta1) < 0 || degrees(theta1) > 180)
      theta1 = fmod(theta1 + PI, 2 * PI);

    float A = dx - L4 * cos(phi) * cos(theta1);
    float B = dy - L4 * cos(phi) * sin(theta1);
    float C = dz - L1 - L4 * sin(phi);
    float R = sqrt(A * A + B * B);

    float D = (R * R + C * C - L2 * L2 - L3 * L3) / (2.0 * L2 * L3);
    D = constrain(D, -1.0, 1.0);

    float theta3 = acos(D);
    float a = L3 * sin(theta3);
    float b = L2 + L3 * cos(theta3);
    float theta2 = atan2(C, R) - atan2(a, b);
    float theta4 = phi - theta2 - theta3;

    float t1_deg = fmod(degrees(theta1) + 360.0, 360.0);
    float t2_deg = fmod(degrees(theta2) + 360.0, 360.0);
    float t3_deg = fmod(degrees(theta3) + 360.0, 360.0);
    float t4_deg = fmod(degrees(theta4) + 360.0, 360.0);

    bool isValid = t1_deg <= 180 && t2_deg <= 180 && t3_deg <= 180 && t4_deg <= 180;
    if (!isValid) {
      Serial.println("Ungültige Lösung: Winkel außerhalb von 0°–180°.");
      return;
    }

    int deg1 = constrain(round(t1_deg), 0, 180);
    int deg2 = constrain(round(t2_deg), 0, 180);
    int deg3 = constrain(round(t3_deg), 0, 180);
    int deg4 = constrain(round(t4_deg), 0, 180);

    int targets[6] = {
      deg1, deg2, deg3,
      currentAngles[3],
      deg4,
      currentAngles[5]
    };

    Serial.print("Fahre Position: ");
    Serial.print(dx); Serial.print(", ");
    Serial.print(dy); Serial.print(", ");
    Serial.print(dz); Serial.print(" (");
    Serial.print(degrees(phi), 1); Serial.println("°)");

    smoothMoveAll(targets);
    return;
  }

  // Einzelservo setzen: S1xxx
  if (cmd.startsWith("S") && cmd.length() >= 4) {
    int servoIndex = cmd.substring(1, 2).toInt() - 1;
    int angle = cmd.substring(2).toInt();

    if (servoIndex >= 0 && servoIndex < 6 && angle >= 0 && angle <= 180) {
      int targets[6];
      for (int i = 0; i < 6; i++) targets[i] = currentAngles[i];
      targets[servoIndex] = angle;

      Serial.print("Servo S");
      Serial.print(servoIndex + 1);
      Serial.print(" auf ");
      Serial.print(angle);
      Serial.println("°");

      smoothMoveAll(targets);
    } else {
      Serial.println("Ungültiger Servo-Befehl.");
    }
  }
}

void setup() {
  Serial.begin(9600);
  Serial.println("Bereit. Sende PROG:... oder einzelne Befehle.");

  servos[0].attach(3);
  servos[1].attach(5);
  servos[2].attach(6);
  servos[3].attach(10);
  servos[4].attach(9);
  servos[5].attach(11);

  for (int i = 0; i < 6; i++) servos[i].write(currentAngles[i]);
}

void loop() {
  if (Serial.available()) {
    input = Serial.readStringUntil('\n');
    input.trim();

    if (input.startsWith("PROG:")) {
      input.remove(0, 5);
      int lastIndex = 0;
      while (true) {
        int nextIndex = input.indexOf(';', lastIndex);
        String cmd = (nextIndex != -1) ?
                     input.substring(lastIndex, nextIndex) :
                     input.substring(lastIndex);
        executeCommand(cmd);
        if (nextIndex == -1) break;
        lastIndex = nextIndex + 1;
      }
    } else {
      executeCommand(input);
    }
  }
}

