#pragma once
#include <AccelStepper.h>

class StepperHomer {
public:
  StepperHomer(AccelStepper& stepper, int homingPin, int postHomeSteps, float homingSpeed);
  void update();
  void reset();
  bool isHomed() const;

private:
  enum State { PRE_HOME_MOVE, FIND_HOME, MOVE_AFTER_HOME };
  State state;

  AccelStepper& stepper;
  int homingPin;
  int preHomeSteps;
  int postHomeSteps;
  float homingSpeed;

  bool homed;
};
