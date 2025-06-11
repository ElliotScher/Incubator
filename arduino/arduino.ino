#include <Arduino.h>
#include <AccelStepper.h>
#include "StepperHomer.h"

#define dirPin 2
#define stepPin 3
#define homingPin 28
#define motorInterfaceType 1

AccelStepper stepper(motorInterfaceType, stepPin, dirPin);
StepperHomer homer(stepper, homingPin, 25, 625);

enum SuperState {
  IDLE,
  TEST_CONNECTION,
  CALIBRATE,
  RUN_REACTION
};

SuperState currentState = IDLE;
String inputBuffer = "";

void setup() {
  Serial.begin(9600);
  Serial1.begin(9600);
  stepper.setMaxSpeed(3000);
  stepper.setAcceleration(10000);
  pinMode(homingPin, INPUT);
}

void loop() {
  checkSerialInput();
  
  switch (currentState) {
    case IDLE:
      break;

    case TEST_CONNECTION:
      echoSerialInput();
      break;

    case CALIBRATE:
      break;

    case RUN_REACTION:
      break;
  }

//  Serial.println(currentState);
}

void checkSerialInput() {
  while (Serial1.available()) {
    char c = Serial1.read();

    if (c == '\n') {
      // Process the command once the whole line is received
      if (inputBuffer == "CMD:TESTCONNECTION") {
        currentState = TEST_CONNECTION;
      } else if (inputBuffer == "CMD:CALIBRATE") {
        currentState = CALIBRATE;
      } else if (inputBuffer == "CMD:RUNREACTION") {
        currentState = RUN_REACTION;
      } else if (inputBuffer == "CMD:IDLE") {
        currentState = IDLE;
      } else {
        Serial1.println("ERR:UNKNOWN_COMMAND");
      }

      Serial.println(inputBuffer);
      inputBuffer = ""; // Clear buffer for next command
    } else {
      inputBuffer += c;
    }
  }
}

void echoSerialInput() {
  while (Serial1.available()) {
    char c = Serial1.read();
    Serial1.write(c);  // Echo back each character
  }
}
