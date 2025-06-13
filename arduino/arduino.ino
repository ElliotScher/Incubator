#include <Arduino.h>
#include <AccelStepper.h>
#include "StepperHomer.h"
#include "ChannelStepper.h"

#define dirPin 2
#define stepPin 3
#define homingPin 28
#define ODPin A0
#define motorInterfaceType 1

AccelStepper stepper(motorInterfaceType, stepPin, dirPin);
StepperHomer homer(stepper, homingPin, 25, 625);
ChannelStepper channelStepper(stepper, 50, 48, 800, 6.25);


// Calibration Variables
int channels = 0;
bool waitingForChannels = false;
bool homed = false;
int channelIterator = 0;
int currentOD = 0;

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
  stepper.setAcceleration(6000);
}

void loop() {
  switch (currentState) {
    case IDLE:
      runIdleState();
      break;

    case TEST_CONNECTION:
      runTestConnectionState();
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

      if (calibrationStateInputBuffer == "CMD:CANCEL_CALIBRATION") {
        stepper.stop();
        calibrationState = CAL_NONE;
        currentState = IDLE;
      } else if (calibrationStateInputBuffer.startsWith("CHANNELS:")) {
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

void runCalibrationState() {
  checkCalibrationStateSerial();
  
  switch (calibrationState) {
    case CAL_NONE:
      channelIterator = 1;
      homer.reset();
      channelStepper.setCurrentChannel(48);
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
      delay(1000);
      channelStepper.moveToChannel(channelIterator);
      channelStepper.moveToChannel(channelIterator, COUNTER_CLOCKWISE);
      channelStepper.moveToChannel(channelIterator, CLOCKWISE);
      delay(1000);
      calibrationState = CAL_READ_ANALOG;
      break;

    case CAL_READ_ANALOG:
      delay(10000);
      currentOD = analogRead(ODPin);
      calibrationState = CAL_TRANSMIT_DATA;
      break;

    case CAL_TRANSMIT_DATA:
      Serial1.print("OD:");
      Serial1.println(currentOD);

      channelIterator++;
      if (channelIterator > channels) {
        delay(10000);
        Serial1.println("CMD:CALIBRATION_FINISHED");
        currentState = IDLE;
        calibrationState = CAL_NONE;
      } else {
        calibrationState = CAL_MOVE_TO_POSITION;
      }
      break;

    default:
      break;
  }
}
