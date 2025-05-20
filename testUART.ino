#include <Arduino.h>

void setup() {
  Serial1.begin(9600);
}

void loop() {
  if (Serial1.available()) {
    char c = Serial.read();
    Serial1.write(c);
  }
}
