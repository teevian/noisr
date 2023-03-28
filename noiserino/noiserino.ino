int analogValue = 0;
bool reading = false;


// IAD PROTOCOL                 https://theasciicode.com.ar
uint32_t IAD_START = 0x01;    //  SOH: start header control character
uint32_t IAD_PAUSE = 0x03;    //  ETX: indicates that it is the end of the message (interrupt)
uint32_t IAD_STOP = 0x04;     //  EOT: indicates the end of transmission
uint32_t IAD_ENQUIRE = 0x05;  //  ENQ: requests a response from arduino to confirm it is ready (Equiry)
uint32_t IAD_OK = 0x06;       //  ACK: acknowledgsement
uint32_t IAD_SYNC = 0x16;     //  DLE: synchronous Idle (used for transmission)
uint32_t IAD_ERROR = 0x21;    //  NAK: exclaim(error) special character

const int TIMEOUT_MILLISECONDS = 5000;

// defining state machines
enum State {
  IDLE,
  WAITING,
  WRITTING,
  ERROR
};

void setup() {
  Serial.begin(9600);  // Initialize serial communication
}

void loop() {

  if (Serial.available()) {
    uint8_t command = Serial.read();

    // start sending analog values
    if (command == IAD_START) {

      // Acknowledge command from Python
      Serial.write(IAD_OK);

      // Wait for analog pin number from Python - - WRITE A TIMEOUT HERE TODO
      while (Serial.available() == 0);

      const uint8_t pin = Serial.read();
      if(pin == IAD_STOP)
        return;
      //Serial.flush();

      reading = true;
      // Send analog values to Python program
      while (reading) {
        analogValue = analogRead(pin);
        double voltage = analogValue * (5. / 1023.);
        Serial.println(voltage, 8);

        // Check for stop command from Python
        if (Serial.available() && Serial.read() == IAD_STOP)
          reading = false;

        delay(100);  // Delay for 100ms
      }
    } else if (command = IAD_ENQUIRE) {
      handshake();
    } else {
      // sends an error message
      Serial.write(IAD_ERROR);
    }

    Serial.flush();
  }
}

void handshake() {
  Serial.write(IAD_OK);

  // wait for python to give a pin number
  unsigned long start_time = millis();
  while (Serial.available() == 0)
    if (millis() - start_time > TIMEOUT_MILLISECONDS)
      Serial.write(IAD_ERROR);
      return;

  // no timeout occured (pin was introduced)
  uint32_t pin = Serial.read();

  // Generate random number and send to Python
  randomSeed(analogRead(pin));
  int randomValue = random(10);
  Serial.write(randomValue);
}
