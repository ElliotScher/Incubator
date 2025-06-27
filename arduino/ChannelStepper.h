#include <AccelStepper.h>

enum RotationDirection {
  CLOCKWISE,
  COUNTER_CLOCKWISE
};

class ChannelStepper {
private:
  AccelStepper& stepper;
  const int totalChannels;
  const int zeroPosition;
  const int stepsPerChannel;

  int currentChannel;

public:
  ChannelStepper(AccelStepper& stepper_,
                 int totalChannels_,
                 int zeroPosition_,
                 int stepsPerChannel_);

  int getCurrentChannel() const;
  void setCurrentChannel(int channel);

  long channelToSteps(int channel);
  long computeStepDelta(int fromChannel, int toChannel, RotationDirection direction);

  void moveToChannel(int targetChannel, RotationDirection direction);
  void moveToChannel(int targetChannel);

  void fullRevolution(RotationDirection direction);
};
