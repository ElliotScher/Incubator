#pragma once
#include <AccelStepper.h>

class StepperHomer {
public:
  StepperHomer(AccelStepper& stepper, int homingPin, int postFastHomeSteps, int postSlowHomeSteps, float fastHomingSpeed, float slowHomingSpeed);
  void update();
  void reset();
  bool isHomed() const;

private:
  enum State {
    PRE_HOME_MOVE,
    FAST_HOME,
    POST_FAST_HOME,
    SLOW_HOME,
    POST_SLOW_HOME
};
  State state;

  AccelStepper& stepper;
  int homingPin;
  int preHomeSteps;
  int postFastHomeSteps;
  int postSlowHomeSteps;
  float fastHomingSpeed;
  float slowHomingSpeed;

  bool homed;
};
