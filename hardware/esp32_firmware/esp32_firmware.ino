/*
 * esp32_firmware.ino — ESP32 Hardware Theft Deterrent System
 * 
 * Connected Components:
 *   1. Active/Passive Buzzer -> GPIO 18 (and GND)
 *   2. Red LED              -> GPIO 19 (through 220 Ohm resistor, and GND)
 *   3. Green LED (Optional) -> GPIO 21 (through 220 Ohm resistor, and GND)
 * 
 * Communication:
 *   Standard USB Serial at 115200 baud.
 *   Commands from Python AI Engine:
 *     - "ALARM_ON"  : Triggers loud siren sound on Buzzer and flashes RED LED.
 *     - "ALARM_OFF" : Silences Buzzer and turns RED LED OFF.
 *     - "AUTH_OK"   : Turns GREEN LED ON (Owner Access Granted), ensures Buzzer is OFF.
 */

// Pin Definitions (Adjust if your pins are different)
const int BUZZER_PIN    = 18;  // Buzzer positive terminal
const int RED_LED_PIN   = 19;  // Red LED (Intruder Alert)
const int GREEN_LED_PIN = 21;  // Green LED (Owner Verified)
const int ONBOARD_LED   = 2;   // ESP32 onboard blue LED for heartbeat

bool alarmActive = false;
unsigned long lastSirenToggle = 0;
bool sirenToneHigh = false;

void setup() {
  Serial.begin(115200);

  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(ONBOARD_LED, OUTPUT);

  // Initial Standby State
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(RED_LED_PIN, LOW);
  digitalWrite(GREEN_LED_PIN, LOW);
  digitalWrite(ONBOARD_LED, LOW);

  // Startup Test Beep (Confirms hardware is working)
  digitalWrite(GREEN_LED_PIN, HIGH);
  digitalWrite(BUZZER_PIN, HIGH);
  delay(150);
  digitalWrite(BUZZER_PIN, LOW);
  delay(100);
  digitalWrite(GREEN_LED_PIN, LOW);

  Serial.println("ESP32_VEHICLE_SECURITY_READY");
}

void loop() {
  // 1. Process Serial Commands from Python AI Engine
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "ALARM_ON") {
      alarmActive = true;
      digitalWrite(GREEN_LED_PIN, LOW);
      Serial.println("ESP32: ALARM_ACTIVATED");
    } 
    else if (cmd == "ALARM_OFF") {
      alarmActive = false;
      digitalWrite(BUZZER_PIN, LOW);
      digitalWrite(RED_LED_PIN, LOW);
      digitalWrite(ONBOARD_LED, LOW);
      Serial.println("ESP32: ALARM_SILENCED");
    } 
    else if (cmd == "AUTH_OK") {
      alarmActive = false;
      digitalWrite(BUZZER_PIN, LOW);
      digitalWrite(RED_LED_PIN, LOW);
      // Flash Green LED twice to confirm Owner Access
      digitalWrite(GREEN_LED_PIN, HIGH);
      digitalWrite(ONBOARD_LED, HIGH);
      delay(200);
      digitalWrite(GREEN_LED_PIN, LOW);
      digitalWrite(ONBOARD_LED, LOW);
      delay(150);
      digitalWrite(GREEN_LED_PIN, HIGH);
      delay(300);
      digitalWrite(GREEN_LED_PIN, LOW);
      Serial.println("ESP32: OWNER_ACCESS_GRANTED");
    }
  }

  // 2. Active Alarm Siren & Flashing Red LED Routine
  if (alarmActive) {
    unsigned long now = millis();
    if (now - lastSirenToggle >= 120) {  // Toggle tone every 120ms
      lastSirenToggle = now;
      sirenToneHigh = !sirenToneHigh;

      if (sirenToneHigh) {
        digitalWrite(BUZZER_PIN, HIGH);
        digitalWrite(RED_LED_PIN, HIGH);
        digitalWrite(ONBOARD_LED, HIGH);
      } else {
        digitalWrite(BUZZER_PIN, LOW);
        digitalWrite(RED_LED_PIN, LOW);
        digitalWrite(ONBOARD_LED, LOW);
      }
    }
  }
}
