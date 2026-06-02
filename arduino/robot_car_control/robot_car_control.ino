// L298N motor driver pins
int IN1 = 8;
int IN2 = 9;
int IN3 = 10;
int IN4 = 11;

char command;

// Change these if a motor direction is reversed
bool LEFT_MOTOR_REVERSED = false;
bool RIGHT_MOTOR_REVERSED = false;

void setup() {
  Serial.begin(9600);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  stopMotors();

  Serial.println("Robot car ready");
  Serial.println("Commands: F, B, L, R, S");
  Serial.println("Test: 1 left forward, 2 left backward, 3 right forward, 4 right backward");
}

void loop() {
  if (Serial.available() > 0) {
    command = Serial.read();

    if (command == 'F') {
      forward();
      Serial.println("FORWARD");
    }
    else if (command == 'B') {
      backward();
      Serial.println("BACKWARD");
    }
    else if (command == 'L') {
      left();
      Serial.println("LEFT");
    }
    else if (command == 'R') {
      right();
      Serial.println("RIGHT");
    }
    else if (command == 'S') {
      stopMotors();
      Serial.println("STOP");
    }
    else if (command == '1') {
      setLeftMotorForward();
      stopRightMotor();
      Serial.println("LEFT MOTOR FORWARD");
    }
    else if (command == '2') {
      setLeftMotorBackward();
      stopRightMotor();
      Serial.println("LEFT MOTOR BACKWARD");
    }
    else if (command == '3') {
      setRightMotorForward();
      stopLeftMotor();
      Serial.println("RIGHT MOTOR FORWARD");
    }
    else if (command == '4') {
      setRightMotorBackward();
      stopLeftMotor();
      Serial.println("RIGHT MOTOR BACKWARD");
    }
  }
}

void forward() {
  setLeftMotorForward();
  setRightMotorForward();
}

void backward() {
  setLeftMotorBackward();
  setRightMotorBackward();
}

void left() {
  setLeftMotorBackward();
  setRightMotorForward();
}

void right() {
  setLeftMotorForward();
  setRightMotorBackward();
}

void stopMotors() {
  stopLeftMotor();
  stopRightMotor();
}

void setLeftMotorForward() {
  if (!LEFT_MOTOR_REVERSED) {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
  } else {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
  }
}

void setLeftMotorBackward() {
  if (!LEFT_MOTOR_REVERSED) {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
  } else {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
  }
}

void stopLeftMotor() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
}

void setRightMotorForward() {
  if (!RIGHT_MOTOR_REVERSED) {
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
  } else {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
  }
}

void setRightMotorBackward() {
  if (!RIGHT_MOTOR_REVERSED) {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
  } else {
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
  }
}

void stopRightMotor() {
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}