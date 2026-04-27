void setup() {
  pinMode(PIN_A0, OUTPUT);
  // Notice: No Serial.begin() needed unless you want to print outside the fast loops!
}

// Helper function to transmit a binary '1' for exactly 800ms
void transmitOne() {
  
  // Phase 1: THE SPIKE (100% ON for 100ms)
  digitalWrite(PIN_A0, HIGH);
  delay(100); 

  // Phase 2: THE HOLD (85% Duty Cycle for 700ms)
  // 700ms total time / 10ms period = exactly 70 cycles
  for (int i = 0; i < 69; i++) {
    digitalWrite(PIN_A0, LOW);
    delayMicroseconds(1500);  // 1.5ms OFF

    digitalWrite(PIN_A0, HIGH);
    delayMicroseconds(8500);  // 8.5ms ON
  }
}

// Helper function to transmit a binary '0' for exactly 800ms
void transmitZero() {
  digitalWrite(PIN_A0, LOW);
  delay(800); // Completely OFF for 800ms to let it cool
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