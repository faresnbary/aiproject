char command;

void setup() {
  Serial.begin(9600);
  Serial.println("Arduino is ready");
  Serial.println("Waiting for commands: F, B, L, R, S");
}

void loop() {
  if (Serial.available() > 0) {
    command = Serial.read();

    if (command == 'F') {
      Serial.println("Command received: FORWARD");
    }
    else if (command == 'B') {
      Serial.println("Command received: BACKWARD");
    }
    else if (command == 'L') {
      Serial.println("Command received: LEFT");
    }
    else if (command == 'R') {
      Serial.println("Command received: RIGHT");
    }
    else if (command == 'S') {
      Serial.println("Command received: STOP");
    }
    else {
      Serial.print("Unknown command: ");
      Serial.println(command);
    }
  }
}