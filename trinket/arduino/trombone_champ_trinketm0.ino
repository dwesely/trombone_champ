#include "Adafruit_VL53L0X.h"
#include <AbsMouse.h>

Adafruit_VL53L0X lox = Adafruit_VL53L0X();

// Prepare pins and debouncing
const byte tootPin = 1;
const byte activePin = 3;
const byte invertPin = 4;
unsigned long lastDebounceTime = 0;       // the last time the output pin was toggled
const unsigned long debounceDelay = 50;   // the debounce time; increase if the output flickers
volatile boolean invertedFlag = false;    // Indicates whether mouse movement is inverted (true) or standard (false)
volatile boolean mouseModeFlag = false;   // Indicates whether device is in mouse mode (true) or off (false)
volatile boolean tootProcessing = false;  // only handle one toot request at once
volatile uint16_t lastRange = 0;
volatile uint16_t smoothedRange = 0;
volatile uint16_t smoothedPosition = 0;

// Distance limits to convert to mouse position
const uint16_t maxDistance = 540;
const uint16_t minDistance = 50;
const uint8_t xaxis = 41;  // Position out of 100 to place the x-axis

#define LONG_RANGE
//#define HIGH_SPEED

// handle toot change
// HW debounce, just take current value
void handleToot() {
  if (tootProcessing) {
    return;
  }
  tootProcessing = true;
  Serial.print("Toot: ");
  delay(10);
  if (digitalRead(tootPin)) {
    Serial.println("Release.");
    AbsMouse.release(MOUSE_LEFT);
  } else {
    Serial.println("Press.");
    AbsMouse.press(MOUSE_LEFT);
  }
  tootProcessing = false;
}

// handle active/invert change
// SW debounce, wait 50ms before reading value
void handleMouseMode() {
  // https://docs.arduino.cc/built-in-examples/digital/Debounce
  Serial.print("Mouse: ");
  delay(debounceDelay);

  // whatever the reading is at, it's been there for longer than the debounce
  // delay, so take it as the actual current state:
  if (digitalRead(activePin) and digitalRead(invertPin)) {
    Serial.println("Mouse off.");
    mouseModeFlag = false;
  } else if (digitalRead(activePin)) {
    Serial.println("Mouse on.");
    mouseModeFlag = true;
    invertedFlag = false;
  } else {
    Serial.println("Mouse inverted.");
    mouseModeFlag = true;
    invertedFlag = true;
  }
}

void setup() {
  // put your setup code here, to run once:
  // Set interrupts on toot, invert, and active pins
  // https://hackaday.com/2015/12/09/embed-with-elliot-debounce-your-noisy-buttons-part-i/
  // HW debounce on toot, SW debounce on active/invert
  pinMode(tootPin, INPUT_PULLUP);
  pinMode(activePin, INPUT_PULLUP);
  pinMode(invertPin, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(tootPin), handleToot, CHANGE);
  attachInterrupt(digitalPinToInterrupt(activePin), handleMouseMode, CHANGE);
  attachInterrupt(digitalPinToInterrupt(invertPin), handleMouseMode, CHANGE);

  // Set up absmouse
  // https://github.com/jonathanedgecombe/absmouse
  AbsMouse.init(100, maxDistance - minDistance);

  // Set up I2C
  // https://forum.arduino.cc/t/handling-of-i2c-bus-at-400khz-and-twbr-register-of-wire-h/334918/3
  Wire.begin();           // Start I2C comms on SCL and SDA
  Wire.setClock(400000);  // Set the SCL clock speed to 400kHz

  // might need this for trinket m0?
  /*
  Wire.begin();                                  // Start Wire (I2C)
  sercom3.disableWIRE();                         // Disable the I2C bus
  SERCOM3->I2CM.BAUD.bit.BAUD = SystemCoreClock / ( 2 * 400000) - 1 ;   // // Set the I2C SCL frequency to 400kHz
  sercom3.enableWIRE();                          // Restart the I2C bus
  */

  // Set up distance

  Serial.begin(115200);

  // wait until serial port opens for native USB devices
  while (!Serial) {
    delay(1);
  }

  Serial.println("Trombone Champ Controller v3.");
  if (!lox.begin()) {
    Serial.println(F("Failed to boot Trombone Champ Controller v3"));
    while (1)
      ;
  }

  // start continuous ranging
  lox.startRangeContinuous();
}

void loop() {
  // continuously measure range and move mouse
  if (lox.isRangeComplete() and mouseModeFlag) {
    //delay(1000);
    uint16_t currentRange = lox.readRange();
    //Serial.print("Mouse distance: ");
    if ((currentRange > lastRange + 25)
        | (currentRange + 25 < lastRange)) {
      /*
          Serial.print("Distance in mm: ");
          Serial.print(lastRange);
          Serial.print(" : ");
          Serial.println(currentRange);
          */
      lastRange = currentRange;
    }
    smoothedRange = (currentRange + lastRange) / 2;
    //smoothedRange = currentRange;
    if (invertedFlag) {
      smoothedPosition = (maxDistance - smoothedRange - minDistance);
      AbsMouse.move(xaxis, smoothedPosition);
      lastRange = currentRange;
      //Serial.println(maxDistance - currentRange - minDistance);
    } else {
      smoothedPosition = (smoothedRange - minDistance);
      AbsMouse.move(xaxis, smoothedPosition);
      lastRange = currentRange;
      //Serial.println(currentRange - minDistance);
    }
  }
}