// Add this global variable at the very top of your sketch
bool wasLastBitHot = false;

void setup() {
  pinMode(PIN_A0, OUTPUT);
}

// Helper function to transmit a binary '1' for exactly 800ms
void transmitOne() {
  
  if (!wasLastBitHot) {
    // STATE: COLD START. We need the Spike!
    digitalWrite(PIN_A0, HIGH);
    delay(750); // 150ms of 100% power to punch up to ~55C

    // Phase 2: EQUILIBRIUM HOLD (e.g., 30% Duty Cycle for the remaining 650ms)
    for (int i = 0; i < 5; i++) {
      digitalWrite(PIN_A0, HIGH);
      delayMicroseconds(6000);  // 3ms ON
      digitalWrite(PIN_A0, LOW);
      delayMicroseconds(4000);  // 7ms OFF
    }
  } else {
    // STATE: ALREADY HOT. Skip the spike, just maintain Equilibrium!
    // 800ms total time / 10ms = 80 cycles
    for (int i = 0; i < 80; i++) {
      digitalWrite(PIN_A0, HIGH);
      delayMicroseconds(7000);  // 3ms ON
      digitalWrite(PIN_A0, LOW);
      delayMicroseconds(3000);  // 7ms OFF
    }
  }
  
  // Update the state for the next bit
  wasLastBitHot = true; 
}

// Helper function to transmit a binary '0' for exactly 800ms
void transmitZero() {
  digitalWrite(PIN_A0, LOW);
  delay(800); 
  
  // Update the state: The wire is now cold!
  wasLastBitHot = false;
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