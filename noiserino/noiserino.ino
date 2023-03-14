int analogValue = 0;
bool reading = false;


// IAD PROTOCOL                 https://theasciicode.com.ar
uint32_t IAD_START  = 0x01; //  SOH: start header control character 
uint32_t IAD_PAUSE  = 0x03; //  ETX: indicates that it is the end of the message (interrupt)
uint32_t IAD_STOP   = 0x04; //  EOT: indicates the end of transmission
uint32_t IAD_ENQUIRE= 0x05; //  ENQ: requests a response from arduino to confirm it is ready (Equiry)
uint32_t IAD_OK     = 0x06; //  ACK: acknowledgsement
uint32_t IAD_SYNC   = 0x16; //  DLE: synchronous Idle (used for transmission)
uint32_t IAD_ERROR  = 0x21; //  NAK: exclaim(error) special character


// defining state machines
enum State {
  IDLE,
  WAITING,
  WRITTING,
  ERROR
};

void setup() {
  Serial.begin(9600); // Initialize serial communication
  randomSeed(analogRead(0));
}

void loop() {

  // Wait for command from Python
  while (Serial.available() == 0);
  int command = Serial.read();

  // If command is 's', start sending analog values
  if (command == IAD_START) {
  
    // Acknowledge command from Python
    Serial.write(IAD_OK);

    // Wait for analog pin number from Python - - WRITE A TIMEOUT HERE TODO
    while (Serial.available() == 0);
    uint32_t pin = Serial.read();
    Serial.flush();

    reading = true;
    // Send analog values to Python program
    while (reading) {
      analogValue = analogRead(pin);
      double voltage = analogValue * (5. / 1023.);
      Serial.println(voltage, 8);

      // Check for stop command from Python
      if (Serial.available() && Serial.read() == IAD_STOP) {
        reading = false;
      }

      delay(100); // Delay for 100ms
    }
  } else if(command = IAD_ENQUIRE) {
    // Generate random number and send to Python
    int randomValue = random(20);
    Serial.println(randomValue);

    Serial.flush();
  } else {
    // sends an error message
    Serial.print("ERROR");

    Serial.flush();
  }
}
