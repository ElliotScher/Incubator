#include "StepperHomer.h"
#include <Arduino.h>

StepperHomer::StepperHomer(AccelStepper& stepper, int homingPin, int postHomeSteps, float homingSpeed)
  : stepper(stepper), homingPin(homingPin), preHomeSteps(preHomeSteps),
    postHomeSteps(postHomeSteps), homingSpeed(homingSpeed) {
  pinMode(homingPin, INPUT);
  reset();
}

void StepperHomer::update() {
  switch (state) {
    case PRE_HOME_MOVE:
      if (digitalRead(homingPin) == LOW) {
        state = FIND_HOME;
      } else {
        stepper.setSpeed(homingSpeed);
        stepper.runSpeed();
      }
      break;

    case FIND_HOME:
      if (digitalRead(homingPin) == HIGH) {
        stepper.setCurrentPosition(0);
        stepper.moveTo(postHomeSteps);
        state = MOVE_AFTER_HOME;
      } else {
        stepper.setSpeed(homingSpeed);
        stepper.runSpeed();
      }
      break;

    case MOVE_AFTER_HOME:
      if (stepper.distanceToGo() != 0) {
        stepper.run();
      } else {
        homed = true;
      }
      break;
  }
}

void StepperHomer::reset() {
  homed = false;
  state = PRE_HOME_MOVE;
}

bool StepperHomer::isHomed() const {
  return homed;
}
