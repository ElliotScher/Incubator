#include <Arduino.h>
#include <AccelStepper.h>
#include "StepperHomer.h"
#include "ChannelStepper.h"

#define dirPin 6
#define stepPin 5
#define homingPin 7
#define pausePin 4
#define ODPin A1
#define motorInterfaceType 1

AccelStepper stepper(motorInterfaceType, stepPin, dirPin);
StepperHomer homer(stepper, homingPin, 75, 125, 1250, 25);
ChannelStepper channelStepper(stepper, 50, 48, 500);


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

int odone = 0;
int odtwo = 0;

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
  REACT_INITIAL_HOME,
  REACT_MOVE_25,
  REACT_READ_25,
  REACT_FULL_REV,
  REACT_HOME_AGAIN,
  REACT_MOVE_25_AGAIN,
  REACT_READ_25_AGAIN,
  MOVE_HOME,
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
  stepper.setMaxSpeed(12000);
  stepper.setAcceleration(12000);
  pinMode(pausePin, INPUT_PULLUP);
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
  while (Serial.available()) {
    char c = Serial.read();

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
      } else if (superStateInputBuffer == "CMD:PLAY_REACTION" || superStateInputBuffer == "CMD:RESUME_REACTION") {
        currentState = RUN_REACTION;
        Serial.println("RESUME SUCCESSFUL");
        paused = false;
      } else {
        Serial.println("ERR:UNKNOWN_COMMAND");
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
    Serial.println("PAUSE SUCCESSFUL");
  }
  previousPaused = paused;
}

void runTestConnectionState() {
  Serial.write("p");
  Serial.write("i");
  Serial.write("n");
  Serial.write("g");
  Serial.write("\n");
  currentState = IDLE;
}

void checkCalibrationStateSerial() {
  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n') {
      calibrationStateInputBuffer.trim();

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
        currentOD += OD;
        delay(10);
      }
      currentOD /= 100;
      calibrationState = CAL_TRANSMIT_DATA;
      break;

    case CAL_TRANSMIT_DATA:
      Serial.print("OD:");
      Serial.println(currentOD);

      channelIterator++;
      if (channelIterator > channels) {
        delay(1000);
        Serial.println("CMD:CALIBRATION_FINISHED");
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
  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n') {
      reactionStateInputBuffer.trim();  // Trim any extra whitespace

      if (reactionStateInputBuffer == "CMD:CANCEL_REACTION") {
        stepper.stop();
        reactionState = REACT_NONE;
        currentState = IDLE;
      } else if (reactionStateInputBuffer == "CMD:PAUSE_REACTION") {
        currentState = IDLE;
        paused = true;
      } else if (reactionStateInputBuffer.startsWith("AGITATIONS:")) {
        String numberStr = reactionStateInputBuffer.substring(11);  // After "AGITATIONS:"
        targetAgitations = numberStr.toInt();  // Convert to integer
      }

      reactionStateInputBuffer = "";  // Clear buffer for next message
    } else {
      reactionStateInputBuffer += c;
    }
  }
}

void runReactionState() {
  checkReactionStateSerial();
  if (digitalRead(pausePin) == HIGH) {
    paused = true;
    currentState = IDLE;
  }
  if (paused) {
    return;
  }
  
  switch (reactionState) {
    case REACT_NONE:
      channelIterator = 1;
      homer.reset();
      channelStepper.setCurrentChannel(48);
      reactionState = REACT_INITIAL_HOME;
      break;
    case REACT_INITIAL_HOME:
      homer.update();
      if (homer.isHomed()) {
        homed = true;
        reactionState = REACT_MOVE_25;
      }
      break;
    case REACT_MOVE_25:
      channelStepper.moveToChannel(25, CLOCKWISE);
      delay(1000);
      reactionState = REACT_READ_25;
      break;
    case REACT_READ_25:
      currentOD = 0;
      delay(1000);
      for (int i = 0; i < 100; i++) {
        currentOD += analogRead(ODPin);
        delay(10);
      }
      currentOD /= 100;
      odone = currentOD;
      reactionState = REACT_FULL_REV;
      break;
    case REACT_FULL_REV:
      channelStepper.fullRevolution(CLOCKWISE);
      delay(1000);
      homer.reset();
      channelStepper.setCurrentChannel(48);
      reactionState = REACT_HOME_AGAIN;
      break;
    case REACT_HOME_AGAIN:
      homer.update();
      if (homer.isHomed()) {
        homed = true;
        reactionState = REACT_MOVE_25_AGAIN;
      }
      break;
    case REACT_MOVE_25_AGAIN:
      channelStepper.moveToChannel(25, CLOCKWISE);
      delay(1000);
      reactionState = REACT_READ_25_AGAIN;
      break;
    case REACT_READ_25_AGAIN:
      currentOD = 0;
      delay(1000);
      for (int i = 0; i < 100; i++) {
        currentOD += analogRead(ODPin);
        delay(10);
      }
      currentOD /= 100;
      odtwo = currentOD;
      homer.reset();
      channelStepper.setCurrentChannel(48);
      reactionState = MOVE_HOME;
      break;
    case MOVE_HOME:
      Serial.print("odone: ");
      Serial.print(odone);
      Serial.print(" odtwo: ");
      Serial.println(odtwo);
      if (odone > odtwo) {
        channelStepper.fullRevolution(COUNTER_CLOCKWISE);
      }
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
      Serial.print("OD:");
      Serial.print(currentOD);
      Serial.print("CH:");
      Serial.println(channelIterator);

      channelIterator++;
      if (channelIterator > 50) {
        channelStepper.fullRevolution(COUNTER_CLOCKWISE);
        channelIterator = 1;
        homer.reset();
        homed = false;
        reactionState = REACT_HOME_WHEEL;
        channelStepper.setCurrentChannel(48);
      } else if (targetAgitations != 0) {
        reactionState = REACT_AGITATE;
      } else {
        reactionState = REACT_MOVE_TO_POSITION;
      }
      break;
  }
}
