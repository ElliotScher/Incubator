#include "ChannelStepper.h"

ChannelStepper::ChannelStepper(AccelStepper& stepper_,
                               int totalChannels_,
                               int zeroPosition_,
                               int stepsPerChannel_)
  : stepper(stepper_),
    totalChannels(totalChannels_),
    zeroPosition(zeroPosition_),
    stepsPerChannel(stepsPerChannel_),
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

void ChannelStepper::fullRevolution(RotationDirection direction) {
  int targetChannel = currentChannel;  // Stay on same channel
  long deltaSteps = static_cast<long>(totalChannels) * stepsPerChannel;

  if (direction == CLOCKWISE) {
    stepper.moveTo(stepper.currentPosition() - deltaSteps);
  } else {
    stepper.moveTo(stepper.currentPosition() + deltaSteps);
  }

  while (stepper.distanceToGo() != 0) {
    stepper.run();
  }
}
