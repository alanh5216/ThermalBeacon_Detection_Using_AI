void setup() {
  pinMode(PIN_A0, OUTPUT);
  // Notice: No Serial.begin() needed unless you want to print outside the fast loops!
}

// Helper function to transmit a binary '1' for exactly 700ms
void transmitOne() {
  
  // Phase 1: THE SPIKE (100% ON for 100ms)
  digitalWrite(PIN_A0, HIGH);
  delay(100); 

  // Phase 2: THE HOLD (90% Duty Cycle for 590ms)
  // 590ms total time / 10ms period = exactly 59 cycles
  for (int i = 0; i < 58; i++) {
    digitalWrite(PIN_A0, LOW);
    delayMicroseconds(1000);  // 1ms OFF

    digitalWrite(PIN_A0, HIGH);
    delayMicroseconds(9000);  // 9ms ON
  }
  // Phase 3: THE PRE COOL (OFF for 10ms)
  // If the next bit is a 0 then this gives it more time to cool,
  // If the next bit is a 1 then this lets it cool down so the spike doesn't overheat it
  digitalWrite(PIN_A0, LOW);
  delayMicroseconds(10000);  // 10ms OFF
}

// Helper function to transmit a binary '0' for exactly 700ms
void transmitZero() {
  digitalWrite(PIN_A0, LOW);
  delay(700); // Completely OFF for 700ms to let it cool
}

void loop() {
  // Transmit 11101 00101
  transmitOne();
  transmitOne();
  transmitOne();
  transmitZero();
  transmitOne();

  transmitZero();
  transmitZero();
  transmitOne();
  transmitZero();
  transmitOne();
}