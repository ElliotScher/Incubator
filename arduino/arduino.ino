#include <Arduino.h>
#include <AccelStepper.h>
#include "StepperHomer.h"

#define dirPin 2
#define stepPin 3
#define homingPin 28
#define motorInterfaceType 1

AccelStepper stepper(motorInterfaceType, stepPin, dirPin);
StepperHomer homer(stepper, homingPin, 25, 625);

// Calibration Variables
int channels = 0;
bool waitingForChannels = false;
bool homed = false;


enum SuperState {
  IDLE,
  TEST_CONNECTION,
  CALIBRATE,
  RUN_REACTION
};

enum CalibrationState {
  CAL_NONE,
  CAL_RECEIVE_CHANNELS,
  CAL_HOME_WHEEL,
  CAL_MOVE_TO_POSITION,
  CAL_READ_ANALOG,
  CAL_TRANSMIT_DATA
};

enum ReactionState {
  REACT_NONE,
  REACT_HOME_WHEEL,
  REACT_AGITATE,
  REACT_MOVE_TO_POSITION,
  REACT_READ_ANALOG,
  REACT_TRANSMIT_DATA,
  REACT_WAIT_FOR_GAZOSCAN,
  REACT_SEND_FLAG
};

SuperState currentState = IDLE;
CalibrationState calibrationState = CAL_NONE;
ReactionState reactionState = REACT_NONE;

String superStateInputBuffer = "";
String calibrationStateInputBuffer = "";

void setup() {
  Serial.begin(9600);
  Serial1.begin(9600);
  stepper.setMaxSpeed(3000);
  stepper.setAcceleration(10000);
}

void loop() {
  switch (currentState) {
    case IDLE:
      runIdleState();
      break;

    case TEST_CONNECTION:
      
      break;

    case CALIBRATE:
      runCalibrationState();
      break;

    case RUN_REACTION:
      break;
  }
}

void checkSuperStateSerial() {
  while (Serial1.available()) {
    char c = Serial1.read();

    if (c == '\n') {
      superStateInputBuffer.trim();

      if (superStateInputBuffer == "CMD:TESTCONNECTION") {
        currentState = TEST_CONNECTION;
      } else if (superStateInputBuffer == "CMD:CALIBRATE") {
        currentState = CALIBRATE;
      } else if (superStateInputBuffer == "CMD:RUNREACTION") {
        currentState = RUN_REACTION;
      } else if (superStateInputBuffer == "CMD:IDLE") {
        currentState = IDLE;
      } else {
        Serial1.println("ERR:UNKNOWN_COMMAND");
      }

      superStateInputBuffer = ""; // Clear buffer for next command
    } else {
      superStateInputBuffer += c;
    }
  }
}

void runIdleState() {
  checkSuperStateSerial();
}

void runCalibrationState() {
  checkCalibrationStateSerial();
  
  switch (calibrationState) {
    case CAL_NONE:
      calibrationState = CAL_RECEIVE_CHANNELS;
      break;
      
    case CAL_RECEIVE_CHANNELS:
      if (channels != 0) {
        calibrationState = CAL_HOME_WHEEL;
      }
      break;

    case CAL_HOME_WHEEL:
      homer.update();
  
      if (homer.isHomed()) {
        homed = true;
        calibrationState = CAL_MOVE_TO_POSITION;
      }
      break;

    case CAL_MOVE_TO_POSITION:
      // move to known calibration position
      // once reached:
      calibrationState = CAL_READ_ANALOG;
      break;

    case CAL_READ_ANALOG:
      // analogRead() sensors here
      calibrationState = CAL_TRANSMIT_DATA;
      break;

    case CAL_TRANSMIT_DATA:
      // Serial1.println() of calibration data
      currentState = IDLE;
      calibrationState = CAL_NONE;
      break;

    default:
      break;
  }
}

void runTestConnectionState() {
  Serial1.write("p");
  Serial1.write("i");
  Serial1.write("n");
  Serial1.write("g");
  Serial1.write("\n");
  currentState = IDLE;
}

void checkCalibrationStateSerial() {
  while (Serial1.available()) {
    char c = Serial1.read();

    if (c == '\n') {
      calibrationStateInputBuffer.trim();  // Trim any extra whitespace

      Serial.println(calibrationStateInputBuffer);

      if (calibrationStateInputBuffer.startsWith("CHANNELS:")) {
        String numberStr = calibrationStateInputBuffer.substring(9);  // After "CHANNELS:"
        channels = numberStr.toInt();  // Convert to integer
        Serial.print("Parsed channels: ");
        Serial.println(channels);
      }

      calibrationStateInputBuffer = "";  // Clear buffer for next message
    } else {
      calibrationStateInputBuffer += c;
    }
  }
}
