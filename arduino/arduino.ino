#include <Arduino.h>
#include <AccelStepper.h>
#include "StepperHomer.h"
#include "ChannelStepper.h"

#define dirPin 6
#define stepPin 5
#define homingPin 7
#define ODPin A1
#define motorInterfaceType 1

AccelStepper stepper(motorInterfaceType, stepPin, dirPin);
StepperHomer homer(stepper, homingPin, 25, 125, 1250, 100);
ChannelStepper channelStepper(stepper, 50, 48, 800, 31.25);


// Calibration Variables
int channels = 0;
bool waitingForChannels = false;
bool homed = false;
int channelIterator = 0;
unsigned long currentOD = 0;
int targetAgitations = 0;
int currentAgitations = 0;
bool paused = false;
bool previousPaused = false;

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
  REACT_TRANSMIT_DATA
};

SuperState currentState = IDLE;
CalibrationState calibrationState = CAL_NONE;
ReactionState reactionState = REACT_NONE;

String superStateInputBuffer = "";
String calibrationStateInputBuffer = "";
String reactionStateInputBuffer = "";

void setup() {
  Serial.begin(9600);
  Serial1.begin(9600);
  stepper.setMaxSpeed(15000);
  stepper.setAcceleration(15000);
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
      runReactionState();
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
      } else if (superStateInputBuffer.substring(0, 11) == "AGITATIONS:") {
        targetAgitations = superStateInputBuffer.substring(11).toInt();
      } else if (superStateInputBuffer == "CMD:RUNREACTION") {
        currentState = RUN_REACTION;
      } else if (superStateInputBuffer == "CMD:IDLE") {
        currentState = IDLE;
      } else if (superStateInputBuffer == "CMD:PLAY_REACTION") {
        currentState = RUN_REACTION;
        paused = false;
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
  if (paused && !previousPaused) {
    Serial1.println("PAUSE SUCCESSFUL");
  }

//  Serial.println(paused);

  previousPaused = paused;
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

//      Serial.println(calibrationStateInputBuffer);

      if (calibrationStateInputBuffer == "CMD:CANCEL_CALIBRATION") {
        stepper.stop();
        calibrationState = CAL_NONE;
        currentState = IDLE;
      } else if (calibrationStateInputBuffer.startsWith("CHANNELS:")) {
        String numberStr = calibrationStateInputBuffer.substring(9);  // After "CHANNELS:"
        channels = numberStr.toInt();  // Convert to integer
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
      currentOD = 0;
      delay(1000);
      for (int i = 0; i < 100; i++) {
        int OD = analogRead(ODPin);
        Serial.println(OD);
        currentOD += OD;
        delay(10);
      }
      currentOD /= 100;
      calibrationState = CAL_TRANSMIT_DATA;
      break;

    case CAL_TRANSMIT_DATA:
      Serial1.print("OD:");
      Serial1.println(currentOD);

      channelIterator++;
      if (channelIterator > channels) {
        delay(1000);
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

void checkReactionStateSerial() {
  while (Serial1.available()) {
    char c = Serial1.read();

    if (c == '\n') {
      reactionStateInputBuffer.trim();  // Trim any extra whitespace

//      Serial.println(reactionStateInputBuffer);

      if (reactionStateInputBuffer == "CMD:CANCEL_REACTION") {
        stepper.stop();
        reactionState = REACT_NONE;
        currentState = IDLE;
      } else if (reactionStateInputBuffer == "CMD:PAUSE_REACTION") {
        Serial.println("Pausing");
        currentState = IDLE;
        paused = true;
      } else if (reactionStateInputBuffer.startsWith("AGITATIONS:")) {
        String numberStr = reactionStateInputBuffer.substring(11);  // After "AGITATIONS:"
        targetAgitations = numberStr.toInt();  // Convert to integer
//        Serial.print("Agitations: ");
//        Serial.println(targetAgitations);
      }

      reactionStateInputBuffer = "";  // Clear buffer for next message
    } else {
      reactionStateInputBuffer += c;
    }
  }
}

void runReactionState() {
  checkReactionStateSerial();
  if (paused) {
    return;
  }

  if (!paused && previousPaused) {
    Serial1.println("RESUME SUCCESSFUL");
    delay(1000);
  }
  
  switch (reactionState) {
    case REACT_NONE:
      channelIterator = 1;
      homer.reset();
      channelStepper.setCurrentChannel(48);
      reactionState = REACT_HOME_WHEEL;
      break;
    case REACT_HOME_WHEEL:
      homer.update();
  
      if (homer.isHomed()) {
        homed = true;

        reactionState = REACT_MOVE_TO_POSITION;
      }
      break;
    case REACT_AGITATE:
      channelStepper.fullRevolution(COUNTER_CLOCKWISE);
      channelStepper.fullRevolution(CLOCKWISE);
      currentAgitations++;
      if (currentAgitations >= targetAgitations) {
        reactionState = REACT_MOVE_TO_POSITION;
        currentAgitations = 1;
      }
      break;
    case REACT_MOVE_TO_POSITION:
      channelStepper.moveToChannel(channelIterator);
      delay(1000);
      reactionState = REACT_READ_ANALOG;
      break;
    case REACT_READ_ANALOG:
      currentOD = 0;
      delay(1000);
      for (int i = 0; i < 100; i++) {
        currentOD += analogRead(ODPin);
        delay(10);
      }
      currentOD /= 100;
      reactionState = REACT_TRANSMIT_DATA;
      break;
    case REACT_TRANSMIT_DATA:
      Serial1.print("OD:");
      Serial1.println(currentOD);

      channelIterator++;
      channelIterator %= 50;
      if (targetAgitations != 0) {
        reactionState = REACT_AGITATE;
      } else {
        reactionState = REACT_MOVE_TO_POSITION;
      }
      break;
  }
}
