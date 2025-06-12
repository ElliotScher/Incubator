#include "ChannelStepper.h"

ChannelStepper::ChannelStepper(AccelStepper& stepper_,
                               int totalChannels_,
                               int zeroPosition_,
                               int stepsPerRev_,
                               float gearRatio_)
  : stepper(stepper_),
    totalChannels(totalChannels_),
    zeroPosition(zeroPosition_),
    stepsPerRev(stepsPerRev_),
    gearRatio(gearRatio_),
    stepsPerChannel(static_cast<int>((stepsPerRev_ * gearRatio_) / totalChannels_)),
    currentChannel(zeroPosition_)
{
}

int ChannelStepper::getCurrentChannel() const {
  return currentChannel;
}

void ChannelStepper::setCurrentChannel(int channel) {
  if (channel >= 0 && channel < totalChannels) {
    currentChannel = channel;
  }
}

long ChannelStepper::channelToSteps(int channel) {
  int deltaChannels = (channel - zeroPosition + totalChannels) % totalChannels;
  return static_cast<long>(deltaChannels) * stepsPerChannel;
}

long ChannelStepper::computeStepDelta(int fromChannel, int toChannel, RotationDirection direction) {
  int delta;

  if (fromChannel == toChannel) {
    // Full rotation in specified direction
    delta = (direction == CLOCKWISE) ? totalChannels : -totalChannels;
  } else {
    if (direction == CLOCKWISE) {
      delta = -((toChannel - fromChannel + totalChannels) % totalChannels);
    } else {
      delta = (fromChannel - toChannel + totalChannels) % totalChannels;
    }
  }

  return static_cast<long>(delta) * stepsPerChannel;
}

void ChannelStepper::moveToChannel(int targetChannel, RotationDirection direction) {
  long deltaSteps = computeStepDelta(currentChannel, targetChannel, direction);
  long targetPosition = stepper.currentPosition() + deltaSteps;

  stepper.moveTo(targetPosition);

  // Run the stepper until it reaches the position
  while (stepper.distanceToGo() != 0) {
    stepper.run();
  }

  currentChannel = targetChannel;
}

void ChannelStepper::moveToChannel(int targetChannel) {
  int clockwiseDelta = (targetChannel - currentChannel + totalChannels) % totalChannels;
  int counterClockwiseDelta = (currentChannel - targetChannel + totalChannels) % totalChannels;

  if (clockwiseDelta <= counterClockwiseDelta) {
    moveToChannel(targetChannel, CLOCKWISE);
  } else {
    moveToChannel(targetChannel, COUNTER_CLOCKWISE);
  }
}
