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

String inputBuffer = "";

void setup() {
  Serial.begin(9600);
  Serial1.begin(9600);
  stepper.setMaxSpeed(3000);
  stepper.setAcceleration(10000);
}

void loop() {
  checkSerialInput();
  
  switch (currentState) {
    case IDLE:
      break;

    case TEST_CONNECTION:
      Serial1.write("p");
      Serial1.write("i");
      Serial1.write("n");
      Serial1.write("g");
      Serial1.write("\n");
      currentState = IDLE;
      break;

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
      inputBuffer.trim();
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

void runCalibrationState() {
  switch (calibrationState) {
    case CAL_NONE:
      calibrationState = CAL_RECEIVE_CHANNELS;
      break;
      
    case CAL_RECEIVE_CHANNELS:
      if (Serial1.available()) {
        String input = Serial1.readStringUntil('\n');
        input.trim();
    
        if (input.startsWith("CHANNELS:")) {
          channels = input.substring(9).toInt();
          Serial1.println("ACK:CHANNELS_RECEIVED");
          calibrationState = CAL_HOME_WHEEL;
          waitingForChannels = true;
        } else {
          Serial1.println("ERR:INVALID_CHANNEL_DATA");
        }
      }
      break;

      calibrationState = CAL_HOME_WHEEL;
      break;

    case CAL_HOME_WHEEL:
      if (homed) {
        calibrationState = CAL_MOVE_TO_POSITION;
      } else {
        if (!homer.isHomed()) {
          homer.update();
        } else {
          homer.reset();
        }
      }
      if (homer.isHomed()) {
        homed = true;
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
