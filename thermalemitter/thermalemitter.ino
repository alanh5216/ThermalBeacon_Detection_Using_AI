void setup() {
  pinMode(PIN_A0, OUTPUT);
  // Notice: No Serial.begin() needed unless you want to print outside the fast loops!
}

// Helper function to transmit a binary '1' for exactly 500ms
void transmitOne() {
  
  // Phase 1: THE SPIKE (100% ON for 100ms)
  digitalWrite(PIN_A0, HIGH);
  delay(100); 

  // Phase 2: THE HOLD (90% Duty Cycle for the remaining 400ms)
  // 400ms total time / 10ms period = exactly 40 cycles
  for (int i = 0; i < 40; i++) {
    digitalWrite(PIN_A0, HIGH);
    delayMicroseconds(9000);  // 9ms ON
    
    digitalWrite(PIN_A0, LOW);
    delayMicroseconds(1000);  // 1ms OFF
  }
}

// Helper function to transmit a binary '0' for exactly 500ms
void transmitZero() {
  digitalWrite(PIN_A0, LOW);
  delay(500); // Completely OFF for 500ms to let it cool
}

void loop() {
  // Transmit a 1, then transmit a 0, repeating forever.
  // This gives a ~1Hz square wave
  transmitOne();
  transmitZero();
}