#include "StepperHomer.h"
#include <Arduino.h>

StepperHomer::StepperHomer(AccelStepper& stepper, int homingPin, int postFastHomeSteps, int postSlowHomeSteps, float fastHomingSpeed, float slowHomingSpeed)
  : stepper(stepper), homingPin(homingPin), preHomeSteps(preHomeSteps), postFastHomeSteps(postFastHomeSteps),
    postSlowHomeSteps(postSlowHomeSteps), fastHomingSpeed(fastHomingSpeed), slowHomingSpeed(slowHomingSpeed) {
  pinMode(homingPin, INPUT);
  reset();
}

void StepperHomer::update() {
  switch (state) {
    case PRE_HOME_MOVE:
      if (digitalRead(homingPin) == LOW) {
        state = FAST_HOME;
      } else {
        stepper.setSpeed(fastHomingSpeed);
        stepper.runSpeed();
      }
      break;

    case FAST_HOME:
      if (digitalRead(homingPin) == HIGH) {
        stepper.setCurrentPosition(0);
        stepper.moveTo(-postFastHomeSteps);
        state = POST_FAST_HOME;
      } else {
        stepper.setSpeed(fastHomingSpeed);
        stepper.runSpeed();
      }
      break;

    case POST_FAST_HOME:
      if (stepper.distanceToGo() != 0) {
        stepper.run();
      } else {
        state = SLOW_HOME;
        stepper.setSpeed(slowHomingSpeed);
      }
      break;

    case SLOW_HOME:
      if (digitalRead(homingPin) == HIGH) {
        if (abs(stepper.currentPosition()) > 4) {
          stepper.setCurrentPosition(0);
        }
        stepper.moveTo(postSlowHomeSteps);
        stepper.setSpeed(slowHomingSpeed);
        state = POST_SLOW_HOME;
      } else {
        stepper.setSpeed(slowHomingSpeed);
        stepper.runSpeed();
      }
      break;

    case POST_SLOW_HOME:
      if (stepper.distanceToGo() != 0) {
        stepper.runSpeed();
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
