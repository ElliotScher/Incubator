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
  Serial1.begin(9600);
  stepper.setMaxSpeed(3000);
  stepper.setAcceleration(10000);
  pinMode(homingPin, INPUT);
}

void loop() {
  switch (currentState) {
    case IDLE:
      checkSerialInput();
      if (inputBuffer == "CMD:TESTCONNECTION") currentState = TEST_CONNECTION;
      break;

    case TEST_CONNECTION:
      if (Serial1.available()) {
        char c = Serial1.read();
        Serial1.write(c);
      }

    case CALIBRATE:
      break;

    case RUN_REACTION:
      break;
  }
}

void checkSerialInput() {
  while (Serial1.available()) {
    char c = Serial1.read();
    if (c == '\n') {
      handleCommand(inputBuffer);
      inputBuffer = "";
    } else {
      inputBuffer += c;
    }
  }
}

void handleCommand(String cmd) {
  cmd.trim();
  cmd.toUpperCase();
}
